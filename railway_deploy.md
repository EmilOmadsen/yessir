# 🚀 Quick Railway Deployment Guide

## Your Current Setup:
- **Client ID**: `d7a59142072e4223a5e94195be60a1d5`
- **Client Secret**: `ef91d4916f9249f985d4bbd545473541`
- **Current Redirect**: `http://127.0.0.1:8080/callback`

## Step 1: Deploy to Railway
1. Go to: https://railway.app
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your `yessir` repository

## Step 2: Set Environment Variables
In Railway dashboard, add these variables:
```
SPOTIFY_CLIENT_ID=d7a59142072e4223a5e94195be60a1d5
SPOTIFY_CLIENT_SECRET=ef91d4916f9249f985d4bbd545473541
PORT=5000
PUBLIC=true
```

## Step 3: Get Your Live URL
- Railway will give you a URL like: `https://spot-gen-production-xxxx.up.railway.app`
- **Save this URL** - you'll need it for the redirect URI

## Step 4: Update Spotify Dashboard
1. Go to: https://developer.spotify.com/dashboard
2. Click your app
3. Go to "Edit Settings"
4. In "Redirect URIs", ADD:
   - `https://spot-gen-production-xxxx.up.railway.app/callback`
5. Save changes

## Step 5: Update Railway Environment
In Railway, update the REDIRECT_URI:
```
REDIRECT_URI=https://spot-gen-production-xxxx.up.railway.app/callback
```

## Step 6: Test
Visit your Railway URL and test the Spotify login!

## 🎯 Result:
Your app will be live and accessible from anywhere!
