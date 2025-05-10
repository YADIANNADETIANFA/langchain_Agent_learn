from mcp.server import FastMCP

app = FastMCP("Math")

@app.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@app.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b


if __name__ == '__main__':
    app.run(transport="stdio")
