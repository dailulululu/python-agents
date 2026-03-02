"""
智能旅行助手 - 主程序
基于 ReAct 模式的 Agent，结合 LLM 与工具调用，使用火山引擎（豆包）。
"""
import os
import re
from openai import OpenAI

from weather import AGENT_SYSTEM_PROMPT
from tools import available_tools, parse_action

VOLC_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
VOLC_DEFAULT_MODEL = "doubao-seed-2-0-code-preview-260215"


def parse_llm_response(text: str) -> tuple[str | None, str | None]:
    """
    从 LLM 回复中解析 Thought 和 Action
    返回 (thought, action_str)
    """
    thought = None
    action = None

    thought_match = re.search(r"Thought:\s*(.+?)(?=Action:|$)", text, re.DOTALL)
    if thought_match:
        thought = thought_match.group(1).strip()

    action_match = re.search(r"Action:\s*(.+?)(?=\n\n|\nThought:|$)", text, re.DOTALL)
    if action_match:
        action = action_match.group(1).strip()

    return thought, action


def run_agent(user_query: str, history: list | None = None, max_turns: int = 10) -> str:
    """
    运行 Agent 主循环（火山引擎豆包）。
    history: 多轮对话历史 [{"role":"user","content":...},{"role":"assistant","content":...}, ...]
    """
    api_key = os.environ.get("VOLC_API_KEY") or os.environ.get("VOLC_ACCESS_TOKEN")
    if not api_key:
        return "错误: 请设置 VOLC_API_KEY 或 VOLC_ACCESS_TOKEN。获取: https://console.volcengine.com/ark"

    model = os.environ.get("VOLC_MODEL") or VOLC_DEFAULT_MODEL
    client = OpenAI(base_url=VOLC_BASE_URL, api_key=api_key)
    api_messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        *(history or []),
        {"role": "user", "content": user_query},
    ]

    for turn in range(max_turns):
        print("\n💭 模型思考:", flush=True)
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=api_messages,
                temperature=0.7,
                timeout=120,
                stream=True,
            )
            assistant_content = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    print(delta, end="", flush=True)
                    assistant_content += delta
            print()
            assistant_content = assistant_content.strip()
        except KeyboardInterrupt:
            print("\n\n已取消。")
            return "请求已取消，请重试。"
        except Exception as e:
            print(f"\n\n错误: 请求失败 - {e}")
            return f"请求失败: {e}"

        # 截断多余的 Thought-Action 对，只保留第一对
        match = re.search(
            r"(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)",
            assistant_content,
            re.DOTALL,
        )
        if match:
            truncated = match.group(1).strip()
            if truncated != assistant_content.strip():
                assistant_content = truncated
                print("  [已截断多余的 Thought-Action 对]")

        if not assistant_content:
            return "错误: 模型返回为空。"
        api_messages.append({"role": "assistant", "content": assistant_content})

        thought, action_str = parse_llm_response(assistant_content)

        if not action_str:
            return "Agent 未返回有效的 Action，请重试。"

        action_type, arg1, arg2 = parse_action(action_str)

        if action_type == "finish":
            print(f"\n✅ 完成")
            return arg1 or "任务已完成。"

        if action_type == "tool":
            print(f"🔧 Action: {arg1}({arg2})")
            func = available_tools.get(arg1)
            if not func:
                tool_result = f"错误: 未知工具 {arg1}"
            else:
                print(f"    ⏳ 正在调用 {arg1}...", end="", flush=True)
                try:
                    tool_result = func(**arg2)
                    print(" 完成")
                except Exception as e:
                    print(f" 失败")
                    tool_result = f"错误: 执行工具时出错 - {e}"

            print(f"📋 结果: {tool_result[:200]}{'...' if len(tool_result) > 200 else ''}\n")

            api_messages.append(
                {
                    "role": "user",
                    "content": f"Observation: {tool_result}\n\n请根据以上结果继续思考，输出下一对 Thought 和 Action。",
                }
            )
        else:
            api_messages.append(
                {
                    "role": "user",
                    "content": "Observation: 无法解析你的 Action，请严格按照格式输出，例如: get_weather(city=\"北京\") 或 Finish[最终答案]",
                }
            )

    return "达到最大轮次限制，任务未完成。"


def main():
    print("=" * 50)
    print("  智能旅行助手（支持多轮对话上下文）")
    print("  输入城市名获取天气和景点推荐，输入 q 退出")
    print("=" * 50)

    conversation_history: list[dict] = []

    while True:
        user_input = input("\n请输入您的问题: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("q", "quit", "exit"):
            print("再见！")
            break

        result = run_agent(user_input, history=conversation_history)
        print(f"\n📌 最终回答:\n{result}")

        # 将本轮对话加入历史，供后续联想上下文
        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": result})


if __name__ == "__main__":
    main()
