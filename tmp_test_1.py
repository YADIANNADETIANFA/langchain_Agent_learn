from dotenv import load_dotenv, find_dotenv

# 自动查找 .env 文件并加载
load_dotenv(find_dotenv())

from openai import OpenAI

client = OpenAI()

chat_completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello world"}]
)

print(chat_completion.choices[0].message.content)