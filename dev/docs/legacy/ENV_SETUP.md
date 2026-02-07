# TradeIQ 环境配置指南

## 🚀 快速开始

### 方法 1: 使用自动化脚本（推荐）

```bash
# 运行环境设置脚本（从项目根目录）
./scripts/setup_env.sh

# 激活环境
conda activate tradeiq
```

### 方法 2: 手动创建 conda 环境

```bash
# 创建环境
conda env create -f scripts/environment.yml

# 激活环境
conda activate tradeiq

# 安装依赖（如果需要更新）
pip install -r backend/requirements.txt
```

### 方法 3: 使用 requirements.txt（如果不用 conda）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 安装依赖
pip install -r backend/requirements.txt
```

## ✅ 验证环境

运行验证脚本检查所有依赖：

```bash
conda activate tradeiq
python scripts/verify_env.py
```

## 📦 依赖说明

### 核心框架
- **Django 5.0+**: Web 框架
- **Django REST Framework 3.14+**: API 框架
- **Django Channels 4.0+**: WebSocket 支持

### 数据库
- **psycopg2-binary**: PostgreSQL 驱动
- **dj-database-url**: 数据库 URL 解析

### AI/LLM
- **openai 1.0+**: DeepSeek API（OpenAI 兼容）

### 外部 API
- **atproto**: Bluesky AT Protocol
- **requests**: HTTP 客户端

### 工具
- **python-dotenv**: 环境变量管理

## 🔧 环境配置

### 1. 激活环境

```bash
conda activate tradeiq
```

### 2. 配置环境变量

确保 `.env` 文件在项目根目录，包含所有必需的配置（见 `ENV_CHECKLIST.md`）

### 3. 运行 Django 迁移

```bash
cd backend
python manage.py migrate
```

### 4. 创建超级用户（可选）

```bash
python manage.py createsuperuser
```

### 5. 运行开发服务器

```bash
python manage.py runserver
```

## 🐛 常见问题

### 问题 1: conda 命令未找到

**解决方案：**
- 安装 Miniconda 或 Anaconda
- 确保 conda 在 PATH 中
- 重新打开终端

### 问题 2: psycopg2 安装失败

**解决方案：**
```bash
# macOS
brew install postgresql

# 然后重新安装
pip install psycopg2-binary
```

### 问题 3: channels 相关错误

**解决方案：**
```bash
pip install --upgrade channels channels[daphne] daphne
```

### 问题 4: 环境激活后找不到包

**解决方案：**
```bash
# 确保环境已激活
conda activate tradeiq

# 重新安装依赖
pip install -r backend/requirements.txt
```

## 📝 环境管理命令

```bash
# 列出所有 conda 环境
conda env list

# 激活环境
conda activate tradeiq

# 停用环境
conda deactivate

# 删除环境（如果需要）
conda env remove -n tradeiq

# 导出环境（备份）
conda env export > environment_backup.yml
```

## 🔄 更新依赖

```bash
# 激活环境
conda activate tradeiq

# 更新所有包
pip install --upgrade -r backend/requirements.txt

# 或更新单个包
pip install --upgrade django
```

## 📋 Python 版本要求

- **推荐**: Python 3.11
- **最低**: Python 3.10
- **不支持**: Python 3.9 及以下

## ✨ 下一步

环境配置完成后：

1. ✅ 验证环境：`python verify_env.py`
2. ✅ 运行迁移：`cd backend && python manage.py migrate`
3. ✅ 启动服务器：`python manage.py runserver`
4. ✅ 访问：http://localhost:8000
