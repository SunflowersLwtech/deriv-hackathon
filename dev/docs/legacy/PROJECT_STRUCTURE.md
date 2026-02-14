# Project Structure Guide

## 📁 Directory Structure

```
tradeiq/
├── README.md                 # Main project documentation
├── .env                      # Environment variables (not committed to Git)
├── .gitignore                # Git ignore rules
│
├── backend/                  # Django backend application
│   ├── manage.py            # Django management script
│   ├── requirements.txt     # Python dependencies
│   ├── db.sqlite3           # SQLite database (for development)
│   │
│   ├── tradeiq/            # Django project configuration
│   │   ├── settings.py    # Project settings
│   │   ├── urls.py        # URL routing
│   │   ├── asgi.py        # ASGI configuration (WebSocket)
│   │   └── wsgi.py        # WSGI configuration
│   │
│   ├── agents/             # AI Agent module
│   │   ├── llm_client.py  # DeepSeek unified client
│   │   ├── router.py      # Query routing (Function Calling)
│   │   ├── tools_registry.py  # Tool registry
│   │   ├── prompts.py     # System prompts
│   │   └── compliance.py  # Compliance checks
│   │
│   ├── behavior/           # Behavioral analysis module
│   │   ├── models.py      # Data models
│   │   ├── views.py       # API views
│   │   ├── tools.py       # DeepSeek tool functions
│   │   ├── detection.py   # Pattern detection algorithms
│   │   └── websocket_utils.py  # WebSocket utilities
│   │
│   ├── market/             # Market analysis module
│   │   ├── models.py      # Data models
│   │   ├── views.py       # API views
│   │   └── tools.py       # Market analysis tools
│   │
│   ├── content/            # Content generation module
│   │   ├── models.py      # Data models
│   │   ├── views.py       # API views
│   │   ├── tools.py       # Content generation tools
│   │   ├── bluesky.py     # Bluesky publisher
│   │   └── personas.py    # AI persona configuration
│   │
│   ├── chat/               # WebSocket chat
│   │   ├── consumers.py   # WebSocket consumers
│   │   └── routing.py     # WebSocket routing
│   │
│   ├── demo/               # Demo tools
│   │   └── views.py       # Scenario switching API
│   │
│   └── fixtures/           # Demo data
│       ├── demo_revenge_trading.json
│       ├── demo_overtrading.json
│       ├── demo_loss_chasing.json
│       └── demo_healthy_session.json
│
├── docs/                    # Project documentation
│   ├── DESIGN_DOCUMENT.md  # Design document
│   ├── DEEPSEEK_MIGRATION.md  # DeepSeek migration guide
│   ├── LLM_COST_COMPARISON.md  # LLM cost comparison
│   ├── ENV_CHECKLIST.md    # Environment variable checklist
│   ├── ENV_SETUP.md        # Environment setup guide
│   ├── QUICK_START.md      # Quick start guide
│   ├── PROJECT_STRUCTURE.md  # This file
│   └── REDIS_REQUIREMENT.md  # Redis requirement analysis
│
├── scripts/                 # Utility scripts
│   ├── setup_env.sh        # Environment setup script
│   ├── verify_env.py       # Environment verification script
│   ├── environment.yml     # Conda environment configuration
│   ├── test_bluesky_simple.py  # Bluesky test
│   └── deriv_test.py       # Deriv API test
│
└── dev/                     # Development resources
    ├── diagrams/           # Architecture diagrams (PNG)
    └── docs/               # Original design documents (PDF)
```

## 📂 Directory Descriptions

### backend/
Django backend application containing all business logic and APIs.

**Main Modules:**
- `agents/` - AI Agent routing and tool calling
- `behavior/` - Trading behavior analysis and pattern detection
- `market/` - Market data analysis and explanations
- `content/` - Social media content generation
- `chat/` - WebSocket real-time communication

### docs/
All project documentation, including design documents, migration guides, environment configuration, etc.

### scripts/
Utility scripts and configuration files:
- `setup_env.sh` - Automated environment setup
- `verify_env.py` - Environment verification
- `environment.yml` - Conda environment configuration
- Test scripts

### dev/
Development resources, including architecture diagrams and original design documents.

## 🔄 File Movement History

The following files have been organized from root directory to respective directories:

**Documentation Files** → `docs/`
- `ENV_SETUP.md`
- `ENV_SUMMARY.md`
- `QUICK_START.md`
- `dev/docs/*.md`

**Script Files** → `scripts/`
- `setup_env.sh`
- `verify_env.py`
- `environment.yml`
- `dev/tests/*.py`

## 📝 Usage Instructions

### Running Scripts

```bash
# Environment setup (from project root)
./scripts/setup_env.sh

# Environment verification (from project root)
python scripts/verify_env.py

# Test scripts (from project root)
python scripts/test_bluesky_simple.py
```

### Accessing Documentation

All documentation is in the `docs/` directory and can be accessed via links in README.md.

## 🎯 Best Practices

1. **Code** - Place in `backend/` directory
2. **Documentation** - Place in `docs/` directory
3. **Scripts** - Place in `scripts/` directory
4. **Resources** - Place in `dev/` directory
