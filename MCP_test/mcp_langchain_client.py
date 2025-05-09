from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import asyncio

load_dotenv(dotenv_path='./.env')

model = ChatOpenAI(model="gpt-4o")

async def main():
    # langchain，连接多个MCP服务器，并加载它们的工具
    async with MultiServerMCPClient(
            {
                # "command": "python", 会报错: "ModuleNotFoundError: No module named 'mcp'"
                # 原因: 使用的是系统默认Python解释器，而不是`uv venv`所创建的虚拟环境
                # 解决方案:
                #   1. 使用`uv run ...` (推荐)
                #   2. 手动指定uv虚拟环境的py解释器，即"../.venv/Scripts/python"
                # "math": {
                #     "command": "../.venv/Scripts/python",
                #     "args": ["math_server.py"],
                #     "transport": "stdio",
                # },
                "math": {
                    "command": "uv",
                    "args": ["run", "math_server.py"],
                    "transport": "stdio",
                },

                # 受到VPN，全局代理的干扰，无法访问127.0.0.1. 因此，改用stdio进行测试
                # "weather": {
                #     "url": "http://127.0.0.1:3795/sse",
                #     "transport": "sse",
                # }
                "weather": {
                    "command": "uv",
                    "args": ["run", "weather_server.py"],
                    "transport": "stdio",
                },
            }
    ) as client:
        agent = create_react_agent(model, client.get_tools())
        math_response = await agent.ainvoke({"messages": "what's (3 + 5) * 12 ?"})
        print(math_response)
        weather_response = await agent.ainvoke({"messages": "what is the weather in nyc ?"})
        print(weather_response)


if __name__ == '__main__':
    asyncio.run(main())