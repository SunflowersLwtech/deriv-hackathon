# TradeIQ Environment Setup Guide

## 🚀 Quick Start

### Method 1: Using Automated Script (Recommended)

```bash
# Run environment setup script (from project root)
./scripts/setup_env.sh

# Activate environment
conda activate tradeiq
```

### Method 2: Manual Conda Environment Creation

```bash
# Create environment
conda env create -f scripts/environment.yml

# Activate environment
conda activate tradeiq

# Install dependencies (if update needed)
pip install -r backend/requirements.txt
```

### Method 3: Using requirements.txt (If Not Using Conda)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

## ✅ Verify Environment

Run verification script to check all dependencies:

```bash
conda activate tradeiq
python scripts/verify_env.py
```

## 📦 Dependency Overview

### Core Framework
- **Django 5.0+**: Web framework
- **Django REST Framework 3.14+**: API framework
- **Django Channels 4.0+**: WebSocket support

### Database
- **psycopg2-binary**: PostgreSQL driver
- **dj-database-url**: Database URL parser

### AI/LLM
- **openai 1.0+**: DeepSeek API (OpenAI compatible)

### External APIs
- **atproto**: Bluesky AT Protocol
- **requests**: HTTP client

### Utilities
- **python-dotenv**: Environment variable management

## 🔧 Environment Configuration

### 1. Activate Environment

```bash
conda activate tradeiq
```

### 2. Configure Environment Variables

Ensure `.env` file is in project root directory with all required configuration (see `ENV_CHECKLIST.md`)

### 3. Run Django Migrations

```bash
cd backend
python manage.py migrate
```

### 4. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

## 🐛 Common Issues

### Issue 1: conda command not found

**Solution:**
- Install Miniconda or Anaconda
- Ensure conda is in PATH
- Restart terminal

### Issue 2: psycopg2 installation failed

**Solution:**
```bash
# macOS
brew install postgresql

# Then reinstall
pip install psycopg2-binary
```

### Issue 3: channels related errors

**Solution:**
```bash
pip install --upgrade channels channels[daphne] daphne
```

### Issue 4: Packages not found after environment activation

**Solution:**
```bash
# Ensure environment is activated
conda activate tradeiq

# Reinstall dependencies
pip install -r backend/requirements.txt
```

## 📝 Environment Management Commands

```bash
# List all conda environments
conda env list

# Activate environment
conda activate tradeiq

# Deactivate environment
conda deactivate

# Remove environment (if needed)
conda env remove -n tradeiq

# Export environment (backup)
conda env export > environment_backup.yml
```

## 🔄 Update Dependencies

```bash
# Activate environment
conda activate tradeiq

# Update all packages
pip install --upgrade -r backend/requirements.txt

# Or update single package
pip install --upgrade django
```

## 📋 Python Version Requirements

- **Recommended**: Python 3.11
- **Minimum**: Python 3.10
- **Not Supported**: Python 3.9 and below

## ✨ Next Steps

After environment configuration:

1. ✅ Verify environment: `python verify_env.py`
2. ✅ Run migrations: `cd backend && python manage.py migrate`
3. ✅ Start server: `python manage.py runserver`
4. ✅ Visit: http://localhost:8000
