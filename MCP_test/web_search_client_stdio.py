import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters


# 为stdio连接创建服务器参数
server_params = StdioServerParameters(
    # 服务器执行的命令，这里我们使用uv来运行
    command='uv',
    # 运行的参数
    args=['run', 'web_search_server_stdio.py'],
    # 环境变量，默认为None，表示使用当前环境变量
    # env=None
)


async def main():
    # 创建stdio客户端
    async with stdio_client(server_params) as (stdio, write):
        # 创建ClientSession对象
        async with ClientSession(stdio, write) as session:
            # 初始化ClientSession
            await session.initialize()
            # 列出可用的工具
            response = await session.list_tools()
            print(response)
            # 调用工具
            response = await session.call_tool('web_search', {'query': '今天杭州的天气'})
            print(response)


if __name__ == '__main__':
    asyncio.run(main())