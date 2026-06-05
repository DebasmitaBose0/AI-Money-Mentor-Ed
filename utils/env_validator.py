import os
import sys

def validate_environment():
    """Validates that all required environment variables are configured.
    
    Generates a diagnostics summary on startup. If critical settings are invalid
    or missing, prints helpful setup instructions.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    
    required = {
        "GROQ_API_KEY": groq_key
    }
    
    missing = []
    placeholders = []
    
    for key, val in required.items():
        if not val:
            missing.append(key)
        elif val.strip() in ("", "your_groq_api_key_here"):
            placeholders.append(key)
            
    if missing or placeholders:
        print("\n" + "="*60, file=sys.stderr)
        print("  ⚠️  ENVIRONMENT VALIDATION WARNING / ERROR", file=sys.stderr)
        print("="*60, file=sys.stderr)
        if missing:
            print(f"  Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        if placeholders:
            print(f"  Placeholder values found for: {', '.join(placeholders)}", file=sys.stderr)
        print("\n  Please follow these steps to configure your environment:", file=sys.stderr)
        print("    1. Copy '.env.example' to '.env'", file=sys.stderr)
        print("    2. Set a valid GROQ_API_KEY in '.env'", file=sys.stderr)
        print("    3. Obtain a free key at https://console.groq.com/\n", file=sys.stderr)
        print("="*60 + "\n", file=sys.stderr)
        
        # If running in production or strictly checked, we could fail.
        # But for development/offline fallback compatibility, we log a warning.
        return False

    print("\n" + "="*60)
    print("  🚀 ENVIRONMENT DIAGNOSTICS: SUCCESS")
    print("="*60)
    print(f"  - FLASK_ENV: {os.getenv('FLASK_ENV', 'development')}")
    print(f"  - FLASK_DEBUG: {os.getenv('FLASK_DEBUG', '1')}")
    print("  - GROQ_API_KEY: Configured (Active)")
    print("="*60 + "\n")
    return True
