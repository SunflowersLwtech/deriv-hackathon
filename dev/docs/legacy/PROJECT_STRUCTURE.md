# 项目结构说明

## 📁 目录结构

```
tradeiq/
├── README.md                 # 项目主文档
├── .env                      # 环境变量（不提交到 Git）
├── .gitignore                # Git 忽略规则
│
├── backend/                  # Django 后端应用
│   ├── manage.py            # Django 管理脚本
│   ├── requirements.txt     # Python 依赖
│   ├── db.sqlite3           # SQLite 数据库（开发用）
│   │
│   ├── tradeiq/            # Django 项目配置
│   │   ├── settings.py    # 项目设置
│   │   ├── urls.py        # URL 路由
│   │   ├── asgi.py        # ASGI 配置（WebSocket）
│   │   └── wsgi.py        # WSGI 配置
│   │
│   ├── agents/             # AI Agent 模块
│   │   ├── llm_client.py  # DeepSeek 统一客户端
│   │   ├── router.py      # 查询路由（Function Calling）
│   │   ├── tools_registry.py  # 工具注册表
│   │   ├── prompts.py     # 系统提示词
│   │   └── compliance.py  # 合规检查
│   │
│   ├── behavior/           # 行为分析模块
│   │   ├── models.py      # 数据模型
│   │   ├── views.py       # API 视图
│   │   ├── tools.py       # DeepSeek 工具函数
│   │   ├── detection.py   # 模式检测算法
│   │   └── websocket_utils.py  # WebSocket 工具
│   │
│   ├── market/             # 市场分析模块
│   │   ├── models.py      # 数据模型
│   │   ├── views.py       # API 视图
│   │   └── tools.py       # 市场分析工具
│   │
│   ├── content/            # 内容生成模块
│   │   ├── models.py      # 数据模型
│   │   ├── views.py       # API 视图
│   │   ├── tools.py       # 内容生成工具
│   │   ├── bluesky.py     # Bluesky 发布器
│   │   └── personas.py    # AI 人设配置
│   │
│   ├── chat/               # WebSocket 聊天
│   │   ├── consumers.py   # WebSocket 消费者
│   │   └── routing.py     # WebSocket 路由
│   │
│   ├── demo/               # 演示工具
│   │   └── views.py       # 场景切换 API
│   │
│   └── fixtures/           # 演示数据
│       ├── demo_revenge_trading.json
│       ├── demo_overtrading.json
│       ├── demo_loss_chasing.json
│       └── demo_healthy_session.json
│
├── docs/                    # 项目文档
│   ├── DESIGN_DOCUMENT.md  # 设计文档
│   ├── DEEPSEEK_MIGRATION.md  # DeepSeek 迁移说明
│   ├── LLM_COST_COMPARISON.md  # LLM 成本对比
│   ├── ENV_CHECKLIST.md    # 环境变量检查清单
│   ├── ENV_SETUP.md        # 环境设置指南
│   ├── QUICK_START.md      # 快速开始指南
│   ├── PROJECT_STRUCTURE.md  # 本文件
│   └── REDIS_REQUIREMENT.md  # Redis 需求分析
│
├── scripts/                 # 工具脚本
│   ├── setup_env.sh        # 环境设置脚本
│   ├── verify_env.py       # 环境验证脚本
│   ├── environment.yml     # Conda 环境配置
│   ├── test_bluesky_simple.py  # Bluesky 测试
│   └── deriv_test.py       # Deriv API 测试
│
└── dev/                     # 开发资源
    ├── diagrams/           # 架构图表（PNG）
    └── docs/               # 原始设计文档（PDF）
```

## 📂 目录说明

### backend/
Django 后端应用，包含所有业务逻辑和 API。

**主要模块：**
- `agents/` - AI Agent 路由和工具调用
- `behavior/` - 交易行为分析和模式检测
- `market/` - 市场数据分析和解释
- `content/` - 社交媒体内容生成
- `chat/` - WebSocket 实时通信

### docs/
所有项目文档，包括设计文档、迁移说明、环境配置等。

### scripts/
工具脚本和配置文件：
- `setup_env.sh` - 自动化环境设置
- `verify_env.py` - 环境验证
- `environment.yml` - Conda 环境配置
- 测试脚本

### dev/
开发资源，包括架构图表和原始设计文档。

## 🔄 文件移动历史

以下文件已从根目录整理到相应目录：

**文档文件** → `docs/`
- `ENV_SETUP.md`
- `ENV_SUMMARY.md`
- `QUICK_START.md`
- `dev/docs/*.md`

**脚本文件** → `scripts/`
- `setup_env.sh`
- `verify_env.py`
- `environment.yml`
- `dev/tests/*.py`

## 📝 使用说明

### 运行脚本

```bash
# 环境设置（从项目根目录）
./scripts/setup_env.sh

# 环境验证（从项目根目录）
python scripts/verify_env.py

# 测试脚本（从项目根目录）
python scripts/test_bluesky_simple.py
```

### 访问文档

所有文档都在 `docs/` 目录下，可以通过 README.md 中的链接访问。

## 🎯 最佳实践

1. **代码** - 放在 `backend/` 目录
2. **文档** - 放在 `docs/` 目录
3. **脚本** - 放在 `scripts/` 目录
4. **资源** - 放在 `dev/` 目录
