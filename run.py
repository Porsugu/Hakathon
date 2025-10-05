#!/usr/bin/env python3
"""
Personal Learning OS Runner
Checks setup and launches the modular application
"""
import os
import sys
import subprocess

def check_files():
    """Check if all required files exist"""
    required_files = [
        'app.py', 'models.py', 'api_manager.py', 'plan_generator.py',
        'learning.py', 'practice.py', 'chat.py', 'ui_styles.py'
    ]

    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)

    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        return False

    print("✅ All modular files found")
    return True

def check_api_key():
    """Check if API key is configured"""
    if os.path.exists('.streamlit/secrets.toml'):
        print("✅ Secrets file found")
        return True
    elif os.getenv('GEMINI_API_KEY'):
        print("✅ API key in environment")
        return True
    else:
        print("⚠️  No API key found. Add to .streamlit/secrets.toml or environment")
        return False

def main():
    print("🧠 Personal Learning OS - Modular Version")
    print("=" * 50)

    if not check_files():
        print("\nPlease ensure all modular files are present.")
        sys.exit(1)

    check_api_key()

    print("\n🚀 Starting modular application...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Application stopped.")

if __name__ == "__main__":
    main()
