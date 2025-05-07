from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv, find_dotenv

# 自动查找 .env 文件并加载
load_dotenv(find_dotenv())

llm = ChatOpenAI(model="gpt-4")

# **************************************************************************

# from langchain_community.tools.tavily_search import TavilySearchResults
#
# search = TavilySearchResults(max_results=2)
# print(search.invoke("今天上海天气怎么样"))

# **************************************************************************

# from langchain_core.tools import create_retriever_tool
# from langchain_community.document_loaders import WebBaseLoader
# from langchain_community.vectorstores import FAISS
# from langchain_openai import OpenAIEmbeddings
# from langchain_text_splitters import RecursiveCharacterTextSplitter
#
# loader = WebBaseLoader("https://zh.wikipedia.org/wiki/%E7%8C%AB")
# docs = loader.load()
#
# documents = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs)
# # 需手动安装依赖，`uv add -U faiss-cpu`
# vector = FAISS.from_documents(documents, OpenAIEmbeddings())
# retriever = vector.as_retriever()
#
# print(retriever.invoke("猫的特征")[0])
#
# retriever_tool = create_retriever_tool(
#     retriever,
#     "wiki_search",
#     "搜索维基百科"
# )

# **************************************************************************

# 使用LangChain创建Agent，并进行工具调用

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools.retriever import create_retriever_tool
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain import hub
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor
from langchain.globals import set_verbose
from langchain.globals import set_debug

# 控制台详细过程打印、详细日志记录打印
set_verbose(True)
set_debug(True)

loader = WebBaseLoader("https://zh.wikipedia.org/wiki/%E7%8C%AB")
docs = loader.load()
documents = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs)
vector = FAISS.from_documents(documents, OpenAIEmbeddings())
retriever = vector.as_retriever()
retriever_tool = create_retriever_tool(
    retriever,
    "wiki_search",
    "搜索维基百科"
)

search = TavilySearchResults(max_results=1)

tools = [search, retriever_tool]

# 获取要使用的提示 (LangChain Hub)
prompt = hub.pull("hwchase17/openai-functions-agent")
print(prompt.messages)

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

# 调用过程，LangSmith非常详细
print(agent_executor.invoke({"input": "从维基百科搜索有关猫的特征，并从网上告诉我今天都有哪些新闻"}))

# **************************************************************************

# 历史会话

# 会话隔离







