# 🎵 Spotify Playlist Generator

A Python application that allows you to search for any Spotify playlists and automatically generate new mixed playlists with unique combinations of songs from those playlists.

## Features

- **🎨 Beautiful Web Interface**: Modern, responsive design with intuitive controls
- **🏠 Dashboard**: Discover popular playlists by genre and featured content
- **🔍 Smart Search**: Search for any playlists on Spotify with real-time recommendations
- **💡 Search Recommendations**: Get playlist suggestions as you type (after 2 characters)
- **🎵 Genre Explorer**: Quick access to popular playlists by music genre
- **📱 Multi-Playlist Selection**: Click to select playlists from search results
- **⚙️ Customizable Generation**: Set number of new playlists and tracks per playlist
- **🔄 Duplicate Avoidance**: Option to avoid duplicate tracks across generated playlists
- **🎯 Smart Naming**: Automatic playlist naming based on source playlists
- **🌐 Public/Private Control**: Choose whether new playlists are public or private
- **📊 Visual Feedback**: Real-time progress indicators and status updates
- **🔗 Direct Spotify Links**: One-click access to generated playlists
- **📄 Separate Pages**: Dashboard and Generator on different pages for better organization
- **🌍 Geographic Rankings**: Country-specific playlist rankings via PlaylistRankings API
- **📈 Popularity Data**: Real-time playlist popularity and ranking information
- **🔍 Advanced Search**: Search by keyword and country for targeted results

## Prerequisites

- Python 3.7 or higher
- A Spotify account
- Spotify Developer credentials

## Setup Instructions

### 1. Get Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "Create App"
4. Fill in the app details:
   - **App name**: "Playlist Generator" (or any name you like)
   - **App description**: "A tool to generate mixed playlists"
   - **Website**: `http://127.0.0.1:8080`
   - **Redirect URI**: `http://127.0.0.1:8080/callback`
5. Click "Save"
6. Copy your **Client ID** and **Client Secret**

### 2. Configure the Application

1. Rename `config.env` to `.env` (or copy the contents)
2. Update the `.env` file with your credentials:
   ```
   SPOTIFY_CLIENT_ID=your_actual_client_id_here
   SPOTIFY_CLIENT_SECRET=your_actual_client_secret_here
   REDIRECT_URI=http://127.0.0.1:8080/callback
   PORT=8080
   PUBLIC=false
   ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Option 1: Web Interface (Recommended)

The web interface provides a beautiful, user-friendly experience:

```bash
python run_web.py
```

This will:
- Start a web server on port 8080
- Open your browser automatically
- Provide a modern interface with search, selection, and generation features

### Option 2: Terminal Interface

For command-line usage:

```bash
python spotify_playlist_generator.py
```

### Step-by-Step Process

#### Dashboard (Home Page)
1. **Authentication**: The app will open your browser for Spotify authentication
2. **Explore Genres**: Use quick access buttons or search for specific genres
3. **Discover Popular Playlists**: Browse featured playlists and genre-specific content
4. **Select Playlists**: Click on playlists you like to add them to your selection
5. **Navigate to Generator**: Click "Open Generator" to create mixed playlists

#### Playlist Generator
1. **Smart Search**: Type in the search box and get real-time recommendations
2. **Use Recommendations**: Click on suggested playlists to instantly search for them
3. **Select Playlists**: Choose playlists from search results to add to your mix
4. **Configure Settings**: Set number of playlists, tracks per playlist, and duplicate avoidance
5. **Generate**: Create your mixed playlists with one click

### Example Session

```
🎵 Spotify Playlist Generator
Search for playlists and create mixed playlists!

✅ Successfully authenticated as: Your Name

Step 1: Search for playlists
Enter a search term to find playlists (e.g., 'workout', 'chill', 'party')
Search term: workout

🔍 Searching for playlists: 'workout'

┌─────┬─────────────────────────────────────┬────────────────────┬─────────┬────────┐
│Index│ Name                                │ Creator             │ Tracks  │ Public │
├─────┼─────────────────────────────────────┼────────────────────┼─────────┼────────┤
│  1  │ Workout Mix 2024                    │ Spotify             │   50    │  Yes   │
│  2  │ Gym Motivation                      │ Fitness Fan         │   35    │  Yes   │
│  3  │ Cardio Beats                        │ Workout Pro         │   42    │  Yes   │
└─────┴─────────────────────────────────────┴────────────────────┴─────────┴────────┘

Select playlists to add to your mix
Enter playlist numbers separated by commas (e.g., 1,3,5)
Or type 'search' to search again, or 'done' when finished
Playlist numbers: 1,2

✅ Added 2 playlists to your selection
📋 Total playlists selected: 2

Step 2: Configure generation settings
How many new playlists to create? [3]: 2
How many tracks per playlist? [20]: 15
Avoid duplicate tracks across new playlists? (y/N): y

Step 3: Generate playlists
Creating 2 playlists with 15 tracks each...
Proceed with generation? (y/N): y

📥 Loading tracks from: My Favorites
📥 Loading tracks from: Workout Mix
📊 Total tracks collected: 77
📊 Unique tracks after deduplication: 77
🎵 Creating playlist 1/2: My Favorites + Workout Mix Mix #1
✅ Created: My Favorites + Workout Mix Mix #1 (15 tracks)
🎵 Creating playlist 2/2: My Favorites + Workout Mix Mix #2
✅ Created: My Favorites + Workout Mix Mix #2 (15 tracks)

🎉 Successfully created 2 playlists!
```

## Configuration Options

- **PUBLIC**: Set to `true` to make generated playlists public, `false` for private
- **PORT**: The port for the OAuth callback (default: 8080)
- **REDIRECT_URI**: Must match what you set in Spotify Developer Dashboard

## 🔄 Redirect URI Setup

**Important**: Each user needs to set up their own Spotify API credentials and redirect URI.

### For Local Development:
- **Redirect URI**: `http://127.0.0.1:8080/callback`
- **Port**: 8080 (configurable in .env file)

### For Production Deployment:
If you deploy this app to a live server (Heroku, Railway, etc.), update the redirect URI to your live domain:
- **Example**: `https://your-app-name.herokuapp.com/callback`

## Troubleshooting

### Common Issues

1. **Authentication Failed**: 
   - Check your Client ID and Secret in the `.env` file
   - Ensure the redirect URI matches exactly

2. **No Playlists Found**:
   - Make sure you have playlists in your Spotify account
   - Check that the app has the correct permissions

3. **Permission Errors**:
   - The app needs permissions to read and modify playlists
   - Re-authenticate if needed

### Getting Help

If you encounter issues:
1. Check that all dependencies are installed correctly
2. Verify your Spotify API credentials
3. Ensure your redirect URI is properly configured
4. Check that you have playlists in your Spotify account

## Features in Detail

### Duplicate Avoidance
When enabled, the app ensures that no track appears in multiple generated playlists, giving you maximum variety.

### Smart Naming
The app automatically generates playlist names based on the source playlists:
- Single playlist: "Mixed from [Playlist Name]"
- Two playlists: "[Playlist 1] + [Playlist 2] Mix"
- Multiple playlists: "Mixed from X Playlists"

### Batch Processing
The app handles large playlists efficiently by processing tracks in batches of 100 (Spotify API limit).

## License

This project is open source and available under the MIT License.
