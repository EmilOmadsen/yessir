#!/bin/bash

# Set environment variables for Spotify API
export SPOTIFY_CLIENT_ID=d7a59142072e4223a5e94195be60a1d5
export SPOTIFY_CLIENT_SECRET=ef91d4916f9249f985d4bbd545473541
export PORT=8080
export PUBLIC=true

# Get the Codespace URL for redirect URI
CODESPACE_URL=$(echo $CODESPACES)
if [ -z "$CODESPACE_URL" ]; then
    CODESPACE_URL="https://$CODESPACE_NAME-$GITHUB_USER.preview.app.github.dev"
fi

export REDIRECT_URI="$CODESPACE_URL/callback"

echo "✅ Environment variables set:"
echo "SPOTIFY_CLIENT_ID: $SPOTIFY_CLIENT_ID"
echo "SPOTIFY_CLIENT_SECRET: $SPOTIFY_CLIENT_SECRET"
echo "REDIRECT_URI: $REDIRECT_URI"
echo "PORT: $PORT"
echo "PUBLIC: $PUBLIC"

# Install dependencies
pip install -r requirements.txt

# Run the app
echo "🚀 Starting Spotify Playlist Generator..."
python app.py
