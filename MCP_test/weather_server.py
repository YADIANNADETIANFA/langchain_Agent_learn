from mcp.server import FastMCP

# app = FastMCP("Weather", port=9001)
app = FastMCP("Weather")

@app.tool()
async def get_weather(location: str) -> str:
    """Get weather for location."""
    return "It's always sunny in New York."

if __name__ == '__main__':
    # app.run(transport="sse")
    app.run(transport="stdio")