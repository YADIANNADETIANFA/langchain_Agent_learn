from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from typing import TypedDict, List
from langgraph.graph import StateGraph, END, START, MessagesState
from llm_prompt import LLM_TEMPLATE
from langchain_core.messages import SystemMessage
import asyncio
from pathlib import Path
from langgraph.prebuilt import ToolNode, tools_condition
from dotenv import load_dotenv
from pydantic import BaseModel, Field


load_dotenv(dotenv_path="../.env")

# todo，使用之前，确定vpn连接模型；
#  确定pycharm配置的http proxy
# model = ChatOpenAI(model="gpt-5")

# siliconflow，API_key，系统环境变量总是不刷新，因此直接放到这里
model = ChatOpenAI(
    model="Qwen/QwQ-32B",
    api_key="2333",
    base_url="https://api.siliconflow.cn/v1",
)


class AgentState(TypedDict):
    custom_input: str                           # 用户输入的原始要求
    article_format: str                         # 生成文章的格式
    article_style: str                          # 生成文章的风格
    word_count_req: int                         # 生成文章的字数要求
    attachment: str                             # 附件  todo，当前是单个附件
    attachment_knowledge: List[str]             # 从附件中，每一轮，所提取到的知识
    use_knowledge_base: bool                    # 是否使用本地知识库
    knowledge_base_query: List[List[str]]       # 梳理出的，每一轮，查询本地知识库，用于丰富文章内容的问题
    knowledge_base_res: List[List[str]]         # 本地知识库，每一轮，检索到的结果
    article_content: str                        # 文章内容
    optimization_suggestion: str                # 对当前文章的优化建议
    revision_number: int                        # 当前修订次数
    max_revision: int                           # 最大允许修订次数


async def attachment_knowledge_node(state: AgentState):
    async with MultiServerMCPClient(
            {
                "attachment_reading": {
                    "command": "uv",
                    "args": ["run", "attachment_reading.py"],
                    "transport": "stdio",
                }
            },
    ) as client:
        tools = client.get_tools()
        tool_node = ToolNode(tools)

        async def call_model(state_in: MessagesState):
            return {
                "messages": [
                    await model.bind_tools(tools).ainvoke(state_in["messages"])
                ]
            }

        # 嵌套子图
        builder = StateGraph(MessagesState)
        builder.add_node("call_model", call_model)
        builder.add_node("tools", tool_node)
        builder.add_edge(START, "call_model")
        builder.add_conditional_edges("call_model", tools_condition)
        builder.add_edge("tools", "call_model")
        graph = builder.compile()

        llm_prompt = LLM_TEMPLATE["attachment_knowledge"].format(
            attachment_local_path=state.get("attachment", "无"),
            attachment_knowledge=str(state.get("attachment_knowledge", "无")),
            optimization_suggestion=state.get("optimization_suggestion", "无")
        )
        out = await graph.ainvoke({"messages": [SystemMessage(content=llm_prompt)]})

    final_msg = out["messages"][-1]

    if state.get("attachment_knowledge"):
        attachment_knowledge = state.get("attachment_knowledge", [])
        attachment_knowledge.append(final_msg.content)
        return {"attachment_knowledge": attachment_knowledge}
    else:
        return {"attachment_knowledge": [final_msg.content, ]}


async def relate_query_generate_node(state: AgentState):
    if state.get("use_knowledge_base", False):
        llm_prompt = LLM_TEMPLATE["relate_query_generate"].format(
            article_generation_requirements=state.get("custom_input", "无"),
            knowledge_base_query=str(state.get("knowledge_base_query", "无")),
            optimization_suggestion=state.get("optimization_suggestion", "无")
        )

        class Query(BaseModel):
            """梳理出的问题"""
            query_ls: List[str] = Field(description="以List列表的形式，依次列出各个问题")

        messages = [SystemMessage(content=llm_prompt)]
        # 控制输出格式为List
        response = await model.with_structured_output(Query).ainvoke(messages)

        if state.get("knowledge_base_query"):
            knowledge_base_query = state.get("knowledge_base_query", [])
            knowledge_base_query.append(response.query_ls)
            return {"knowledge_base_query": knowledge_base_query}
        else:
            return {"knowledge_base_query": [response.query_ls,]}
    else:
        return {"knowledge_base_query": "无"}


