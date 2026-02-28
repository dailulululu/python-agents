"""
火山引擎豆包 API 调用示例
- 纯文本对话
- 图片 + 文本（多模态，与你提供的 curl 一致）
"""
import os
from openai import OpenAI

VOLC_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
MODEL = "doubao-seed-2-0-code-preview-260215"


def chat_text_only(api_key: str, user_text: str) -> str:
    """仅文字对话。"""
    client = OpenAI(base_url=VOLC_BASE_URL, api_key=api_key)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": user_text}],
        temperature=0.7,
    )
    return (resp.choices[0].message.content or "").strip()


def chat_with_image(api_key: str, image_url: str, user_text: str) -> str:
    """
    图片 + 文字（多模态），对应你提供的 curl 格式。
    content 为数组：image_url 与 text 混合。
    """
    client = OpenAI(base_url=VOLC_BASE_URL, api_key=api_key)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {"type": "text", "text": user_text},
                ],
            }
        ],
        temperature=0.7,
    )
    return (resp.choices[0].message.content or "").strip()


if __name__ == "__main__":
    api_key = os.environ.get("VOLC_API_KEY") or os.environ.get("VOLC_ACCESS_TOKEN")
    if not api_key:
        print("请设置环境变量: VOLC_API_KEY 或 VOLC_ACCESS_TOKEN")
        exit(1)

    # 1）纯文本
    print("--- 纯文本 ---")
    reply = chat_text_only(api_key, "用一句话介绍 Python。")
    print(reply)

    # 2）图片 + 文本（与你的 curl 一致）
    print("\n--- 图片 + 文本 ---")
    image_url = "https://ark-project.tos-cn-beijing.ivolces.com/images/view.jpeg"
    reply = chat_with_image(api_key, image_url, "图片主要讲了什么?")
    print(reply)
