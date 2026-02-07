#!/usr/bin/env python
"""
Verify TradeIQ environment configuration
Checks all required packages and versions
"""
import sys
import importlib

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

def main():
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
    
    print()
    
    if all_ok:
        print("✅ All packages verified successfully!")
        return 0
    else:
        print("❌ Some packages are missing or have incorrect versions")
        print("\nTo fix, run:")
        print("  conda activate tradeiq")
        print("  pip install -r backend/requirements.txt")
        return 1

if __name__ == '__main__':
    sys.exit(main())
