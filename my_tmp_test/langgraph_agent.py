from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import asyncio


load_dotenv(dotenv_path='../.env')

model = ChatOpenAI(model="gpt-4o")


async def main():
    async with MultiServerMCPClient(
        {
            "math": {
                "command": "uv",
                "args": ["run", "my_tmp_test.py"],
                "transport": "stdio",
            },
        }
    ) as client:
        tools = client.get_tools()

        def call_model(state: MessagesState):
            response = model.bind_tools(tools).invoke(state["messages"])
            return {"messages": response}

        builder = StateGraph(MessagesState)
        builder.add_node(call_model)
        builder.add_node(ToolNode(tools))
        builder.add_edge(START, "call_model")
        builder.add_conditional_edges(
            "call_model",
            tools_condition
        )
        builder.add_edge("tools", "call_model")
        graph = builder.compile()

        video_path = r"C:\Users\Icarus\Desktop\tmp_path.mp4"
        play_response = await graph.ainvoke({"messages": f"Use your video player tool to play the video for me, video_path param is: {video_path}"})
        print(play_response)


if __name__ == '__main__':
    asyncio.run(main())