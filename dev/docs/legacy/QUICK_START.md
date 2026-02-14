# 🚀 TradeIQ Quick Start Guide

## ✅ Environment Configured!

Conda virtual environment `tradeiq` has been successfully created and configured.

## 📋 Quick Commands

### 1. Activate Environment
```bash
conda activate tradeiq
```

### 2. Navigate to Backend Directory
```bash
cd backend
```

### 3. Run Database Migrations
```bash
python manage.py migrate
```

### 4. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 5. Start Development Server
```bash
python manage.py runserver
```

Visit: http://localhost:8000

## 🔍 Verify Environment

```bash
# From project root directory
python scripts/verify_env.py
```

## 📦 Installed Packages

- ✅ Django 5.2.11
- ✅ Django REST Framework 3.16.1
- ✅ Django Channels 4.3.2
- ✅ OpenAI SDK 1.109.1 (DeepSeek)
- ✅ atproto 0.0.65 (Bluesky)
- ✅ psycopg2-binary 2.9.11
- ✅ All other dependencies

## ⚙️ Environment Configuration

### Environment Files
- `environment.yml` - Conda environment configuration
- `backend/requirements.txt` - Pip dependencies (optimized)
- `.env` - Environment variables (configured)

### Verification Status
- ✅ Django configuration check passed
- ✅ All dependencies installed
- ✅ Environment variables configured

## 🎯 Next Steps

1. **Run Migrations**: `python manage.py migrate`
2. **Load Demo Data**: `python manage.py loaddata fixtures/demo_*.json`
3. **Start Server**: `python manage.py runserver`
4. **Test API**: Visit http://localhost:8000/api/

## 📚 More Information

- Detailed Environment Setup: `ENV_SETUP.md`
- Environment Checklist: `ENV_CHECKLIST.md`
- Environment Summary: `ENV_SUMMARY.md`
