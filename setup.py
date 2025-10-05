"""
Enhanced setup script for Learning OS
Handles database initialization, environment checks, and first-time setup
"""
import os
import sys
from database_setup import setup_database
from config import Config
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} is compatible")
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'streamlit', 'google-generativeai'
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} is missing")

    if missing:
        print(f"\nTo install missing packages, run:")
        print(f"pip install {' '.join(missing)}")
        return False

    return True

def check_environment():
    """Check if environment variables are set up"""
    # First check environment variable
    if os.getenv('GEMINI_API_KEY'):
        print("✅ GEMINI_API_KEY found in environment")
        return True

    # Next check .streamlit/secrets.toml
    secrets_path = Path('.streamlit') / 'secrets.toml'
    if secrets_path.exists():
        try:
            content = secrets_path.read_text()
            if 'GEMINI_API_KEY' in content:
                print("✅ GEMINI_API_KEY found in .streamlit/secrets.toml")
                return True
        except Exception:
            pass

    # Prompt to create secrets.toml
    print("GEMINI_API_KEY not found in environment or .streamlit/secrets.toml.")
    create = input('Would you like to create .streamlit/secrets.toml now? (y/N): ').strip().lower()
    if create == 'y':
        api_key = input('Enter your GEMINI API key: ').strip()
        if not api_key:
            print('No API key entered. Skipping.')
            return False
        os.makedirs('.streamlit', exist_ok=True)
        with open(secrets_path, 'w') as f:
            f.write(f'GEMINI_API_KEY = "{api_key}"\n')
        print(f'✅ Wrote {secrets_path} (DO NOT commit this file)')
        return True

    print('❌ API key not configured')
    return False

def setup_database_and_user():
    """Set up database and create default user if needed"""
    print("\n🔧 Setting up database...")

    try:
        setup_database()

        # Import here to avoid circular imports
        from db_functions import add_user, get_user_by_username

        # Create default user if it doesn't exist
        default_user = get_user_by_username("demo_user")
        if not default_user:
            # Using a simple hash for demo purposes
            import hashlib
            password_hash = hashlib.md5("demo123".encode()).hexdigest()

            if add_user("demo_user", password_hash):
                print("✅ Created demo user (username: demo_user, password: demo123)")
            else:
                print("⚠️  Demo user already exists")
        else:
            print("✅ Demo user already exists")

        return True

    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_streamlit_config():
    """Create .streamlit/config.toml for better app experience"""
    os.makedirs('.streamlit', exist_ok=True)

    config_toml = '''[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[server]
headless = true
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
'''

    config_path = '.streamlit/config.toml'
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            f.write(config_toml)
        print("✅ Created Streamlit configuration")
    else:
        print("✅ Streamlit configuration already exists")

def main():
    """Main setup function"""
    print("🚀 Learning OS Setup")
    print("=" * 50)

    success = True

    # Check Python version
    if not check_python_version():
        success = False

    # Check dependencies
    if not check_dependencies():
        success = False

    # Check environment configuration
    if not check_environment():
        success = False

    if not success:
        print("\n❌ Setup failed. Please fix the issues above.")
        return False

    # Set up database
    if not setup_database_and_user():
        success = False

    # Create Streamlit config
    create_streamlit_config()

    if success:
        print("\n🎉 Setup completed successfully!")
        print("\n🚀 To run the application:")
        print("streamlit run main.py")
        print("\n💡 Demo credentials:")
        print("Username: demo_user")
        print("Password: demo123")
    else:
        print("\n❌ Setup completed with errors. Please review above.")

    return success

if __name__ == "__main__":
    main()
