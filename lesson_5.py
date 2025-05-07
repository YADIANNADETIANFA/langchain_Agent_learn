from dotenv import load_dotenv, find_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.checkpoint.sqlite import SqliteSaver
from uuid import uuid4


# 自动查找 .env 文件并加载
load_dotenv(find_dotenv())

"""
In previous examples we've annotated the `messages` state key
with the default `operator.add` or `+` reducer, which always
appends new messages to the end of the existing messages array.

Now, to support replacing existing messages, we annotate the
`messages` key with a customer reducer function, which replaces
messages with the same `id`, and appends them otherwise.
"""
def reduce_messages(left: list[AnyMessage], right: list[AnyMessage]) -> list[AnyMessage]:
    # assign ids to messages that don't have them
    for message in right:
        if not message.id:
            message.id = str(uuid4())

    # merge the new messages with the existing messages
    merged = left.copy()
    for message in right:
        for i, existing in enumerate(merged):
            # replace any existing messages with the same id
            if existing.id == message.id:
                merged[i] = message
                break
        # 注意！这里没有问题，是py合法且常用的模式：`for ... else`
        # `else`会在`for`循环没有被`break`的时候执行
        # 这里不是`if ... else`，而是`for ... else`!
        else:
            # append any new messages to the end
            merged.append(message)
    return merged

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], reduce_messages]

tool = TavilySearchResults(max_results=2)

class Agent:
    def __init__(self, model, tools, system="", checkpointer=None):
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_openai)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges("llm", self.exists_action, {True: "action", False: END})
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")

        # graph编译时，添加checkpoint，用于持久化存储
        # 规定，在"action"操作前，中断循环，添加人工干预 (Human in the Loop)
        self.graph = graph.compile(
            checkpointer=checkpointer,
            interrupt_before=["action"]
        )

        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)


    def exists_action(self, state: AgentState):
        # print(state)
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
            # print(f"Calling: {t}")
            result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print("Back to the model!")
        return {'messages': results}

prompt = """You are a smart research assistant. Use the search engine to look up information. \
You are allowed to make multiple calls (either together or in sequence). \
Only look up information when you are sure of what you want. \
If you need to look up some information before asking a follow up question, you are allowed to do that!
"""

# model = ChatOpenAI(model="gpt-4o")
model = ChatOpenAI(model="gpt-3.5-turbo")

# 这里使用sqlite，在内存进行Agent持久化处理
# with SqliteSaver.from_conn_string(":memory:") as memory:
#     abot = Agent(model, [tool], system=prompt, checkpointer=memory)
#
#     # 不同td，持久化存储位置不同，这里进行控制
#     thread_1 = {"configurable": {"thread_id": "1"}}
#
#     messages = [HumanMessage(content="What is the weather in SF?")]
#     for event in abot.graph.stream({"messages": messages}, thread_1):
#         for v in event.values():
#             print(v)
#
#     print("graph当前的状态:")
#     print(abot.graph.get_state(thread_1))
#
#     print("graph下一步将要调用的节点:")
#     # 结果为 ('action',)
#     print(abot.graph.get_state(thread_1).next)
#
#     print("graph go on:")
#     # graph从中断处继续 (continue after interrupt) (输入为None)
#     for event in abot.graph.stream(None, thread_1):
#         for v in event.values():
#             print(v)
#
#     print("graph再次查看当前的状态:")
#     # 结果为所有的状态信息
#     print(abot.graph.get_state(thread_1))
#
#     print("graph再次查看下一步将要调用的节点:")
#     # 结果为空，表示没有什么需要做的了
#     print(abot.graph.get_state(thread_1).next)
#
#     # 额外再起一个td，实现手动干预
#     thread_2 = {"configurable": {"thread_id": "2"}}
#     for event in abot.graph.stream({"messages": messages}, thread_2):
#         for v in event.values():
#             print(v)
#     while abot.graph.get_state(thread_2).next:
#         print(abot.graph.get_state(thread_2))
#         _input = input("proceed?")
#         if _input != "y":
#             print("aborting")
#             break
#         for event in abot.graph.stream(None, thread_2):
#             for v in event.values():
#                 print(v)



"""
这里调了很久才复现。

排查：
将断点打在
    `def call_openai()`中的`return {'messages': [message]}`
    `def take_action()`中的`tool_calls = state['messages'][-1].tool_calls`
使用"gpt-4o"时发现，当你手动将位置从"LA"调整到"Louisiana"后，llm会认为tool回答的不对，即当前上下文不满足对"LA"天气进行回答。
llm自己会再次调用工具，再次对"LA"进行天气询问。然后，当llm从tool回答拿到"LA"天气后，回答了HumanMessage("What is the weather in LA?")
即，"gpt-4o"更"智能"，这个"智能"让"gpt-4o"目标更加清晰，更加专注于，必须要拿到"LA"的天气才回答。
所以，使用"gpt-4o"始终无法复现，始终在回答"LA"的天气。

然后，尝试使用llm "gpt-3.5-turbo"，发现就没有上述问题。
"gpt-3.5-turbo"，拿到"Louisiana"的天气就回答了，不管HumanMessage具体问的是哪里了

(但是，回答结果非常不稳定。后续有机会再调吧...) 
https://www.bilibili.com/video/BV1bi421v7oD?spm_id_from=333.788.player.switch&vd_source=9c2b9b14820d6f6ec6ccc022af406252&p=6
"""
# 手动修改graph的state
with SqliteSaver.from_conn_string(":memory:") as memory:
    abot = Agent(model, [tool], system=prompt, checkpointer=memory)
    thread_3 = {"configurable": {"thread_id": "3"}}

    # messages = [HumanMessage(content="What is the weather in LA?")]
    messages = [HumanMessage(content="If you don't know the weather anywhere, please check and tell me the weather in LA. But if you know the weather in another place, please answer me immediately without checking the weather in LA.")]

    for event in abot.graph.stream({"messages": messages}, thread_3):
        for v in event.values():
            print(v)

    print("查看graph当前的state：")
    current_values = abot.graph.get_state(thread_3)

    # 修改graph的state，天气查询，从查询LA变为查询Louisiana
    _id = current_values.values["messages"][-1].tool_calls[0]['id']
    current_values.values['messages'][-1].tool_calls = [
        {
            "name": "tavily_search_results_json",

            "args": {"query": "current weather in Louisiana"},

            "id": _id
        }
    ]
    # 执行graph的state更新
    abot.graph.update_state(thread_3, current_values.values)

    print("查看graph state是否更新成功：")
    print(abot.graph.get_state(thread_3).values['messages'][-1].tool_calls)

    for event in abot.graph.stream(None, thread_3):
        for v in event.values():
            print(v)


    # =================================================================

    # 这里也是，没办法复现的
    states = []
    for state in abot.graph.get_state_history(thread_3):
        print(state)
        print('--')
        states.append(state)

    to_replay = states[-1]
    print("to_replay:")
    print(to_replay)

    for event in abot.graph.stream(None, to_replay.config):
        for k, v in event.items():
            print(v)