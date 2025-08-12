#!/bin/bash

echo "🎵 Spotify Playlist Generator Setup"
echo "=================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3."
    exit 1
fi

echo "✅ pip3 found: $(pip3 --version)"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully!"
else
    echo "❌ Failed to install dependencies. Please check your internet connection and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    cp config.env .env
    echo "✅ .env file created!"
    echo ""
    echo "⚠️  IMPORTANT: Please edit the .env file with your Spotify API credentials:"
    echo "   1. Go to https://developer.spotify.com/dashboard"
    echo "   2. Create a new app"
    echo "   3. Set redirect URI to: http://127.0.0.1:3000/callback"
    echo "   4. Copy your Client ID and Client Secret"
    echo "   5. Update the .env file with your credentials"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To run the application:"
echo "   python3 spotify_playlist_generator.py"
echo ""
echo "For help, see README.md"




