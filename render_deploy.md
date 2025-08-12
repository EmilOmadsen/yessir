# 🌐 Deploy to Render - Complete Guide

## Why Render?
- ✅ **Free tier** with 750 hours/month
- ✅ **Always-on** deployment
- ✅ **Easy setup** - just connect GitHub
- ✅ **Automatic HTTPS**
- ✅ **Great for Flask apps**

## Step-by-Step Deployment

### 1. Prepare Your Project
Your project is already ready! You have:
- ✅ `app.py` (Flask app)
- ✅ `requirements.txt` (dependencies)
- ✅ `Procfile` (tells Render how to run)

### 2. Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click "New +" → "Web Service"

### 3. Deploy Your App
1. Connect your GitHub repository: `EmilOmadsen/yessir`
2. Render will auto-detect it's a Python app
3. Set these build settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Environment**: Python 3

### 4. Set Environment Variables
In Render dashboard, add these variables:
```
SPOTIFY_CLIENT_ID=d7a59142072e4223a5e94195be60a1d5
SPOTIFY_CLIENT_SECRET=ef91d4916f9249f985d4bbd545473541
PORT=8080
PUBLIC=true
SECRET_KEY=your-secret-key-change-this
```

### 5. Update Spotify Redirect URI
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Find your app
3. Add this redirect URI:
   ```
   https://your-app-name.onrender.com/callback
   ```
   (Replace `your-app-name` with your actual Render app name)

### 6. Deploy!
- Render will automatically build and deploy
- You'll get a URL like: `https://your-app-name.onrender.com`

## 🎉 Result
- Your app runs **24/7**
- **Always accessible** via the Render URL
- **Automatic HTTPS**
- **No more Codespaces needed**

## Troubleshooting
- If you get build errors, check the Render logs
- Make sure all environment variables are set
- Verify your Spotify redirect URI matches exactly

## Next Steps
1. Deploy to Render
2. Test your app
3. Share the Render URL with others!
