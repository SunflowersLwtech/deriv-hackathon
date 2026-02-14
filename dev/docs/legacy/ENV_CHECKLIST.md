# .env File Configuration Checklist

## ✅ Configured Variables

| Variable | Status | Description |
|----------|--------|-------------|
| `DATABASE_URL` | ✅ Configured | Supabase PostgreSQL connection string |
| `DEBUG` | ✅ Configured | Django debug mode |
| `ALLOWED_HOSTS` | ✅ Configured | Allowed host list |
| `BLUESKY_HANDLE` | ✅ Configured | Bluesky account handle |
| `BLUESKY_APP_PASSWORD` | ✅ Configured | Bluesky App Password |
| `DERIV_TOKEN` | ✅ Configured | Deriv API Token |
| `DERIV_APP_ID` | ✅ Configured | Deriv App ID |
| `NEWS_API_KEY` | ✅ Configured | NewsAPI key |
| `FINNHUB_API_KEY` | ✅ Configured | Finnhub API key |
| `DEEPSEEK_API_KEY` | ✅ Configured | DeepSeek LLM API key |

## ⚠️ Variables That Need Updating

### 1. `DJANGO_SECRET_KEY` - **Must Update**

**Current Value:** `your-secret-key`  
**Issue:** This is a placeholder, not secure  
**Action:** Need to generate a real Django Secret Key

**Generation Method:**
```python
# Run in Python shell:
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Or use:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 📝 Optional Configuration (Production)

### Redis Configuration (If WebSocket/Real-time Features Needed)

Currently using `InMemoryChannelLayer`, suitable for development. Production recommends Redis:

```bash
# Redis (for production WebSocket/Channels)
REDIS_URL=redis://localhost:6379/0
# Or
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Deriv API URL (If Customization Needed)

```bash
# Deriv API URL (optional, defaults to wss://ws.deriv.com/ws/1.0/websocket)
DERIV_API_URL=wss://ws.deriv.com/ws/1.0/websocket
```

## 🔒 Security Recommendations

1. **DJANGO_SECRET_KEY** - Must be replaced with randomly generated key
2. **Production Environment** - Set `DEBUG=False`
3. **ALLOWED_HOSTS** - Production needs to add actual domain names
4. **API Keys** - Ensure not committed to Git (already in .gitignore)

## 📋 Complete Configuration Template

```bash
# TradeIQ - Environment Variables

# Database (Supabase connection string from Project Settings -> Database)
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres

# Django
DJANGO_SECRET_KEY=[GENERATE_RANDOM_KEY]  # ⚠️ Must update
DEBUG=True  # Change to False for production
ALLOWED_HOSTS=localhost,127.0.0.1  # Add actual domain for production

# Bluesky (Settings -> App Passwords)
BLUESKY_HANDLE=your-handle.bsky.social
BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# Deriv API
DERIV_TOKEN=your-deriv-token
DERIV_APP_ID=your-deriv-app-id
# DERIV_API_URL=wss://ws.deriv.com/ws/1.0/websocket  # Optional

# NewsAPI
NEWS_API_KEY=your-newsapi-key

# Finnhub
FINNHUB_API_KEY=your-finnhub-key

# DeepSeek LLM
DEEPSEEK_API_KEY=sk-your-deepseek-key

# Redis (optional, recommended for production)
# REDIS_URL=redis://localhost:6379/0
```

## ✅ Checklist

- [x] DATABASE_URL configured
- [x] All API Keys configured
- [ ] **DJANGO_SECRET_KEY needs updating** ⚠️
- [ ] Production needs DEBUG=False
- [ ] Production needs ALLOWED_HOSTS updated
- [ ] Redis configuration (if WebSocket needed)

## 🚀 Quick Fix

Run the following command to generate Django Secret Key:

```bash
cd backend
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print('DJANGO_SECRET_KEY=' + get_random_secret_key())"
```

Then copy the output to `.env` file to replace `your-secret-key`.
