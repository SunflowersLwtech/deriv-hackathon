# DeepSeek 统一迁移完成 ✅

## 概述

项目已完全迁移到使用最新的 **DeepSeek-V3.2** 作为统一的 LLM 提供商，支持 function calling 和 tool use。

## 更改内容

### 1. 统一的 DeepSeek 客户端 (`backend/agents/llm_client.py`)

创建了统一的 `DeepSeekClient` 类，提供：
- **deepseek-reasoner**: 用于需要工具调用的场景（Market Analyst）
- **deepseek-chat**: 用于简单对话场景（Behavioral Coach, Content Creator）
- 支持 function calling / tool use
- 统一的 API 接口

### 2. 更新的模块

#### ✅ Behavioral Coach (`backend/behavior/tools.py`)
- 已更新使用统一的 `get_llm_client()`
- 继续使用 `deepseek-chat` 模型
- 功能：生成个性化的交易行为建议

#### ✅ Market Analyst (`backend/market/tools.py`)
- **新实现**：完整的市场分析工具
- 功能：
  - `fetch_price_data()` - 获取价格数据
  - `search_news()` - 搜索新闻（使用 NewsAPI）
  - `get_sentiment()` - 情感分析（使用 DeepSeek）
  - `explain_market_move()` - 解释市场波动
- 使用 `deepseek-chat` 进行文本生成

#### ✅ Content Creator (`backend/content/tools.py`)
- **新实现**：内容生成工具
- 功能：
  - `generate_draft()` - 生成单个帖子
  - `generate_thread()` - 生成线程（多个帖子）
  - `format_for_platform()` - 平台格式化
- 使用 `deepseek-chat` 模型

#### ✅ Agent Router (`backend/agents/router.py`)
- **完全重写**：使用 DeepSeek function calling
- 支持三种 Agent 类型：
  - `market` - 市场分析
  - `behavior` - 行为教练
  - `content` - 内容生成
- 自动工具调用和执行

#### ✅ Tools Registry (`backend/agents/tools_registry.py`)
- **完全重写**：DeepSeek 工具注册表
- 注册所有可用工具
- 提供工具执行映射

### 3. 依赖更新 (`backend/requirements.txt`)

添加了：
- `openai>=1.0.0` - DeepSeek API（OpenAI 兼容）
- `requests>=2.31.0` - 用于 NewsAPI 等外部 API

## DeepSeek 模型选择

| Agent | 模型 | 用途 |
|--------|------|------|
| Behavioral Coach | `deepseek-chat` | 生成行为建议（简单对话） |
| Market Analyst | `deepseek-reasoner` | 工具调用 + 市场分析 |
| Content Creator | `deepseek-chat` | 生成社交媒体内容 |

## 配置要求

确保 `.env` 文件包含：

```bash
DEEPSEEK_API_KEY=your-deepseek-api-key-here
```

获取 API Key: https://platform.deepseek.com/

## 使用示例

### Market Analyst
```python
from agents.router import route_market_query

result = route_market_query("Why did EUR/USD spike 1.2%?")
# 自动调用: search_news, get_sentiment, explain_market_move
```

### Behavioral Coach
```python
from agents.router import route_behavior_query

result = route_behavior_query(
    "Analyze my recent trading patterns",
    user_id="user-uuid"
)
# 自动调用: get_recent_trades, analyze_trade_patterns
```

### Content Creator
```python
from content.tools import generate_draft

draft = generate_draft(
    persona_id="persona-uuid",
    topic="EUR/USD market analysis",
    platform="bluesky"
)
```

## 优势

1. ✅ **统一技术栈** - 所有 LLM 调用使用同一个提供商
2. ✅ **成本优化** - DeepSeek 价格远低于 Claude/GPT-4
3. ✅ **功能完整** - 支持 function calling 和 tool use
4. ✅ **中文支持** - DeepSeek 对中文支持优秀
5. ✅ **最新模型** - 使用 DeepSeek-V3.2（2025年最新）

## 下一步

1. 获取 DeepSeek API Key 并配置到 `.env`
2. 测试各个 Agent 的功能
3. 根据需要调整 prompt 和参数

## 注意事项

- DeepSeek API 使用 OpenAI 兼容格式，但 base_url 不同
- Function calling 需要 `deepseek-reasoner` 模型
- 简单对话可以使用 `deepseek-chat`（更便宜）
- 所有工具函数都有错误处理和 fallback 机制
