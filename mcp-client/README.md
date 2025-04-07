# Setting a virtual env

```uv
uv venv .venv python 3.13.2
```

Source the newly created virtaul env: `source .venv/bin/activate`

Install libraries: `uv add "mcp[cli]" openai python-dotenv pydantic-settings==2.8.1`
or

```
uv pip install -r requirements.txt
```

# Run client

```uv
uv run main.py ../mcp-server/weather_server.py
```
