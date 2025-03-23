from weather_server import mcp


def main():
    print("Hello from weather!")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
