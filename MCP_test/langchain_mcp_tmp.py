from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import asyncio


load_dotenv(dotenv_path='../.env')

model = ChatOpenAI(model="gpt-4o")

server_params = StdioServerParameters(
    command='uv',
    args=['run', 'web_search_server_stdio.py'],
)


async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 获取工具列表
            tools = await load_mcp_tools(session)

            # 创建并使用ReAct agent
            agent = create_react_agent(model, tools)
            agent_response = await agent.ainvoke({"messages": "杭州今天天气怎么样？"})
            print(agent_response)


if __name__ == '__main__':
    asyncio.run(main())