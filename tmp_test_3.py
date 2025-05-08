import base64
from pathlib import Path
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv


load_dotenv(dotenv_path="./.env")

llm = ChatOpenAI(model="gpt-4o")


# 多模态输入，图片，base64编码传入
def png_to_base64(pic_path: Path):
    with open(pic_path, "rb") as img_file:
        encoded_bytes = base64.b64encode(img_file.read())
        encoded_str = encoded_bytes.decode("utf-8")
        return encoded_str


# **************************************************************************


# image_date = png_to_base64(Path("./dataset/tmp_test_3_pic.png"))
# message = HumanMessage(
#     content=[
#         {"type": "text", "text": "用中文描述这张图片的主要内容"},
#         {"type": "image_url", "image_url": {
#             "url": f"data:image/png;base64, {image_date}"
#         }}
#     ]
# )
# response = llm.invoke([message])
# print(response.content)
# 这张图片中有两个卡通角色。左边的人物坐在地板上，微笑看着右边的蓝色机器人。右边的机器人看起来不太高兴，表情严肃。背景中有一个窗户和桌子，上面有一些物品。图片下方有文字显示：“真是太过分了”。


# **************************************************************************


# 简单的工具调用
# from typing import Literal      # 用于代码的静态检查，要求参数值必须在给出范围内
# from langchain_core.tools import tool
#
# """
# 注意！下面的 "Describe the mood" ，是用来描述工具的功能的，LLM或agent会将其作为上下文。不可乱写，不可省略！
# """
# @tool
# def mood_tool(mood: Literal["高兴", "愤怒", "悲伤", "生气", "不满"]) -> None:
#     """Describe the mood"""
#     pass
#
#
# model_with_tools = llm.bind_tools([mood_tool])
#
# image_date = png_to_base64(Path("./dataset/tmp_test_3_pic.png"))
# message = HumanMessage(
#     content=[
#         {"type": "text", "text": "用中文描述，这张图片右侧蓝色人物的情绪"},
#         {"type": "image_url", "image_url": {
#             "url": f"data:image/png;base64, {image_date}"
#         }}
#     ]
# )
# print(llm.invoke([message]).content)
# response = model_with_tools.invoke([message])
# print(response.tool_calls)


# **************************************************************************


"""
指定JSON格式输出
`JSONOutputParser`是一个内置选项，用于提示并解析JSON输出。虽然它在功能上类似于`PydanticOutputParser`，
    但是它还支持流式返回部分JSON对象
    
下面将其与Pydantic一起使用，以方便地声明预期模式
"""
# from langchain_core.output_parsers import JsonOutputParser
# from langchain_core.prompts import PromptTemplate
# from langchain_core.pydantic_v1 import BaseModel, Field
#
#
# # 定义期望的输出结构
# class Joke(BaseModel):
#     setup: str = Field(description="设置笑话的问题")
#     punchline: str = Field(description="解决笑话的答案")
#
# joke_query = "告诉我一个笑话"
# parser = JsonOutputParser(pydantic_object=Joke)
# prompt = PromptTemplate(
#     template="回答用户的查询。\n{format_instructions}\n{query}\n",
#     input_variables=["query"],
#     partial_variables={"format_instructions": parser.get_format_instructions()},
# )
# chain = prompt | llm | parser

# 非流式输出
# response = chain.invoke({"query": joke_query})
# print(response)

# 流式输出
# for s in chain.stream({"query": joke_query}):
#     print(s)

"""
同理，使用`XMLOutputParser`可以实现XML格式输出；使用`YamlOutputParser`可以实现YAML格式输出。
"""

# **************************************************************************