#!/usr/bin/env python3
"""
Launcher for Spotify Playlist Generator Web Interface
"""

import os
import sys
import webbrowser
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

def check_environment():
    """Check if environment is properly configured"""
    required_vars = ['SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET', 'REDIRECT_URI']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease check your .env file and ensure all variables are set.")
        return False
    
    return True

def main():
    """Main launcher function"""
    print("🎵 Spotify Playlist Generator - Web Interface")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    print("✅ Environment variables configured")
    
    # Check if Flask is installed
    try:
        import flask
        print("✅ Flask is installed")
    except ImportError:
        print("❌ Flask is not installed. Installing...")
        os.system("pip3 install flask==3.0.0")
        print("✅ Flask installed")
    
    # Get port from environment
    port = int(os.getenv('PORT', 3000))
    
    print(f"\n🚀 Starting web server on port {port}...")
    print(f"📱 Web interface will be available at: http://localhost:{port}")
    print("🌐 Opening browser automatically...")
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(2)
        webbrowser.open(f'http://localhost:{port}')
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start the Flask app
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down web server...")
    except Exception as e:
        print(f"\n❌ Error starting web server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
