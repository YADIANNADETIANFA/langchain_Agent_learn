from mcp.server import FastMCP

app = FastMCP("db_search")

@app.tool()
def db_search(query: str) -> str:
    """retrieve knowledge from the knowledge base based on user query, then output answer"""
    answer = """
        问题_1：张凯是否近视？ 回答_1：张凯不近视，两眼视力均为1.5。
        问题_2：张凯能否接受长期出差？  回答_2：张凯可以接受长期出差，张凯喜欢在世界各地进行工作。
        问题_3：张凯对办公室恋情的看法如何？  回答_3：张凯认为，办公室恋情最好不要影响工作。
    """
    return answer


if __name__ == "__main__":
    app.run(transport="stdio")