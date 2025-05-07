from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv, find_dotenv

# 自动查找 .env 文件并加载
load_dotenv(find_dotenv())

llm = ChatOpenAI(model="gpt-3.5-turbo")

# prompt = ChatPromptTemplate.from_messages([
#     ("system", "你是世界级的技术专家"),
#     ("human", "{input}")
# ])

# chain = prompt | llm
#
# result = chain.invoke({"input": "帮我写一篇关于AI的技术文章，100个字"})
# print(result)

# **************************************************************************

from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

# 字符串输出解析器
# output_parser = StrOutputParser()
#
# chain = prompt | llm | output_parser
#
# result = chain.invoke({"input": "帮我写一篇关于AI的技术文章，100个字"})
# print(result)

# **************************************************************************

# from langchain_core.prompts import PromptTemplate
#
# # 基本的字符串提示词模板
# prompt_template = PromptTemplate.from_template(
#     "给我讲一个关于{content}的{adjective}笑话"
# )
# result = prompt_template.format(adjective="冷", content="猴子")
# print(result)

# **************************************************************************

# langchain prompt few shot
# https://www.bilibili.com/video/BV1BgfBYoEpQ?spm_id_from=333.788.player.switch&vd_source=9c2b9b14820d6f6ec6ccc022af406252&p=2
# 20 min

# **************************************************************************

# SSE协议，流式调用
# chunks = []
# for chunk in llm.stream("天空是什么颜色？"):
#     chunks.append(chunk)
#     print(chunk.content, end="|", flush=True)

# **************************************************************************

# 异步流式处理
# import asyncio
#
# prompt = ChatPromptTemplate.from_template("给我讲一个关于{topic}的笑话，字数为200字左右")
# parser = StrOutputParser()
# chain = prompt | llm | parser
#
# async def async_stream():
#     async for chunk in chain.astream({"topic": "鹦鹉"}):
#         print(chunk, end="|", flush=True)
#
# asyncio.run(async_stream())


# **************************************************************************


# 异步流式调用，要求以JSON格式输出，并进行JSON格式转换 (正常是markdown格式)
# import asyncio
# from langchain_openai import ChatOpenAI
#
# model = ChatOpenAI(model="gpt-3.5-turbo")
# chain = (
#     model | JsonOutputParser()
# )
#
# async def async_stream():
#     async for text in chain.astream(
#         "以 JSON 格式输出法国、西班牙和日本的国家及其人口列表。"
#         "使用一个带有“countries”外部键的字典，其中包含国家列表。"
#         "每个国家都应该有键`name`和`population`"
#     ):
#         print(text, flush=True)
#
# asyncio.run(async_stream())


# **************************************************************************


# 对于langchain事件的异步流式输出 (该功能在langSmith ? 可辅助问题排查)
# from langchain_openai import ChatOpenAI
# import asyncio
#
# async def async_stream():
#     events = []
#     async for event in llm.astream_events("hello", version="v2"):
#         events.append(event)
#     print(events)
#
# asyncio.run(async_stream())