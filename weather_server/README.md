# Create a venv & Install dependencies

Inside of weather_server folder.

```python
uv venv venv --python 3.13.2
source venv/bin/activate
uv pip install -r requirements.txt
```

# Run the mcp weather server localy

Run with the mcp-inspector:

```python
mcp dev main.py
```
