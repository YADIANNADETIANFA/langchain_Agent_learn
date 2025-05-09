import httpx
from dataclasses import dataclass
from contextlib import asynccontextmanager
from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from dotenv import load_dotenv
import os


load_dotenv(dotenv_path='../.env')


"""
`@dataclass`装饰器，作用是将普通类自动转化为数据类(Data Class)。
    它可以简化类的定义，自动为类添加如下方法:
        + `__init__()`: 初始化方法
        + `__repr__()`: 可打印的字符串表示
        + `__eq__()`: 对象比较方法
        + `__hash__()`: (可选)

等价为如下代码:
class AppContext:
    def __init__(self, histories: dict):
        self.histories = histories
    def __repr__(self):
        return f"AppContext(histories={self.histories})"
"""
@dataclass
# 初始化一个生命周期上下文对象
class AppContext:
    # 该字段用于存储请求历史
    histories: dict


# 异步上下文管理器
@asynccontextmanager
async def app_lifespan(server):
    # 在MCP初始化时执行
    histories = {}
    try:
        # 返回的`AppContext(history)`对象，会在整个MCP服务的生命周期内，作为共享资源使用
        # 每次tool请求，都可以访问到这个共享资源对象(共享上下文对象)
        # 所有tool请求，都可以访问和更新这个共享的histories字典
        # (这里只会被调用一次，即在MCP服务启动时调用。返回的`AppContext(history)`会被框架保存并重复使用。每次tool请求，会直接访问和修改这个共享对象本体，而非拷贝体)
        yield AppContext(histories)
    finally:
        # 当MCP服务关闭时执行
        print(histories)


app = FastMCP(
    'web-search',
    # 设置生命周期监听函数
    # 将`app_lifespan`函数作为生命周期钩子传入`FastMCP`
    #   + MCP在服务启动时，会进入`app_lifespan()`上下文
    #   + MCP在服务关闭时，会自动退出上下文
    lifespan=app_lifespan,
)


# 第一个参数会被传入上下文对象 (每次工具被调用时，`ctx`都是由`app_lifespan`提供的上下文对象)
@app.tool()
async def web_search(ctx: Context, query: str) -> str:
    """
    搜索互联网内容

    Args:
        query: 要搜索内容

    Returns:
        搜索结果的总结
    """

    # 如果之前问过同样的问题，就直接返回缓存
    histories = ctx.request_context.lifespan_context.histories
    if query in histories:
        return histories[query]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://open.bigmodel.cn/api/paas/v4/tools',
            headers={'Authorization': os.getenv('ZHIPU_API_KEY')},
            json={
                'tool': 'web-search-pro',
                'messages': [
                    {'role': 'user', 'content': query}
                ],
                'stream': False
            }
        )

        res_data = []
        for choice in response.json()['choices']:
            for message in choice['message']['tool_calls']:
                search_results = message.get('search_result')
                if not search_results:
                    continue
                for result in search_results:
                    res_data.append(result['content'])

        return_data = '\n\n\n'.join(res_data)

        # 将查询值和返回值存入到histories中
        ctx.request_context.lifespan_context.histories[query] = return_data

        return return_data


if __name__ == '__main__':
    app.run(transport='stdio')
