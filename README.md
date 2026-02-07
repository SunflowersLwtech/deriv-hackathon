# TradeIQ - Intelligent Trading Analyst

> The Bloomberg Terminal for retail traders, the trading coach they never had, and the content team they always wanted.

## 🚀 快速开始

### 1. 环境设置

```bash
# 使用自动化脚本（推荐）
./scripts/setup_env.sh

# 或手动创建
conda env create -f scripts/environment.yml
conda activate tradeiq
```

### 2. 配置环境变量

确保 `.env` 文件已配置（见 `docs/ENV_CHECKLIST.md`）

### 3. 运行项目

```bash
cd backend
python manage.py migrate
python manage.py runserver
```

访问：http://localhost:8000

## 📁 项目结构

```
tradeiq/
├── backend/              # Django 后端应用
│   ├── agents/           # AI Agent 路由和工具
│   ├── behavior/        # 行为分析模块
│   ├── market/           # 市场分析模块
│   ├── content/          # 内容生成模块
│   ├── chat/             # WebSocket 聊天
│   └── demo/             # 演示工具
│
├── docs/                 # 项目文档
│   ├── DESIGN_DOCUMENT.md
│   ├── DEEPSEEK_MIGRATION.md
│   ├── LLM_COST_COMPARISON.md
│   ├── ENV_CHECKLIST.md
│   ├── ENV_SETUP.md
│   ├── QUICK_START.md
│   └── ...
│
├── scripts/              # 工具脚本
│   ├── setup_env.sh      # 环境设置脚本
│   ├── verify_env.py     # 环境验证脚本
│   ├── environment.yml   # Conda 环境配置
│   └── test_*.py         # 测试脚本
│
├── dev/                  # 开发资源
│   ├── diagrams/         # 架构图表
│   └── docs/             # 原始设计文档
│
├── .env                  # 环境变量（不提交到 Git）
├── .gitignore
└── README.md             # 本文件
```

## 🎯 核心功能

1. **Market Analysis** - 实时市场分析和解释
2. **Behavioral Coaching** - 交易行为模式检测和建议
3. **Social Content Engine** - AI 生成社交媒体内容

## 🛠️ 技术栈

- **Backend**: Django 5 + DRF + Channels
- **AI/LLM**: DeepSeek-V3.2 (Function Calling)
- **Database**: Supabase (PostgreSQL)
- **WebSocket**: Django Channels (InMemoryChannelLayer)
- **External APIs**: Deriv, NewsAPI, Bluesky

## 📚 文档

- [快速开始指南](docs/QUICK_START.md)
- [环境设置指南](docs/ENV_SETUP.md)
- [设计文档](docs/DESIGN_DOCUMENT.md)
- [DeepSeek 迁移说明](docs/DEEPSEEK_MIGRATION.md)
- [LLM 成本对比](docs/LLM_COST_COMPARISON.md)

## 🔧 开发工具

```bash
# 验证环境
python scripts/verify_env.py

# 运行测试
cd backend
python manage.py test

# 加载演示数据
python manage.py loaddata fixtures/demo_*.json
```

## 📝 许可证

Deriv AI Hackathon 2026
