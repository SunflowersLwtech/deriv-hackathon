#!/usr/bin/env python
"""
Verify TradeIQ environment configuration.
Checks required packages, env vars, and Django settings bootstrap.
"""
import sys
import os
import importlib
from pathlib import Path
from dotenv import load_dotenv

REQUIRED_PACKAGES = {
    'django': '5.0',
    'rest_framework': '3.14',
    'channels': '4.0',
    'openai': '1.0.0',
    'atproto': '0.0.18',
    'psycopg2': '2.9',
    'requests': '2.31.0',
    'dotenv': '1.0',
    'dj_database_url': '2.1',
    'corsheaders': '4.3',
}

REQUIRED_ENV_VARS = [
    'DATABASE_URL',
    'DJANGO_SECRET_KEY',
    'SUPABASE_JWT_SECRET',
    'SUPABASE_URL',
    'DERIV_APP_ID',
    'DERIV_TOKEN',
    'NEWS_API_KEY',
    'FINNHUB_API_KEY',
    'BLUESKY_HANDLE',
    'BLUESKY_APP_PASSWORD',
    'GOOGLE_CLIENT_ID',
    'GOOGLE_CLIENT_SECRET',
    'CALLBACK_URL',
]


def check_package(package_name, min_version=None):
    """Check if a package is installed and optionally verify version"""
    try:
        module = importlib.import_module(package_name)
        version = getattr(module, '__version__', 'unknown')
        
        if min_version:
            # Simple version comparison (major.minor)
            try:
                installed_major, installed_minor = map(int, version.split('.')[:2])
                required_major, required_minor = map(int, min_version.split('.')[:2])
                
                if (installed_major, installed_minor) >= (required_major, required_minor):
                    return True, version, None
                else:
                    return False, version, f"Version {version} < {min_version}"
            except (ValueError, AttributeError):
                return True, version, "Could not verify version"
        
        return True, version, None
    except ImportError:
        return False, None, "Not installed"


def check_env_var(name: str):
    value = (os.environ.get(name) or "").strip()
    return bool(value), len(value)


def main():
    root_dir = Path(__file__).resolve().parent.parent
    backend_dir = root_dir / "backend"
    load_dotenv(root_dir / ".env")

    # Make verify script runnable from project root without extra env exports.
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tradeiq.settings")

    print("=" * 50)
    print("TradeIQ Environment Verification")
    print("=" * 50)
    print()
    
    all_ok = True
    results = []
    
    for package, min_version in REQUIRED_PACKAGES.items():
        # Handle package name differences
        import_name = package.replace('-', '_')
        if import_name == 'dotenv':
            import_name = 'dotenv'
        elif import_name == 'dj_database_url':
            import_name = 'dj_database_url'
        elif import_name == 'corsheaders':
            import_name = 'corsheaders'
        
        is_ok, version, error = check_package(import_name, min_version)
        
        status = "✅" if is_ok else "❌"
        if is_ok:
            results.append(f"{status} {package:20s} {version:15s}")
        else:
            results.append(f"{status} {package:20s} {error}")
            all_ok = False
    
    for result in results:
        print(result)
    
    print()
    print("=" * 50)
    print("\n🔐 Environment Variables:")
    env_all_ok = True
    for key in REQUIRED_ENV_VARS:
        ok, value_len = check_env_var(key)
        status = "✅" if ok else "❌"
        print(f"{status} {key:20s} {'set' if ok else 'missing'} (len={value_len})")
        if not ok:
            env_all_ok = False

    has_deepseek = bool((os.environ.get("DEEPSEEK_API_KEY") or "").strip())
    has_openrouter = bool((os.environ.get("OPENROUTER_API_KEY") or "").strip())
    llm_ok = has_deepseek or has_openrouter
    print(
        f"{'✅' if llm_ok else '❌'} "
        f"{'DEEPSEEK/OPENROUTER':20s} "
        f"{'set' if llm_ok else 'missing'} "
        f"(deepseek={'Y' if has_deepseek else 'N'}, openrouter={'Y' if has_openrouter else 'N'})"
    )
    env_all_ok = env_all_ok and llm_ok
    
    # Check Django settings
    try:
        import django
        django.setup()
        from django.conf import settings
        
        print("\n📋 Django Configuration:")
        print(f"  DEBUG: {settings.DEBUG}")
        print(f"  INSTALLED_APPS: {len(settings.INSTALLED_APPS)} apps")
        print(f"  DATABASES: {settings.DATABASES['default']['ENGINE']}")
        
        # Check channel layers
        if hasattr(settings, 'CHANNEL_LAYERS'):
            backend = settings.CHANNEL_LAYERS['default']['BACKEND']
            print(f"  CHANNEL_LAYERS: {backend}")
        
    except Exception as e:
        print(f"\n⚠️  Could not verify Django settings: {e}")
        env_all_ok = False
    
    print()
    
    if all_ok and env_all_ok:
        print("✅ Environment verification passed!")
        return 0
    else:
        print("❌ Environment verification failed")
        print("\nTo fix, run:")
        print("  conda activate tradeiq")
        print("  pip install -r backend/requirements.txt")
        print("  # then update missing values in .env")
        return 1

if __name__ == '__main__':
    sys.exit(main())
