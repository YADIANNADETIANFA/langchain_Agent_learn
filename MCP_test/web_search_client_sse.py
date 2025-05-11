from mcp.client.sse import sse_client
from mcp import ClientSession
import asyncio
from dotenv import load_dotenv


# client端，设置环境变量`NO_PROXY=127.0.0.1,localhost`
# 即告诉client端的HTTP请求库，对于"127.0.0.1 或 localhost"，不要使用代理，直接连接
# 它不会影响服务器的监听行为，而是影响发起请求的一方是否通过代理去访问地址
load_dotenv(dotenv_path='../.env')


async def main():
    async with sse_client('http://localhost:9000/sse') as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()

            res = await session.call_tool('web_search', {'query': '杭州今天的天气'})
            print(res)


if __name__ == '__main__':
    asyncio.run(main())