import asyncio
from mcp.client.sse import sse_client
from mcp import ClientSession
import asyncio


async def main():
    async with sse_client('http://localhost:9000/sse') as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()

            res = await session.call_tool('web_search', {'query': '杭州今天的天气'})
            print(res)


if __name__ == '__main__':
    asyncio.run(main())