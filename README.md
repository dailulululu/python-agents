# 智能旅行助手 Agent Demo

基于 ReAct 模式的智能体，结合 LLM 与工具调用，实现天气查询和景点推荐。

## 项目结构

```
agentDemo/
├── weither.py      # 指令模板 (AGENT_SYSTEM_PROMPT)
├── tools.py        # 工具函数: get_weather, get_attraction
├── main.py         # 主程序入口
├── requirements.txt
└── README.md
```

## 环境准备

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

| 变量名 | 说明 |
|--------|------|
| `VOLC_API_KEY` 或 `VOLC_ACCESS_TOKEN` | 火山引擎 API Key（必填） |
| `VOLC_MODEL` | 可选，默认 `doubao-seed-2-0-code-preview-260215` |
| `TAVILY_API_KEY` | Tavily 景点搜索（必填） |

```powershell
$env:VOLC_API_KEY = "你的API_Key"
$env:TAVILY_API_KEY = "你的Tavily密钥"
```

> 获取：火山 https://console.volcengine.com/ark | Tavily https://tavily.com  

## 运行

```bash
python main.py
```

运行后输入问题，例如：
- `北京今天天气怎么样？有什么推荐景点？`
- `上海适合出游吗？`

输入 `q` 退出。
