# 🚀 TradeIQ 快速开始指南

## ✅ 环境已配置完成！

Conda 虚拟环境 `tradeiq` 已成功创建并配置完成。

## 📋 快速命令

### 1. 激活环境
```bash
conda activate tradeiq
```

### 2. 进入后端目录
```bash
cd backend
```

### 3. 运行数据库迁移
```bash
python manage.py migrate
```

### 4. 创建超级用户（可选）
```bash
python manage.py createsuperuser
```

### 5. 启动开发服务器
```bash
python manage.py runserver
```

访问：http://localhost:8000

## 🔍 验证环境

```bash
# 在项目根目录
python scripts/verify_env.py
```

## 📦 已安装的包

- ✅ Django 5.2.11
- ✅ Django REST Framework 3.16.1
- ✅ Django Channels 4.3.2
- ✅ OpenAI SDK 1.109.1 (DeepSeek)
- ✅ atproto 0.0.65 (Bluesky)
- ✅ psycopg2-binary 2.9.11
- ✅ 所有其他依赖

## ⚙️ 环境配置

### 环境文件
- `environment.yml` - Conda 环境配置
- `backend/requirements.txt` - Pip 依赖（已优化）
- `.env` - 环境变量（已配置）

### 验证状态
- ✅ Django 配置检查通过
- ✅ 所有依赖已安装
- ✅ 环境变量已配置

## 🎯 下一步

1. **运行迁移**: `python manage.py migrate`
2. **加载演示数据**: `python manage.py loaddata fixtures/demo_*.json`
3. **启动服务器**: `python manage.py runserver`
4. **测试 API**: 访问 http://localhost:8000/api/

## 📚 更多信息

- 详细环境设置：`ENV_SETUP.md`
- 环境检查清单：`ENV_CHECKLIST.md`
- 环境总结：`ENV_SUMMARY.md`
