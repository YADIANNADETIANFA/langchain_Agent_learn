from typing import TypedDict, List
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv(dotenv_path='../.env')

model = ChatOpenAI(model="gpt-4o", temperature=0)


# plan_agent
# 根据已有的工具，对task任务进行分解，分解成多个子任务
class AgentState(TypedDict):
    task: str                   # 用户输入的任务
    plan: List[str]             # 分解出的各项执行计划
    finished_step: List[str]    # 已完成的计划步骤
    next_step: str              # 当前计划步骤
    data: List[int]             # 采集到的各项数据
    report: str                 # 输出的报告
    step_num: int               # 当前步数
    max_step: int               # 最大允许步数

def plan_agent(state: AgentState) -> AgentState:
    PLAN_PROMPT = """
        你是一个专业的任务计划编排者，负责将用户输入的【task】，分解为各个独立且有序的【plan】，使得通过依次执行各个【plan】，可以完成整个【task】目标。\
        每一项的【plan】，仅可以如下内容之一：\
        _______________________________________ \
            "get data" \
            "generate report" \
        _______________________________________ \
        注意！直接按顺序输出每一项【plan】，使用','进行分隔。不要输出任何其他说明内容。
    """
    messages = [
        SystemMessage(content=PLAN_PROMPT),
        HumanMessage(content=state["task"])
    ]
    response = model.invoke(messages)
    return {
        **state,
        "plan": response.content.split(','),
    }

def process_agent(state: AgentState) -> AgentState:
    PROCESS_AGENT = f"""
        你是一个计划执行者，根据所有计划列表【plan】，与已完成计划列表【finished_step】，输出下一步所要执行的计划。\
        所有计划列表：{state["plan"]} \
        已完成计划列表：{state["finished_step"]} \
        如果你认为，所有的计划都已经被执行完成，则直接输出"task finished"。\
        注意！直接输出下一步的计划内容，不要输出任何其他内容。
    """
    messages = [
        SystemMessage(content=PROCESS_AGENT),
    ]
    response = model.invoke(messages)

    next_step = state["next_step"]
    if "get data" in response.content:
        next_step = "get data"
    elif "generate report" in response.content:
        next_step = "generate report"
    else:
        next_step = "task finished"

    return {
        **state,
        "next_step": next_step,
    }

def data_agent(state: AgentState) -> AgentState:
    return {
        **state,
        "finished_step": state["finished_step"] + ["get data"],
        "data": [1, 2, 3, 4, 5],
        "step_num": state["step_num"] + 1,
    }

def report_agent(state: AgentState) -> AgentState:
    REPORT_AGENT = f"""
        根据{state["data"]}中的数据，输出它们的加和结果。 \
        注意！直接输出加和结果，不要输出任何其他内容。
    """
    messages = [
        SystemMessage(content=REPORT_AGENT),
    ]
    response = model.invoke(messages)
    report_content = f"data中的结果加和为：{response.content}"
    print("*"*80)
    print(report_content)
    print("*" * 80)

    return {
        **state,
        "finished_step": state["finished_step"] + ["generate report"],
        "report": report_content,
        "step_num": state["step_num"] + 1,
    }

def route_to_agent(state: AgentState) -> str:
    if state["step_num"] >= state["max_step"]:
        return END
    if state["next_step"] == "get data":
        return "data_agent"
    elif state["next_step"] == "generate report":
        return "report_agent"
    else:
        return END

graph = StateGraph(AgentState)
graph.add_node("plan_agent", plan_agent)
graph.add_node("process_agent", process_agent)
graph.add_node("data_agent", data_agent)
graph.add_node("report_agent", report_agent)

graph.set_entry_point("plan_agent")

graph.add_edge("plan_agent", "process_agent")
graph.add_edge("data_agent", "process_agent")
graph.add_edge("report_agent", "process_agent")

graph.add_conditional_edges(
    "process_agent",
    route_to_agent,
    {END: END, "data_agent": "data_agent", "report_agent": "report_agent"},
)

app = graph.compile()

graph_png = app.get_graph().draw_mermaid_png()
with open("../dataset/multi_agent_tmp.png", "wb") as f:
    f.write(graph_png)

for s in app.stream({
    "task": "根据表中的数据，为我生成一篇报告。",
    "finished_step": [],
    "next_step": "",
    "data": [],
    "report": "",
    "step_num": 0,
    "max_step": 5,
}):
    print(s)
