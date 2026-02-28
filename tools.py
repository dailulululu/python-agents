"""
智能旅行助手的工具函数
"""
import os
import re
import requests
from tavily import TavilyClient


def get_weather(city: str) -> str:
    """
    通过调用 wttr.in API 查询真实的天气信息。
    """
    url = f"https://wttr.in/{city}?format=j1"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        current_condition = data["current_condition"][0]
        weather_desc = current_condition["weatherDesc"][0]["value"]
        temp_c = current_condition["temp_C"]

        return f"{city}当前天气:{weather_desc}，气温{temp_c}摄氏度"

    except requests.exceptions.RequestException as e:
        return f"错误:查询天气时遇到网络问题 - {e}"
    except (KeyError, IndexError) as e:
        return f"错误:解析天气数据失败，可能是城市名称无效 - {e}"


def get_attraction(city: str, weather: str) -> str:
    """
    根据城市和天气，使用 Tavily Search API 搜索并返回优化后的景点推荐。
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "错误:未配置TAVILY_API_KEY环境变量。"

    tavily = TavilyClient(api_key=api_key)
    query = f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由"

    try:
        response = tavily.search(
            query=query, search_depth="basic", include_answer=True
        )

        if response.get("answer"):
            return response["answer"]

        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}: {result['content']}")

        if not formatted_results:
            return "抱歉，没有找到相关的旅游景点推荐。"

        return "根据搜索，为您找到以下信息:\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误:执行Tavily搜索时出现问题 - {e}"


# 将所有工具函数放入一个字典，方便后续调用
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}


def parse_action(action_str: str) -> tuple[str, str | None, dict | None]:
    """
    解析 Action 字符串。
    返回: ("tool", func_name, args) 或 ("finish", answer, None)
    例如: get_weather(city="北京") -> ("tool", "get_weather", {"city": "北京"})
         Finish[这是答案] -> ("finish", "这是答案", None)
    """
    action_str = action_str.strip()
    if action_str.upper().startswith("FINISH"):
        answer = action_str[6:].strip("[] ").strip()
        return "finish", answer, None

    match = re.match(r"(\w+)\s*\((.*)\)", action_str)
    if not match:
        return "unknown", None, None

    func_name = match.group(1)
    args_str = match.group(2)

    if func_name not in available_tools:
        return "unknown", None, None

    args = {}
    for arg_match in re.finditer(r'(\w+)\s*=\s*["\']([^"\']*)["\']', args_str):
        args[arg_match.group(1)] = arg_match.group(2)

    return "tool", func_name, args