async def knowledge_base_retrieval_node(state: AgentState):
    if state.get("use_knowledge_base", False):
        # todo ，RAG的接口对接，也是 List[List[str]]
        return {"knowledge_base_res": [["HS6 2025年的销量是15万量", "红旗集团2025年整体营业额突破100亿大关。", "红旗的新能车，现在世界第一。"]]}
    else:
        return {"knowledge_base_res": "无"}

async def article_generate_node(state: AgentState):
    llm_prompt = LLM_TEMPLATE["article_generate"].format(
        article_generation_requirements=state.get("custom_input", "无"),
        article_format=state.get("article_format", "无"),
        article_style=state.get("article_style", "无"),
        word_count_req=state.get("word_count_req", 500),
        article_content=state.get("article_content", "无"),
        optimization_suggestion=state.get("optimization_suggestion", "无"),
        attachment_knowledge=str(state.get("attachment_knowledge", "无")),
        knowledge_base_res=str(state.get("knowledge_base_res", "无")),
    )
    messages = [SystemMessage(content=llm_prompt)]
    response = await model.ainvoke(messages)
    return {"article_content": response.content, "revision_number": state.get("revision_number", 1) + 1}


async def reflection_and_optimization_node(state: AgentState):
    llm_prompt = LLM_TEMPLATE["reflection_optimization"].format(
        current_article=state.get("article_content", "无"),
        article_generation_requirements=state.get("custom_input", "无"),
        article_format=state.get("article_format", "无"),
        article_style=state.get("article_style", "无"),
        word_count_req=state.get("word_count_req", 500),
        attachment_knowledge=str(state.get("attachment_knowledge", "无")),
        knowledge_base_res=str(state.get("knowledge_base_res", "无")),
    )
    messages = [SystemMessage(content=llm_prompt)]
    response = await model.ainvoke(messages)
    return {"optimization_suggestion": response.content}


def should_continue(state: AgentState):
    return END if state["revision_number"] > state["max_revision"] else "reflection_and_optimization"


builder = StateGraph(AgentState)
builder.add_node("get_attachment_knowledge", attachment_knowledge_node)
builder.add_node("relate_query_generate", relate_query_generate_node)
builder.add_node("knowledge_base_retrieval", knowledge_base_retrieval_node)
builder.add_node("article_generate", article_generate_node)
builder.add_node("reflection_and_optimization", reflection_and_optimization_node)
builder.set_entry_point("get_attachment_knowledge")
builder.add_conditional_edges("article_generate", should_continue, {END: END, "reflection_and_optimization": "reflection_and_optimization"})
builder.add_edge("get_attachment_knowledge", "relate_query_generate")
builder.add_edge("relate_query_generate", "knowledge_base_retrieval")
builder.add_edge("knowledge_base_retrieval", "article_generate")
builder.add_edge("reflection_and_optimization", "get_attachment_knowledge")


async def main():
    graph = builder.compile()
    # graph_png = graph.get_graph().draw_mermaid_png()
    # Path("./article_generate.png").write_bytes(graph_png)
    thread = {"configurable": {"thread_id": "1"}}
    async for s in graph.astream({
        "custom_input": "红旗汽车销量成绩汇报",
        "article_format": "开会汇报材料",
        "article_style": "员工向领导在会上做出的汇报",
        "word_count_req": 300,
        "attachment": "./attachment/20230118  邱总在吉林省第一届职工冰雪运动会暨红旗冰雪嘉年华活动启动仪式上的致辞V6.docx",
        "use_knowledge_base": False,
        "revision_number": 1,
        "max_revision": 3,
    }, thread):
        print(s)

if __name__ == "__main__":
    asyncio.run(main())
