import json
from typing import List, Optional
from contextlib import AsyncExitStack
from openai import AsyncAzureOpenAI

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool

from settings import Settings


class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.settings = Settings()
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

        self.default_llm_config = list(
            filter(lambda client: client.host == "aoai", self.settings.LLM_CLIENTS)
        )[0]

        if self.default_llm_config is not None:
            self.llm = AsyncAzureOpenAI(
                api_version=self.default_llm_config.api_version,
                azure_endpoint=self.default_llm_config.endpoint,
                api_key=self.default_llm_config.api_key,
            )

    async def get_available_tools(self) -> List[Tool]:
        """
        Retrieve a list of available tools from the MCP server.
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        list_tools_result = await self.session.list_tools()
        print(f"\nlist_tools_result: {list_tools_result.tools}")

        return list_tools_result.tools

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        """Establishes connection to MCP server"""
        # self._client = stdio_client(self.server_params)
        # self.read, self.write = await self._client.__aenter__()
        # session = ClientSession(self.read, self.write)
        # self.session = await session.__aenter__()
        # await self.session.initialize()

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command, args=[server_script_path], env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        await self.session.initialize()

        # List available tools
        tools_list = await self.get_available_tools()

        print(
            "\nConnected to server with tools:",
            [tool.name for tool in tools_list if tool],
        )

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""

        user_message = {"role": "user", "content": query}
        print(f"\nuser_message: {user_message}")

        messages = [user_message]

        tools = await self.get_available_tools()

        # Antropic tool schema
        # available_tools = [
        #     {
        #         "name": tool.name,
        #         "description": tool.description,
        #         "input_schema": tool.inputSchema,
        #     }
        #     for tool in response.tools
        # ]

        # Azure OpenAI tool schema
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in tools
        ]
        print(f"\nAvailable tools: {available_tools}")

        # Initial Claude API call
        response = await self.llm.chat.completions.create(
            model=self.default_llm_config.model_deployment_id,  # "claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=messages,
            tools=available_tools,
        )

        print(f"\nInitial response: {response}")
        # Process response and handle tool calls

        final_text = []
        assistant_message_content = []

        for choice in response.choices:
            if query_text := choice.message.content:
                final_text.append(query_text)
                assistant_message_content.append(query_text)
            elif choice.message.tool_calls:
                for tool_call in choice.message.tool_calls:
                    if tool_call.type != "function":
                        continue

                    function = tool_call.function
                    tool_name = function.name
                    print("tool is assigned to assistant.content message: ", tool_call)
                    print(f"\nTool name: {tool_name}, Tool args: {function.arguments}")

                    if function.arguments:
                        tool_args = json.loads(function.arguments)
                    else:
                        tool_args = {}

                    # Execute tool call
                    result = await self.session.call_tool(tool_name, tool_args)
                    final_text.append(
                        f"[Calling tool {tool_name} with args {tool_args}]"
                    )

                    print("self.session.call_tool: ", result)

                    messages.append(
                        {
                            "role": "assistant",
                            "content": assistant_message_content,
                            "tool_calls": [
                                {
                                    "id": tool_call.id,
                                    "function": {
                                        "name": tool_name,
                                        "arguments": tool_call.function.arguments,
                                    },
                                    "type": "function",
                                }
                            ],
                        }
                    )

                    # messages.append(
                    #     {
                    #         "role": "user",
                    #         "content": [
                    #             {
                    #                 "type": "tool_result",
                    #                 "tool_use_id": tool_call.id,
                    #                 "content": result.content[0].text,
                    #             }
                    #         ],
                    #     }
                    # )

                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": tool_name,
                            "content": result.content[0].text,
                        }
                    )

                    print(f"messages: {messages}")

                    response = await self.llm.chat.completions.create(
                        model=self.default_llm_config.model_deployment_id,
                        max_tokens=1000,
                        messages=messages,
                        tools=available_tools,
                    )
                    print(f"\nfinal response: {response}")
                    final_text.append(response.choices[0].message.content)

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()
