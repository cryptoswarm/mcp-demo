import asyncio
import sys
import json
from typing import Optional
from contextlib import AsyncExitStack
from openai import AsyncAzureOpenAI

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# from dotenv import load_dotenv

# load_dotenv()  # load environment variables from .env
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

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

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

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""

        user_message = {"role": "user", "content": query}
        print(f"\nuser_message: {user_message}")

        messages = [user_message]

        response = await self.session.list_tools()
        print(f"\nAvailable tools: {response}")
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
            for tool in response.tools
        ]

        # Initial Claude API call
        response = await self.llm.chat.completions.create(
            model=self.default_llm_config.model_deployment_id,  # "claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=messages,
            tools=available_tools,
        )

        print(f"\nresponse: {response}")
        # Process response and handle tool calls

        final_text = []
        assistant_message_content = []

        for choice in response.choices:
            if query_text := choice.message.content:
                final_text.append(query_text)
                assistant_message_content.append(query_text)
            elif choice.message.tool_calls:
                for tool in choice.message.tool_calls:
                    if tool.type != "function":
                        continue

                    function = tool.function
                    tool_name = function.name
                    print(f"\nTool name: {tool_name}, Tool args: {function.arguments}")
                    try:
                        tool_args = json.loads(function.arguments)
                        print(f"Tool args: {tool_args}")
                    except Exception as e:
                        print(
                            f"Error decoding tool arguments: {function.arguments}, error {e}"
                        )
                        sys.exit(1)

                    # Execute tool call
                    result = await self.session.call_tool(tool_name, tool_args)
                    final_text.append(
                        f"[Calling tool {tool_name} with args {tool_args}]"
                    )

                    print("self.session.call_tool: ", result)

                    assistant_message_content.append(choice.message.content)
                    messages.append(
                        {"role": "assistant", "content": assistant_message_content}
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool.id,
                                    "content": result.content[0].text,
                                }
                            ],
                        }
                    )

                    print(f"messages: {messages}")

                    response = await self.llm.chat.completions.create(
                        model=self.default_llm_config.model_deployment_id,
                        max_tokens=1000,
                        messages=messages,
                        tools=available_tools,
                    )

                    # final_text.append(response.content[0].text)
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
