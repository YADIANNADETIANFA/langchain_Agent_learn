from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults


load_dotenv(dotenv_path='../.env')

tool = TavilySearchResults(max_results=2)

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

from langgraph.checkpoint.sqlite import SqliteSaver

class Agent:
    def __init__(self, model, tools, checkpointer, system=""):
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_openai)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges("llm", self.exists_action, {True: "action", False: END})
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")

        # graph编译时，添加checkpoint，用于持久化存储
        self.graph = graph.compile(checkpointer=checkpointer)

        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)


    def exists_action(self, state: AgentState):
        result = state['messages'][-1]
        return len(result.tool_calls) > 0

    def call_openai(self, state: AgentState):
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        return {'messages': [message]}

    def take_action(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            print(f"Calling: {t}")
            result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print("Back to the model!")
        return {'messages': results}

prompt = """You are a smart research assistant. Use the search engine to look up information. \
You are allowed to make multiple calls (either together or in sequence). \
Only look up information when you are sure of what you want. \
If you need to look up some information before asking a follow up question, you are allowed to do that!
"""

model = ChatOpenAI(model="gpt-4o")

# 这里使用sqlite，在内存进行Agent持久化处理
# with SqliteSaver.from_conn_string(":memory:") as memory:
#     abot = Agent(model, [tool], system=prompt, checkpointer=memory)
#
#     # 不同td，持久化存储位置不同，这里进行控制
#     thread_1 = {"configurable": {"thread_id": "1"}}
#     thread_2 = {"configurable": {"thread_id": "2"}}
#
#     # 第一个问题，td_1
#     messages = [HumanMessage(content="What is the weather in sf?")]
#     for event in abot.graph.stream({"messages": messages}, thread_1):
#         for v in event.values():
#             print(v['messages'])
#
#     # 第二个问题，td_1
#     messages = [HumanMessage(content="What about in la?")]
#     for event in abot.graph.stream({"messages": messages}, thread_1):
#         for v in event.values():
#             print(v)
#
#     # 第三个问题，td_1
#     messages = [HumanMessage(content="Which one is warmer?")]
#     for event in abot.graph.stream({"messages": messages}, thread_1):
#         for v in event.values():
#             print(v)
#
#     # 第三个问题，td_2
#     print('*' * 80)
#     messages = [HumanMessage(content="Which one is warmer?")]
#     for event in abot.graph.stream({"messages": messages}, thread_2):
#         for v in event.values():
#             print(v)
#     print('*' * 80)


# from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
# import asyncio
#
# # 异步流式处理
# memory = AsyncSqliteSaver.from_conn_string(":memory:")
# abot = Agent(model, [tool], system=prompt, checkpointer=memory)
#
# messages = [HumanMessage(content="What is the weather in sf?")]
# thread_3 = {"configurable": {"thread_id": "3"}}
#
# async def main():
#     async for event in abot.graph.astream_events({"messages": messages}, thread_3, version="v1"):
#         kind = event["event"]
#         if kind == "on_chat_model_stream":
#             content = event["data"]["chunk"].content
#             if content:
#                 """
#                 Empty content in the context of OpenAI means that the model is asking for a tool to be invoked.
#                 So we only print non-empty content
#                 """
#                 print(content, end="|")
#
# asyncio.run(main())


from contextlib import AsyncExitStack
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import asyncio

# 异步流式处理
# async def main():
#     stack = AsyncExitStack()
#     memory = await stack.enter_async_context(AsyncSqliteSaver.from_conn_string(":memory:"))
#     # memory = AsyncSqliteSaver.from_conn_string(":memory:")
#
#     abot = Agent(model, [tool], system=prompt, checkpointer=memory)
#
#     messages = [HumanMessage(content="What is the weather in SF?")]
#     thread = {"configurable": {"thread_id": "4"}}
#     async for event in abot.graph.astream_events({"messages": messages}, thread, version="v1"):
#             kind = event["event"]
#             if kind == "on_chat_model_stream":
#                 content = event["data"]["chunk"].content
#                 if content:
#                     # Empty content in the context of OpenAI means
#                     # that the model is asking for a tool to be invoked.
#                     # So we only print non-empty content
#                     print(content, end="|")
#
#     await stack.aclose()
#
# asyncio.run(main())

# 异步流式处理
async def main():
    async with AsyncSqliteSaver.from_conn_string(":memory:") as memory:
        abot = Agent(model, [tool], system=prompt, checkpointer=memory)

        messages = [HumanMessage(content="What is the weather in SF?")]
        thread = {"configurable": {"thread_id": "4"}}
        async for event in abot.graph.astream_events({"messages": messages}, thread, version="v1"):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        # Empty content in the context of OpenAI means
                        # that the model is asking for a tool to be invoked.
                        # So we only print non-empty content
                        print(content, end="|")

asyncio.run(main())