# Run mcp server from client

1. cd into mcp_weather_client, create, activate the virtual env then install depenedencies.
2. Create a virtual env

```uv
uv venv
source .venv/bin/activate
uv sync
```

4. Run client

```uv
uv run main.py ../weather_server/main.py
```

or

```python
python main.py ../weather_server/main.py
```
