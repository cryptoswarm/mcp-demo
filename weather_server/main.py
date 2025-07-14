from mcp.server.fastmcp import FastMCP

from weather_server_tools import get_alerts, get_forecast

mcp = FastMCP("weather-server", log_level="ERROR")

mcp.add_tool(fn=get_alerts, name="weather_alerts_tool")
mcp.add_tool(fn=get_forecast, name="weather_forecasts_tool")

if __name__ == "__main__":
    print("Hello from mcp server!")
    mcp.run(transport="stdio")
