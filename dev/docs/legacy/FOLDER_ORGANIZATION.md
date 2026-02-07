# 📁 文件夹整理说明

## ✅ 整理完成

项目文件夹已重新组织，结构更加清晰有序。

## 📋 整理内容

### 1. 文档文件整理

**移动前** → **移动后**

- `ENV_SETUP.md` → `docs/ENV_SETUP.md`
- `ENV_SUMMARY.md` → `docs/ENV_SUMMARY.md`
- `QUICK_START.md` → `docs/QUICK_START.md`
- `dev/docs/*.md` → `docs/*.md`

**结果：** 所有文档统一放在 `docs/` 目录

### 2. 脚本文件整理

**移动前** → **移动后**

- `setup_env.sh` → `scripts/setup_env.sh`
- `verify_env.py` → `scripts/verify_env.py`
- `environment.yml` → `scripts/environment.yml`
- `dev/tests/*.py` → `scripts/*.py`

**结果：** 所有脚本和配置文件统一放在 `scripts/` 目录

### 3. 新增文件

- `README.md` - 项目主文档（根目录）
- `docs/PROJECT_STRUCTURE.md` - 项目结构说明
- `docs/FOLDER_ORGANIZATION.md` - 本文件

### 4. 更新的文件

- `.gitignore` - 添加了更多忽略规则
- `scripts/setup_env.sh` - 更新了路径引用
- `docs/QUICK_START.md` - 更新了脚本路径
- `docs/ENV_SETUP.md` - 更新了脚本路径

## 📂 最终目录结构

```
tradeiq/
├── README.md                 # 📄 项目主文档
├── .env                      # ⚙️ 环境变量
├── .gitignore               # 🚫 Git 忽略规则
│
├── backend/                  # 💻 Django 后端代码
│   ├── agents/              # AI Agent
│   ├── behavior/            # 行为分析
│   ├── market/              # 市场分析
│   ├── content/             # 内容生成
│   ├── chat/                # WebSocket
│   └── ...
│
├── docs/                     # 📚 项目文档
│   ├── DESIGN_DOCUMENT.md
│   ├── DEEPSEEK_MIGRATION.md
│   ├── LLM_COST_COMPARISON.md
│   ├── ENV_CHECKLIST.md
│   ├── ENV_SETUP.md
│   ├── QUICK_START.md
│   ├── PROJECT_STRUCTURE.md
│   └── ...
│
├── scripts/                  # 🛠️ 工具脚本
│   ├── setup_env.sh         # 环境设置
│   ├── verify_env.py        # 环境验证
│   ├── environment.yml      # Conda 配置
│   └── test_*.py            # 测试脚本
│
└── dev/                      # 🎨 开发资源
    ├── diagrams/            # 架构图表
    └── docs/                # 原始文档（PDF）
```

## 🔄 路径更新

### 脚本调用

**之前：**
```bash
./setup_env.sh
python verify_env.py
conda env create -f environment.yml
```

**现在：**
```bash
./scripts/setup_env.sh
python scripts/verify_env.py
conda env create -f scripts/environment.yml
```

### 文档访问

所有文档现在都在 `docs/` 目录下，可以通过 README.md 中的链接访问。

## ✅ 验证整理结果

运行以下命令验证文件位置：

```bash
# 检查文档
ls docs/

# 检查脚本
ls scripts/

# 检查根目录（应该只有 README.md 和配置文件）
ls -1 *.md *.sh *.yml *.py 2>/dev/null || echo "根目录已清理"
```

## 📝 注意事项

1. **脚本路径** - 所有脚本调用都需要使用 `scripts/` 前缀
2. **文档路径** - 文档链接已更新，指向 `docs/` 目录
3. **环境变量** - `.env` 文件仍在根目录（正确位置）
4. **Git 忽略** - 已更新 `.gitignore`，忽略更多临时文件

## 🎯 整理原则

1. **文档集中** - 所有文档放在 `docs/`
2. **脚本集中** - 所有脚本放在 `scripts/`
3. **代码分离** - 后端代码在 `backend/`
4. **资源分离** - 开发资源在 `dev/`
5. **根目录简洁** - 只保留 README 和配置文件

## ✨ 整理完成

项目结构现在更加清晰，便于维护和协作！
