# .env 文件配置检查清单

## ✅ 已配置的变量

| 变量 | 状态 | 说明 |
|------|------|------|
| `DATABASE_URL` | ✅ 已配置 | Supabase PostgreSQL 连接字符串 |
| `DEBUG` | ✅ 已配置 | Django 调试模式 |
| `ALLOWED_HOSTS` | ✅ 已配置 | 允许的主机列表 |
| `BLUESKY_HANDLE` | ✅ 已配置 | Bluesky 账号 handle |
| `BLUESKY_APP_PASSWORD` | ✅ 已配置 | Bluesky App Password |
| `DERIV_TOKEN` | ✅ 已配置 | Deriv API Token |
| `DERIV_APP_ID` | ✅ 已配置 | Deriv App ID |
| `NEWS_API_KEY` | ✅ 已配置 | NewsAPI 密钥 |
| `FINNHUB_API_KEY` | ✅ 已配置 | Finnhub API 密钥 |
| `DEEPSEEK_API_KEY` | ✅ 已配置 | DeepSeek LLM API 密钥 |

## ⚠️ 需要更新的变量

### 1. `DJANGO_SECRET_KEY` - **必须更新**

**当前值：** `your-secret-key`  
**问题：** 这是占位符，不安全  
**操作：** 需要生成一个真实的 Django Secret Key

**生成方法：**
```python
# 在 Python shell 中运行：
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

或者使用：
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 📝 可选配置（生产环境）

### Redis 配置（如果需要 WebSocket/实时功能）

当前使用 `InMemoryChannelLayer`，适合开发环境。生产环境建议使用 Redis：

```bash
# Redis (for production WebSocket/Channels)
REDIS_URL=redis://localhost:6379/0
# 或
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Deriv API URL（如果需要自定义）

```bash
# Deriv API URL (optional, defaults to wss://ws.deriv.com/ws/1.0/websocket)
DERIV_API_URL=wss://ws.deriv.com/ws/1.0/websocket
```

## 🔒 安全建议

1. **DJANGO_SECRET_KEY** - 必须替换为随机生成的密钥
2. **生产环境** - 设置 `DEBUG=False`
3. **ALLOWED_HOSTS** - 生产环境需要添加实际域名
4. **API Keys** - 确保不要提交到 Git（已在 .gitignore 中）

## 📋 完整配置模板

```bash
# TradeIQ - Environment Variables

# Database (Supabase connection string from Project Settings -> Database)
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres

# Django
DJANGO_SECRET_KEY=[GENERATE_RANDOM_KEY]  # ⚠️ 必须更新
DEBUG=True  # 生产环境改为 False
ALLOWED_HOSTS=localhost,127.0.0.1  # 生产环境添加实际域名

# Bluesky (Settings -> App Passwords)
BLUESKY_HANDLE=your-handle.bsky.social
BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# Deriv API
DERIV_TOKEN=your-deriv-token
DERIV_APP_ID=your-deriv-app-id
# DERIV_API_URL=wss://ws.deriv.com/ws/1.0/websocket  # 可选

# NewsAPI
NEWS_API_KEY=your-newsapi-key

# Finnhub
FINNHUB_API_KEY=your-finnhub-key

# DeepSeek LLM
DEEPSEEK_API_KEY=sk-your-deepseek-key

# Redis (可选，生产环境推荐)
# REDIS_URL=redis://localhost:6379/0
```

## ✅ 检查清单

- [x] DATABASE_URL 已配置
- [x] 所有 API Keys 已配置
- [ ] **DJANGO_SECRET_KEY 需要更新** ⚠️
- [ ] 生产环境需要设置 DEBUG=False
- [ ] 生产环境需要更新 ALLOWED_HOSTS
- [ ] Redis 配置（如需要 WebSocket）

## 🚀 快速修复

运行以下命令生成 Django Secret Key：

```bash
cd backend
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print('DJANGO_SECRET_KEY=' + get_random_secret_key())"
```

然后将输出复制到 `.env` 文件中替换 `your-secret-key`。
