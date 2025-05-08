from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv


load_dotenv(dotenv_path="./.env")

llm = ChatOpenAI(model="gpt-3.5-turbo")


"""
LangChain提供了三种创建工具的方式：
1. 使用`@tool`装饰器 -- 定义自定义工具的最简单方式。
2. 使用`StructuredTool.from_function`类方法 -- 这类似于`@tool`装饰器，但允许更多配置和同步和异步实现的规范。
3. 通过子类化`BaseTool` -- 这是最灵活的方法，它提供了最大程度的控制，但需要更多的工作量和代码。

`@tool`或`StructuredTool.from_function`类方法，对于大多数用例应该足够了。
如果工具具有精心选择的名称、描述和JSON模式，模型的性能会更好。
"""
# **************************************************************************

# 导入工具装饰器库
# from langchain_core.tools import tool

# # @tool
# def multiply(a: int, b: int) -> int:
#     """Multiply two numbers."""
#     return a * b
#
# # 检查与工具相关的一些属性
# print(multiply.name)
# print(multiply.description)
# print(multiply.args)

# 也可以创建异步工具
# @tool
# async def amultiply(a: int, b: int) -> int:
#     """Multiply two numbers."""
#     return a * b
#
# print(amultiply.name)
# print(amultiply.description)
# print(amultiply.args)


# **************************************************************************

# from langchain_core.tools import tool
# from pydantic import BaseModel, Field
#
# class CalculatorInput(BaseModel):
#     a: int = Field(description="first number")
#     b: int = Field(description="second number")
#
#
# """
# name_or_callable: (类型: str) 自定义工具名称
# description: (类型: str) 描述工具的功能，LLM或Agent将使用此描述作为上下文
# args_schema: (类型: Pydantic BaseModel) 建议使用，可以提供更多信息(如few-shot)或验证预期参数
# return_direct: (类型: boolean) 仅对Agent相关。默认为False。当为True时，在调用工具后，代理将停止并将结果直接返回给用户。
# """
# @tool(name_or_callable="multiplication-tool", args_schema=CalculatorInput, return_direct=True)
# def multiply(a: int, b: int) -> int:
#     """Multiply two numbers."""
#     return a * b
#
# print(multiply.name)
# print(multiply.description)
# print(multiply.args)
# print(multiply.return_direct)


# **************************************************************************


# from langchain_core.tools import StructuredTool
# import asyncio
#
# def multiply(a: int, b: int) -> int:
#     """Multiply two numbers."""
#     return a * b
#
# async def amultiply(a: int, b: int) -> int:
#     """Multiply two numbers."""
#     return a * b
#
# async def main():
#     # func 参数：指定一个同步函数。当你在同步上下文中调用工具时，它会使用这个同步函数来执行操作
#     # coroutine 参数：指定一个异步函数。当你在异步上下文中调用工具时，它会使用这个异步函数来操作
#     calculator = StructuredTool.from_function(func=multiply, coroutine=amultiply)
#
#     # invoke同步调用
#     print(calculator.invoke({"a": 2, "b": 3}))
#     # ainvoke异步调用
#     print(await calculator.ainvoke({"a": 2, "b": 5}))
#
# asyncio.run(main())

# **************************************************************************

# from langchain_core.tools import StructuredTool
# from pydantic import BaseModel, Field
# import asyncio
#
#
# class CalculatorInput(BaseModel):
#     a: int = Field(description="first number")
#     b: int = Field(description="second number")
#
# def multiply(a: int, b: int) -> int:
#     """Multiply two numbers."""
#     return a * b
#
# # 创建一个异步包装器函数
# async def async_addition(a: int, b: int) -> int:
#     """Add two numbers."""
#     return a + b
#
# async def main():
#     calculator = StructuredTool.from_function(
#         func=multiply,
#         name="Calculator",
#         description="multiply numbers",
#         args_schema=CalculatorInput,
#         return_direct=True,
#         # coroutine=async_addition
#         # 如有需要，指定异步方法
#     )
#
#     print(calculator.invoke({"a": 2, "b": 3}))
#     # print(await calculator.ainvoke({"a": 2, "b": 5}))
#     print(calculator.name)
#     print(calculator.description)
#     print(calculator.args)
#
# asyncio.run(main())

# **************************************************************************

# 工具异常处理
# from langchain_core.tools import StructuredTool
# from langchain_core.tools import ToolException
#
# def get_weather(city: str) -> int:
#     """获取给定城市的天气。"""
#     raise ToolException(f"错误：没有名为{city}的城市。")
#
# def _handle_error(error: ToolException) -> str:
#     return f"工具调用期间发生以下错误：`{error.args[0]}`"
#
# get_weather_tool = StructuredTool.from_function(
#     func=get_weather,
#     # 为True，则将返回ToolException异常文本；(默认)为False，则将抛出ToolException
#     # handle_tool_error=True
#     # 或者直接写错误描述
#     # handle_tool_error="没这个城市"
#     # 或者使用异常处理函数
#     handle_tool_error=_handle_error,
# )
# response = get_weather_tool.invoke({"city": "foobar"})
# print(response)

# **************************************************************************

# 第三方工具调用 (以维基百科API为例)
# from langchain_community.tools import WikipediaQueryRun
# from langchain_community.utilities import WikipediaAPIWrapper
#
# api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=500)
# tool = WikipediaQueryRun(api_wrapper=api_wrapper)
# print(tool.invoke({"query": "langchain"}))
#
# print(f"Name: {tool.name}")
# print(f"Description: {tool.description}")
# print(f"args schema: {tool.args}")
# print(f"returns directly?: {tool.return_direct}")

# **************************************************************************