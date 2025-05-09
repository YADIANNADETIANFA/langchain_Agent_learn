import httpx
from mcp.server import FastMCP
from dotenv import load_dotenv
import os


load_dotenv(dotenv_path="../.env")

# 初始化FastMCP服务器
app = FastMCP('web-search')


# 函数名称将作为工具名称
# 参数将作为工具参数
# 通过注释描述工具与参数，以及返回值
@app.tool()
async def web_search(query: str) -> str:
    """
    搜索互联网内容

    Args:
        query: 要搜索的内容

    Returns:
        搜索结果的总结
    """

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

        return '\n\n\n'.join(res_data)


if __name__ == '__main__':
    app.run(transport='stdio')