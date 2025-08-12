# 🚀 Deploy to Heroku (Free Tier)

## Quick Deploy Steps:

### 1. Create Heroku Account
- Go to [heroku.com](https://heroku.com)
- Sign up for free account

### 2. Install Heroku CLI
```bash
# macOS
brew tap heroku/brew && brew install heroku

# Or download from: https://devcenter.heroku.com/articles/heroku-cli
```

### 3. Deploy Your App
```bash
# Login to Heroku
heroku login

# Create Heroku app
heroku create your-spotify-generator

# Set environment variables (replace with your actual values)
heroku config:set SPOTIFY_CLIENT_ID=your_client_id
heroku config:set SPOTIFY_CLIENT_SECRET=your_client_secret
heroku config:set REDIRECT_URI=https://your-app-name.herokuapp.com/callback
heroku config:set PORT=5000
heroku config:set PUBLIC=True

# Deploy
git push heroku main

# Open your app
heroku open
```

### 4. Update Spotify App Settings
- Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- Add your Heroku URL to Redirect URIs:
  - `https://your-app-name.herokuapp.com/callback`

## 🎯 Result:
Your app will be live at: `https://your-app-name.herokuapp.com`

---

# 🚀 Alternative: Deploy to Railway (Free Tier)

## Quick Deploy Steps:

### 1. Create Railway Account
- Go to [railway.app](https://railway.app)
- Sign up with GitHub

### 2. Connect Repository
- Click "New Project"
- Select "Deploy from GitHub repo"
- Choose your `yessir` repository

### 3. Set Environment Variables
- Go to Variables tab
- Add your Spotify credentials:
  - `SPOTIFY_CLIENT_ID`
  - `SPOTIFY_CLIENT_SECRET`
  - `REDIRECT_URI` (Railway will provide this)
  - `PORT=5000`
  - `PUBLIC=True`

### 4. Deploy
- Railway will automatically deploy your app
- Get your live URL from the deployment

## 🎯 Result:
Your app will be live at: `https://your-app-name.railway.app`
