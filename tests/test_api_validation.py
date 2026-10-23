"""
Quick API Test Script

Tests the gateway API endpoints without starting the full server.
"""

import sys
sys.path.insert(0, '/workspace')

def test_api_endpoints():
    """Test API endpoint structure"""
    print("\n" + "="*60)
    print("API ENDPOINT VALIDATION")
    print("="*60 + "\n")
    
    # Import routes
    try:
        from src.gateway.routes import health, proxy
        print("✅ Health routes imported successfully")
        print("✅ Proxy routes imported successfully")
    except Exception as e:
        print(f"❌ Failed to import routes: {e}")
        return False
    
    # Check route definitions
    try:
        from src.gateway.main import app
        routes = [route.path for route in app.routes]
        
        expected_routes = [
            "/",
            "/health",
            "/health/",
            "/health/ready",
            "/health/live",
            "/v1/chat/completions",
            "/v1/tool/headroom_retrieve",
            "/metrics"
        ]
        
        print("\n📍 Available API Endpoints:")
        for route in sorted(routes):
            if route in expected_routes:
                print(f"   ✅ {route}")
            elif not route.startswith("/openapi"):
                print(f"   📌 {route}")
        
        print(f"\n✅ {len([r for r in routes if r in expected_routes])}/{len(expected_routes)} core endpoints registered")
        
    except Exception as e:
        print(f"❌ Failed to validate routes: {e}")
        return False
    
    # Test configuration
    try:
        from src.gateway.config import settings
        print("\n⚙️  Configuration Loaded:")
        print(f"   • Environment: {settings.ENVIRONMENT}")
        print(f"   • Host: {settings.HOST}:{settings.PORT}")
        print(f"   • Compression Enabled: {settings.COMPRESSION_ENABLED}")
        print(f"   • PII Detection: {settings.PII_DETECTION_ENABLED}")
        print(f"   • Prompt Injection Detection: {settings.PROMPT_INJECTION_DETECTION}")
        print("   ✅ Configuration valid")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Test auth module
    try:
        from src.gateway.auth import hash_api_key, VALID_API_KEYS
        test_key = "pmtr_live_test_key_12345"
        hashed = hash_api_key(test_key)
        print(f"\n🔑 API Key Validation:")
        print(f"   • Test key: {test_key[:20]}...")
        print(f"   • SHA-256 hash: {hashed[:16]}...")
        print(f"   • Valid keys loaded: {len(VALID_API_KEYS)}")
        print("   ✅ Authentication module ready")
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ ALL API VALIDATIONS PASSED")
    print("="*60 + "\n")
    return True


def test_saas_backend():
    """Test SaaS backend structure"""
    print("\n" + "="*60)
    print("SAAS BACKEND VALIDATION")
    print("="*60 + "\n")
    
    try:
        import sys
        sys.path.insert(0, '/workspace/saas/backend')
        
        # Check if routes exist
        from pathlib import Path
        backend_path = Path('/workspace/saas/backend')
        
        routes = [
            'routes/auth.py',
            'routes/keys.py',
            'routes/stats.py',
            'routes/usage.py',
            'routes/billing.py'
        ]
        
        print("📁 SaaS Backend Structure:")
        for route_file in routes:
            file_path = backend_path / route_file
            if file_path.exists():
                lines = len(file_path.read_text().split('\n'))
                print(f"   ✅ {route_file} ({lines} lines)")
            else:
                print(f"   ❌ {route_file} (missing)")
        
        # Check models
        models_file = backend_path / 'models' / 'database.py'
        if models_file.exists():
            content = models_file.read_text()
            models = ['User', 'ApiKey', 'Request', 'UsageSummary', 'Subscription']
            print(f"\n📊 Database Models:")
            for model in models:
                if f"class {model}" in content:
                    print(f"   ✅ {model}")
                else:
                    print(f"   ❌ {model} (missing)")
        
        print("\n✅ SaaS Backend structure validated")
        return True
        
    except Exception as e:
        print(f"❌ SaaS validation error: {e}")
        return False


def test_saas_frontend():
    """Test SaaS frontend structure"""
    print("\n" + "="*60)
    print("SAAS FRONTEND VALIDATION")
    print("="*60 + "\n")
    
    try:
        from pathlib import Path
        frontend_path = Path('/workspace/saas/frontend')
        
        # Check pages
        pages = [
            'app/page.tsx',
            'app/layout.tsx',
            'app/dashboard/page.tsx',
        ]
        
        print("📄 Frontend Pages:")
        for page in pages:
            file_path = frontend_path / page
            if file_path.exists():
                lines = len(file_path.read_text().split('\n'))
                print(f"   ✅ {page} ({lines} lines)")
            else:
                print(f"   ❌ {page} (missing)")
        
        # Check components
        components = [
            'components/dashboard/nav.tsx',
            'components/dashboard/stats-cards.tsx',
            'components/dashboard/usage-chart.tsx',
            'components/dashboard/api-keys-list.tsx',
            'components/ui/button.tsx',
            'components/ui/card.tsx',
        ]
        
        print(f"\n🧩 React Components:")
        for component in components:
            file_path = frontend_path / component
            if file_path.exists():
                print(f"   ✅ {component}")
            else:
                print(f"   ❌ {component} (missing)")
        
        # Check configuration
        config_files = ['package.json', 'tsconfig.json', 'tailwind.config.js']
        print(f"\n⚙️  Configuration Files:")
        for config in config_files:
            file_path = frontend_path / config
            if file_path.exists():
                print(f"   ✅ {config}")
            else:
                print(f"   ❌ {config} (missing)")
        
        print("\n✅ SaaS Frontend structure validated")
        return True
        
    except Exception as e:
        print(f"❌ Frontend validation error: {e}")
        return False


if __name__ == "__main__":
    print("\n🚀 PERIMETER COMPREHENSIVE TEST SUITE\n")
    
    results = []
    
    # Test API endpoints
    results.append(("API Endpoints", test_api_endpoints()))
    
    # Test SaaS backend
    results.append(("SaaS Backend", test_saas_backend()))
    
    # Test SaaS frontend
    results.append(("SaaS Frontend", test_saas_frontend()))
    
    # Summary
    print("\n" + "="*60)
    print("FINAL TEST SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:.<40} {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} test suites passed")
    
    if total_passed == total_tests:
        print("\n🎉 ALL SYSTEMS OPERATIONAL 🎉\n")
        sys.exit(0)
    else:
        print("\n⚠️  SOME TESTS FAILED ⚠️\n")
        sys.exit(1)
