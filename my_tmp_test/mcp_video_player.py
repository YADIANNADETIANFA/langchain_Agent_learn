import os


from mcp.server import FastMCP

app = FastMCP("video_player")

@app.tool()
def video_player(video_path: str):
    """play the video for video_path"""
    os.startfile(video_path)


if __name__ == '__main__':
    app.run(transport="stdio")
