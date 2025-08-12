#!/usr/bin/env python3
"""
Spotify Playlist Generator - Web Interface
A Flask web application for creating mixed playlists from Spotify search results.
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from dotenv import load_dotenv
import time
import json
import requests

# Load environment variables
load_dotenv('.env')

# For Railway deployment, also check for direct environment variables
if not os.getenv('SPOTIFY_CLIENT_ID'):
    print("⚠️  SPOTIFY_CLIENT_ID not found in environment")
if not os.getenv('SPOTIFY_CLIENT_SECRET'):
    print("⚠️  SPOTIFY_CLIENT_SECRET not found in environment")
if not os.getenv('REDIRECT_URI'):
    print("⚠️  REDIRECT_URI not found in environment")

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

class SpotifyPlaylistGenerator:
    def __init__(self):
        self.sp = None
        self.user_id = None
        self.auth_manager = None
    
    def authenticate_user(self, client_id, client_secret, redirect_uri):
        """Authenticate user with Spotify OAuth"""
        try:
            scope = "playlist-read-private playlist-modify-public playlist-modify-private user-library-read user-read-private"
            
            self.auth_manager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope,
                cache_handler=spotipy.cache_handler.CacheFileHandler(cache_path=".spotify_cache")
            )
            
            # Check if we have a valid token
            if self.auth_manager.get_cached_token():
                self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
                user_info = self.sp.current_user()
                self.user_id = user_info['id']
                print(f"✅ User authenticated: {user_info['display_name']}")
                return True
            else:
                print("❌ No cached token found, user needs to authenticate")
                return False
                
        except Exception as e:
            print(f"❌ User authentication failed: {e}")
            return False
    
    def authenticate_client(self, client_id, client_secret):
        """Authenticate with client credentials for public searches"""
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            ))
            print("✅ Client credentials authentication successful")
            return True
        except Exception as e:
            print(f"❌ Client authentication failed: {e}")
            return False
    
    def get_auth_url(self):
        """Get Spotify OAuth URL for user authentication"""
        if self.auth_manager:
            return self.auth_manager.get_authorize_url()
        return None
    
    def handle_callback(self, code):
        """Handle OAuth callback"""
        try:
            if self.auth_manager:
                self.auth_manager.get_access_token(code)
                self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
                user_info = self.sp.current_user()
                self.user_id = user_info['id']
                print(f"✅ User authenticated via callback: {user_info['display_name']}")
                return True
        except Exception as e:
            print(f"❌ Callback authentication failed: {e}")
        return False
    
    def get_user_playlists(self, limit=50):
        """Get user's playlists"""
        try:
            if not self.sp or not self.user_id:
                return []
            
            playlists = []
            offset = 0
            
            while len(playlists) < limit:
                results = self.sp.current_user_playlists(limit=min(50, limit - len(playlists)), offset=offset)
                if not results['items']:
                    break
                    
                for playlist in results['items']:
                    if playlist is None:
                        continue
                    playlists.append(playlist)
                    
                offset += 50
                
            return playlists
        except Exception as e:
            print(f"Error getting user playlists: {e}")
            return []
    
    def get_playlist_tracks_detailed(self, playlist_id):
        """Get detailed track information from a playlist"""
        try:
            if not self.sp:
                return []
            
            tracks = []
            offset = 0
            limit = 100
            
            while True:
                results = self.sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
                if not results or not results['items']:
                    break
                    
                for item in results['items']:
                    if item and item['track']:
                        # Get detailed track info including audio features
                        track_info = {
                            'id': item['track']['id'],
                            'name': item['track']['name'],
                            'artist': item['track']['artists'][0]['name'] if item['track']['artists'] else 'Unknown',
                            'album': item['track']['album']['name'],
                            'duration_ms': item['track']['duration_ms'],
                            'popularity': item['track']['popularity'],
                            'uri': item['track']['uri'],
                            'added_at': item['added_at']
                        }
                        tracks.append(track_info)
                
                if len(results['items']) < limit:
                    break
                offset += limit
            
            return tracks
        except Exception as e:
            print(f"Error getting playlist tracks: {e}")
            return []
    
    def get_recommendations(self, seed_tracks, limit=20):
        """Get Spotify recommendations based on seed tracks"""
        try:
            if not self.sp:
                return []
            
            # Get track IDs (max 5 for recommendations)
            track_ids = [track['id'] for track in seed_tracks[:5]]
            
            recommendations = self.sp.recommendations(
                seed_tracks=track_ids,
                limit=limit,
                target_popularity=50
            )
            
            return recommendations['tracks']
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return []
    
    def create_playlist_for_user(self, name, description, tracks, is_public=True):
        """Create a new playlist for the authenticated user"""
        try:
            if not self.sp or not self.user_id:
                raise Exception("User not authenticated")
            
            # Create the playlist
            playlist = self.sp.user_playlist_create(
                user=self.user_id,
                name=name,
                public=is_public,
                description=description
            )
            
            # Add tracks to the playlist
            track_uris = [track['uri'] for track in tracks if track.get('uri')]
            
            if track_uris:
                # Spotify API has a limit of 100 tracks per request
                for i in range(0, len(track_uris), 100):
                    batch = track_uris[i:i+100]
                    self.sp.playlist_add_items(playlist['id'], batch)
            
            return playlist
            
        except Exception as e:
            print(f"Error creating playlist: {e}")
            return None
    
    def search_playlists(self, query, limit=20):
        """Search for playlists on Spotify"""
        try:
            if not self.sp:
                raise Exception("Spotify client not authenticated")
                
            results = self.sp.search(q=query, type='playlist', limit=limit)
            
            if not results or 'playlists' not in results:
                print(f"No results found for query: {query}")
                return []
                
            playlists = results['playlists']['items']
            
            # Get detailed playlist information including followers
            detailed_playlists = []
            for playlist in playlists:
                # Skip None playlists
                if playlist is None:
                    continue
                    
                try:
                    # Get full playlist details including followers
                    detailed_playlist = self.sp.playlist(playlist['id'], fields='id,name,owner,tracks.total,public,images,external_urls,followers,description')
                    detailed_playlists.append(detailed_playlist)
                except Exception as e:
                    print(f"Error getting detailed playlist info for {playlist.get('id', 'unknown')}: {e}")
                    detailed_playlists.append(playlist)
            
            return detailed_playlists
        except Exception as e:
            print(f"Error searching playlists: {str(e)}")
            return []
    
    def generate_playlist_name(self, source_playlists):
        """Generate a creative name for the new playlist"""
        names = [p['name'] for p in source_playlists]
        if len(names) == 1:
            return f"Mixed from {names[0]}"
        elif len(names) == 2:
            return f"{names[0]} + {names[1]} Mix"
        else:
            return f"Mixed from {len(names)} Playlists"

# Global generator instance
generator = SpotifyPlaylistGenerator()

class PlaylistRankingsAPI:
    """Handle PlaylistRankings API calls"""
    
    def __init__(self):
        self.base_url = "https://www.playlistrankings.com/api"
        self.api_key = '15|7u1AevqJpuiDCPjJ1HBIgZMgaUYirJMgsYrva3dG3f7dd351'
    
    def get_playlist_rankings(self, spotify_id):
        """Get current rankings for a playlist"""
        try:
            if not self.api_key:
                print("No PlaylistRankings API key configured")
                return []
                
            url = f"{self.base_url}/playlists/{spotify_id}/rankings"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching playlist rankings: {e}")
            return []
    
    def get_keyword_rankings(self, keyword):
        """Get current ranking playlists for a keyword"""
        try:
            if not self.api_key:
                print("No PlaylistRankings API key configured")
                return {}
                
            import urllib.parse
            encoded_keyword = urllib.parse.quote(keyword)
            url = f"{self.base_url}/keywords/{encoded_keyword}/rankings"
            print(f"Fetching rankings for keyword: {keyword} from {url}")
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 419 or response.status_code == 429:
                print(f"Rate limit exceeded for PlaylistRankings API (status: {response.status_code})")
                return {}
            
            response.raise_for_status()
            
            if response.text.strip():
                data = response.json()
                print(f"Successfully fetched {len(data)} countries for keyword '{keyword}'")
                return data
            else:
                print(f"Empty response for keyword: {keyword}")
                return {}
                
        except requests.exceptions.RequestException as e:
            print(f"Request error for keyword '{keyword}': {e}")
            return {}
        except json.JSONDecodeError as e:
            print(f"JSON decode error for keyword '{keyword}': {e}")
            print(f"Response content: {response.text[:200]}...")
            return {}
        except Exception as e:
            print(f"Unexpected error fetching keyword rankings for '{keyword}': {e}")
            return {}
    
    def get_popular_keywords(self):
        """Get a list of popular keywords for dashboard"""
        popular_keywords = [
            "deep house", "lofi", "workout", "chill", "party", "rock", "pop", "jazz",
            "hip hop", "electronic", "classical", "country", "r&b", "reggae", "blues"
        ]
        return popular_keywords
    
    def get_popular_countries(self):
        """Get a comprehensive list of countries for dashboard"""
        all_countries = [
            {"code": "US", "name": "United States"},
            {"code": "GB", "name": "United Kingdom"},
            {"code": "CA", "name": "Canada"},
            {"code": "AU", "name": "Australia"},
            {"code": "DE", "name": "Germany"},
            {"code": "FR", "name": "France"},
            {"code": "IT", "name": "Italy"},
            {"code": "ES", "name": "Spain"},
            {"code": "BR", "name": "Brazil"},
            {"code": "MX", "name": "Mexico"},
            {"code": "JP", "name": "Japan"},
            {"code": "KR", "name": "South Korea"},
            {"code": "IN", "name": "India"},
            {"code": "NL", "name": "Netherlands"},
            {"code": "SE", "name": "Sweden"},
            {"code": "NO", "name": "Norway"},
            {"code": "DK", "name": "Denmark"},
            {"code": "FI", "name": "Finland"},
            {"code": "CH", "name": "Switzerland"},
            {"code": "AT", "name": "Austria"},
            {"code": "BE", "name": "Belgium"},
            {"code": "PT", "name": "Portugal"},
            {"code": "IE", "name": "Ireland"},
            {"code": "PL", "name": "Poland"},
            {"code": "CZ", "name": "Czech Republic"},
            {"code": "HU", "name": "Hungary"},
            {"code": "RO", "name": "Romania"},
            {"code": "BG", "name": "Bulgaria"},
            {"code": "HR", "name": "Croatia"},
            {"code": "SI", "name": "Slovenia"},
            {"code": "SK", "name": "Slovakia"},
            {"code": "LT", "name": "Lithuania"},
            {"code": "LV", "name": "Latvia"},
            {"code": "EE", "name": "Estonia"},
            {"code": "GR", "name": "Greece"},
            {"code": "CY", "name": "Cyprus"},
            {"code": "MT", "name": "Malta"},
            {"code": "LU", "name": "Luxembourg"},
            {"code": "IS", "name": "Iceland"},
            {"code": "RU", "name": "Russia"},
            {"code": "UA", "name": "Ukraine"},
            {"code": "BY", "name": "Belarus"},
            {"code": "MD", "name": "Moldova"},
            {"code": "GE", "name": "Georgia"},
            {"code": "AM", "name": "Armenia"},
            {"code": "AZ", "name": "Azerbaijan"},
            {"code": "TR", "name": "Turkey"},
            {"code": "IL", "name": "Israel"},
            {"code": "SA", "name": "Saudi Arabia"},
            {"code": "AE", "name": "United Arab Emirates"},
            {"code": "QA", "name": "Qatar"},
            {"code": "KW", "name": "Kuwait"},
            {"code": "BH", "name": "Bahrain"},
            {"code": "OM", "name": "Oman"},
            {"code": "JO", "name": "Jordan"},
            {"code": "LB", "name": "Lebanon"},
            {"code": "SY", "name": "Syria"},
            {"code": "IQ", "name": "Iraq"},
            {"code": "IR", "name": "Iran"},
            {"code": "AF", "name": "Afghanistan"},
            {"code": "PK", "name": "Pakistan"},
            {"code": "BD", "name": "Bangladesh"},
            {"code": "LK", "name": "Sri Lanka"},
            {"code": "NP", "name": "Nepal"},
            {"code": "BT", "name": "Bhutan"},
            {"code": "MV", "name": "Maldives"},
            {"code": "MY", "name": "Malaysia"},
            {"code": "SG", "name": "Singapore"},
            {"code": "TH", "name": "Thailand"},
            {"code": "VN", "name": "Vietnam"},
            {"code": "PH", "name": "Philippines"},
            {"code": "ID", "name": "Indonesia"},
            {"code": "MM", "name": "Myanmar"},
            {"code": "LA", "name": "Laos"},
            {"code": "KH", "name": "Cambodia"},
            {"code": "BN", "name": "Brunei"},
            {"code": "TL", "name": "Timor-Leste"},
            {"code": "CN", "name": "China"},
            {"code": "TW", "name": "Taiwan"},
            {"code": "HK", "name": "Hong Kong"},
            {"code": "MO", "name": "Macau"},
            {"code": "MN", "name": "Mongolia"},
            {"code": "KP", "name": "North Korea"},
            {"code": "NZ", "name": "New Zealand"},
            {"code": "FJ", "name": "Fiji"},
            {"code": "PG", "name": "Papua New Guinea"},
            {"code": "SB", "name": "Solomon Islands"},
            {"code": "VU", "name": "Vanuatu"},
            {"code": "NC", "name": "New Caledonia"},
            {"code": "PF", "name": "French Polynesia"},
            {"code": "AR", "name": "Argentina"},
            {"code": "CL", "name": "Chile"},
            {"code": "PE", "name": "Peru"},
            {"code": "CO", "name": "Colombia"},
            {"code": "VE", "name": "Venezuela"},
            {"code": "EC", "name": "Ecuador"},
            {"code": "BO", "name": "Bolivia"},
            {"code": "PY", "name": "Paraguay"},
            {"code": "UY", "name": "Uruguay"},
            {"code": "GY", "name": "Guyana"},
            {"code": "SR", "name": "Suriname"},
            {"code": "GF", "name": "French Guiana"},
            {"code": "FK", "name": "Falkland Islands"},
            {"code": "ZA", "name": "South Africa"},
            {"code": "EG", "name": "Egypt"},
            {"code": "NG", "name": "Nigeria"},
            {"code": "KE", "name": "Kenya"},
            {"code": "GH", "name": "Ghana"},
            {"code": "ET", "name": "Ethiopia"},
            {"code": "TZ", "name": "Tanzania"},
            {"code": "UG", "name": "Uganda"},
            {"code": "DZ", "name": "Algeria"},
            {"code": "MA", "name": "Morocco"},
            {"code": "TN", "name": "Tunisia"},
            {"code": "LY", "name": "Libya"},
            {"code": "SD", "name": "Sudan"},
            {"code": "SS", "name": "South Sudan"},
            {"code": "CM", "name": "Cameroon"},
            {"code": "CI", "name": "Ivory Coast"},
            {"code": "BF", "name": "Burkina Faso"},
            {"code": "ML", "name": "Mali"},
            {"code": "NE", "name": "Niger"},
            {"code": "TD", "name": "Chad"},
            {"code": "CF", "name": "Central African Republic"},
            {"code": "CG", "name": "Republic of the Congo"},
            {"code": "CD", "name": "Democratic Republic of the Congo"},
            {"code": "GA", "name": "Gabon"},
            {"code": "GQ", "name": "Equatorial Guinea"},
            {"code": "ST", "name": "São Tomé and Príncipe"},
            {"code": "AO", "name": "Angola"},
            {"code": "ZM", "name": "Zambia"},
            {"code": "ZW", "name": "Zimbabwe"},
            {"code": "BW", "name": "Botswana"},
            {"code": "NA", "name": "Namibia"},
            {"code": "SZ", "name": "Eswatini"},
            {"code": "LS", "name": "Lesotho"},
            {"code": "MG", "name": "Madagascar"},
            {"code": "MU", "name": "Mauritius"},
            {"code": "SC", "name": "Seychelles"},
            {"code": "KM", "name": "Comoros"},
            {"code": "DJ", "name": "Djibouti"},
            {"code": "SO", "name": "Somalia"},
            {"code": "ER", "name": "Eritrea"},
            {"code": "RW", "name": "Rwanda"},
            {"code": "BI", "name": "Burundi"},
            {"code": "MW", "name": "Malawi"},
            {"code": "MZ", "name": "Mozambique"},
            {"code": "MG", "name": "Madagascar"},
            {"code": "RE", "name": "Réunion"},
            {"code": "YT", "name": "Mayotte"},
            {"code": "CV", "name": "Cape Verde"},
            {"code": "GM", "name": "Gambia"},
            {"code": "GN", "name": "Guinea"},
            {"code": "GW", "name": "Guinea-Bissau"},
            {"code": "SL", "name": "Sierra Leone"},
            {"code": "LR", "name": "Liberia"},
            {"code": "TG", "name": "Togo"},
            {"code": "BJ", "name": "Benin"},
            {"code": "SN", "name": "Senegal"},
            {"code": "MR", "name": "Mauritania"},
            {"code": "EH", "name": "Western Sahara"},
            {"code": "SH", "name": "Saint Helena"},
            {"code": "AC", "name": "Ascension Island"},
            {"code": "TA", "name": "Tristan da Cunha"}
        ]
        return all_countries

# Global rankings API instance
rankings_api = PlaylistRankingsAPI()

def calculate_monthly_growth(followers):
    """Calculate estimated monthly follower growth - DISABLED"""
    # Return None to disable fictional growth data
    return None

def format_playlist_for_frontend(playlist):
    """Safely format a playlist for frontend display"""
    if not playlist or not playlist.get('id'):
        return None
    
    try:
        # Get followers count if available
        followers = playlist.get('followers', {}).get('total', 0) if playlist.get('followers') else 0
        
        # Monthly growth calculation disabled
        
        # Get description for potential keywords
        description = playlist.get('description', '')
        
        # Extract potential keywords from description (simple approach)
        keywords = []
        if description:
            # Common music-related keywords to look for
            music_keywords = ['pop', 'rock', 'hip hop', 'jazz', 'classical', 'electronic', 'country', 'r&b', 'reggae', 'blues', 'folk', 'indie', 'alternative', 'metal', 'punk', 'soul', 'funk', 'disco', 'house', 'techno', 'trance', 'ambient', 'chill', 'lofi', 'workout', 'party', 'romantic', 'sad', 'happy', 'energetic', 'relaxing']
            description_lower = description.lower()
            for keyword in music_keywords:
                if keyword in description_lower:
                    keywords.append(keyword)
        
        return {
            'id': playlist.get('id', ''),
            'name': playlist.get('name', 'Unknown Playlist'),
            'creator': playlist.get('owner', {}).get('display_name', 'Unknown'),
            'tracks': playlist.get('tracks', {}).get('total', 0),
            'followers': followers,
            'description': description,
            'keywords': keywords,
            'public': playlist.get('public', False),
            'image': playlist.get('images', [{}])[0].get('url') if playlist.get('images') else None,
            'url': playlist.get('external_urls', {}).get('spotify', '')
        }
    except Exception as e:
        print(f"Error formatting playlist: {e}")
        return None

@app.route('/')
def index():
    """Main page - redirect to login if not authenticated"""
    # Check if user is authenticated
    if generator.sp and generator.user_id:
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html')

@app.route('/login')
def login():
    """Initiate Spotify OAuth login"""
    try:
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        redirect_uri = os.getenv('REDIRECT_URI')
        
        # Debug: Print what we found
        print(f"🔍 Found CLIENT_ID: {client_id is not None}")
        print(f"🔍 Found CLIENT_SECRET: {client_secret is not None}")
        print(f"🔍 Found REDIRECT_URI: {redirect_uri}")
        
        if not all([client_id, client_secret, redirect_uri]):
            print(f"❌ Missing credentials: client_id={bool(client_id)}, client_secret={bool(client_secret)}, redirect_uri={bool(redirect_uri)}")
            return jsonify({'error': 'Spotify credentials not configured'}), 500
        
        # Try to authenticate user
        if generator.authenticate_user(client_id, client_secret, redirect_uri):
            # Store user info in session
            user_info = generator.sp.current_user()
            session['user_id'] = user_info['id']
            session['user_name'] = user_info['display_name']
            return redirect(url_for('dashboard'))
        
        # If not authenticated, get auth URL
        auth_url = generator.get_auth_url()
        if auth_url:
            return redirect(auth_url)
        else:
            return redirect(url_for('index', error='Failed to get authentication URL'))
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/callback')
def callback():
    """Handle Spotify OAuth callback"""
    try:
        code = request.args.get('code')
        if code:
            if generator.handle_callback(code):
                # Store user info in session
                user_info = generator.sp.current_user()
                session['user_id'] = user_info['id']
                session['user_name'] = user_info['display_name']
                return redirect(url_for('dashboard'))
            else:
                return jsonify({'error': 'Authentication failed'}), 500
        else:
            return jsonify({'error': 'No authorization code received'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    """Logout user"""
    try:
        # Clear cached token
        if generator.auth_manager:
            generator.auth_manager.cache_handler.save_token_to_cache(None)
        generator.sp = None
        generator.user_id = None
        
        # Clear session data
        session.clear()
        
        return redirect(url_for('dashboard'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    """Dashboard page - require authentication"""
    if not generator.sp or not generator.user_id:
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/generator')
def generator_page():
    """Playlist generator page - require authentication"""
    if not generator.sp or not generator.user_id:
        return redirect(url_for('index'))
    return render_template('generator.html')

@app.route('/search', methods=['POST'])
def search_playlists():
    """Search for playlists with country filtering"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        country = data.get('country', '').strip()
        
        if not query:
            return jsonify({'error': 'Please enter a search term'}), 400
        
        # Use client credentials for public searches
        if not generator.sp:
            client_id = os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            
            if not all([client_id, client_secret]):
                return jsonify({'error': 'Spotify credentials not configured'}), 500
            
            generator.authenticate_client(client_id, client_secret)
        
        # Try PlaylistRankings API first if we have a country
        playlists_found = False
        if country and rankings_api.api_key and rankings_api.api_key != 'your_api_key_here':
            try:
                print(f"Trying PlaylistRankings API for '{query}' in '{country}'")
                import time
                time.sleep(1)  # Add delay to prevent rate limiting
                rankings = rankings_api.get_keyword_rankings(query)
                print(f"PlaylistRankings response: {len(rankings) if rankings else 0} countries")
                if rankings and country in rankings:
                    print(f"Found {len(rankings[country])} playlists for {country}")
                    country_playlists = rankings[country]
                    formatted_playlists = []
                    
                    for ranking in country_playlists[:50]:  # Get top 50 playlists from PlaylistRankings
                        if ranking and 'playlist' in ranking:
                            playlist_data = ranking['playlist']
                            position = ranking.get('position', 0)
                            
                            # Get detailed playlist info from Spotify
                            try:
                                detailed_playlist = generator.sp.playlist(playlist_data['id'])
                                formatted_playlist = format_playlist_for_frontend(detailed_playlist)
                                
                                if formatted_playlist:
                                    formatted_playlist['position'] = position
                                    formatted_playlist['country'] = country
                                    formatted_playlist['keyword'] = query
                                    formatted_playlists.append(formatted_playlist)
                            except Exception as e:
                                print(f"Error getting detailed playlist info for {playlist_data['id']}: {e}")
                                # Skip invalid playlists instead of adding basic info
                                continue
                    
                    if formatted_playlists:
                        # Keep original PlaylistRankings order, just filter out invalid playlists
                        formatted_playlists = [p for p in formatted_playlists if p.get('followers', 0) > 0]
                        formatted_playlists = formatted_playlists[:20]  # Limit to top 20
                        if formatted_playlists:  # Only return if we have valid playlists
                            playlists_found = True
                            return jsonify({'playlists': formatted_playlists})
                        
            except Exception as e:
                print(f"PlaylistRankings API failed for {country}, using Spotify fallback: {e}")
        
                # If PlaylistRankings has no data for this country, return empty results
        if not playlists_found:
            print(f"PlaylistRankings has no data for '{query}' in '{country}', returning empty results")
            return jsonify({'playlists': []})
        
    except Exception as e:
        print(f"Spotify search failed: {e}")
        return jsonify({'playlists': [], 'error': 'Search failed, please try again'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recommendations', methods=['POST'])
def get_recommendations():
    """Get playlist recommendations"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({'playlists': []})
        
        # Use client credentials for public searches
        if not generator.sp:
            client_id = os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            
            if not all([client_id, client_secret]):
                return jsonify({'error': 'Spotify credentials not configured'}), 500
            
            generator.authenticate_client(client_id, client_secret)
        
        # Get recommendations
        playlists = generator.sp.search(q=f'"{query}"', type='playlist', limit=8)
        
        # Format playlists for frontend
        formatted_playlists = []
        if 'playlists' in playlists and playlists['playlists']['items']:
            for playlist in playlists['playlists']['items']:
                formatted_playlist = format_playlist_for_frontend(playlist)
                if formatted_playlist:
                    formatted_playlists.append(formatted_playlist)
        
        return jsonify({'playlists': formatted_playlists})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/popular', methods=['POST'])
def get_popular_playlists():
    """Get popular playlists by genre"""
    try:
        data = request.get_json()
        genre = data.get('genre', '').strip()
        
        if not genre:
            return jsonify({'error': 'Please enter a genre'}), 400
        
        # Use client credentials for public searches
        if not generator.sp:
            client_id = os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            
            if not all([client_id, client_secret]):
                return jsonify({'error': 'Spotify credentials not configured'}), 500
            
            generator.authenticate_client(client_id, client_secret)
        
        # Get popular playlists by genre
        playlists = generator.sp.search(q=genre, type='playlist', limit=20)
        
        # Format playlists for frontend
        formatted_playlists = []
        if 'playlists' in playlists and playlists['playlists']['items']:
            for playlist in playlists['playlists']['items']:
                formatted_playlist = format_playlist_for_frontend(playlist)
                if formatted_playlist:
                    formatted_playlists.append(formatted_playlist)
        
        return jsonify({'playlists': formatted_playlists})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/featured', methods=['GET'])
def get_featured_playlists():
    """Get featured playlists for dashboard"""
    try:
        # Use client credentials for public searches
        if not generator.sp:
            client_id = os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            
            if not all([client_id, client_secret]):
                return jsonify({'error': 'Spotify credentials not configured'}), 500
            
            generator.authenticate_client(client_id, client_secret)
        
        # Try to get featured playlists
        try:
            playlists = generator.sp.search(q="popular", type='playlist', limit=12)
        except Exception as e:
            print(f"Error getting featured playlists: {e}")
            # Fallback: search for popular playlists
            playlists = generator.sp.search(q="popular", type='playlist', limit=12)
        
        # Format playlists for frontend
        formatted_playlists = []
        if 'playlists' in playlists and playlists['playlists']['items']:
            for playlist in playlists['playlists']['items']:
                formatted_playlist = format_playlist_for_frontend(playlist)
                if formatted_playlist:
                    formatted_playlists.append(formatted_playlist)
        
        return jsonify({'playlists': formatted_playlists})
        
    except Exception as e:
        print(f"Error in featured playlists endpoint: {e}")
        # Return empty list instead of error
        return jsonify({'playlists': []})

@app.route('/rankings/keyword/<keyword>', methods=['GET'])
def get_keyword_rankings(keyword):
    """Get rankings for a specific keyword"""
    try:
        rankings = rankings_api.get_keyword_rankings(keyword)
        
        # Format the data for frontend
        formatted_rankings = []
        for country, playlists in rankings.items():
            for playlist_data in playlists:
                playlist = playlist_data.get('playlist', {})
                if playlist and playlist.get('id'):
                    formatted_rankings.append({
                        'id': playlist.get('id'),
                        'name': playlist.get('name', 'Unknown Playlist'),
                        'position': playlist_data.get('position', 0),
                        'country': country,
                        'keyword': keyword
                    })
        
        return jsonify({'rankings': formatted_rankings})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/rankings/playlist/<spotify_id>', methods=['GET'])
def get_playlist_rankings(spotify_id):
    """Get rankings for a specific playlist"""
    try:
        rankings = rankings_api.get_playlist_rankings(spotify_id)
        return jsonify({'rankings': rankings})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/rankings/popular', methods=['GET'])
def get_popular_rankings():
    """Get popular playlists from rankings"""
    try:
        popular_keywords = rankings_api.get_popular_keywords()
        all_rankings = []
        
        # Get top playlists for popular keywords
        import time
        for i, keyword in enumerate(popular_keywords[:5]):  # Limit to 5 keywords to avoid too many API calls
            # Add delay between API calls to avoid rate limiting
            if i > 0:
                time.sleep(1)  # 1 second delay between calls
            rankings = rankings_api.get_keyword_rankings(keyword)
            
            if rankings:  # Only process if we got valid rankings
                for country, playlists in rankings.items():
                    for playlist_data in playlists[:3]:  # Top 3 playlists per country
                        playlist = playlist_data.get('playlist', {})
                        if playlist and playlist.get('id'):
                            all_rankings.append({
                                'id': playlist.get('id'),
                                'name': playlist.get('name', 'Unknown Playlist'),
                                'position': playlist_data.get('position', 0),
                                'country': country,
                                'keyword': keyword
                            })
        
        # Sort by position and remove duplicates
        unique_rankings = {}
        for ranking in all_rankings:
            playlist_id = ranking['id']
            if playlist_id not in unique_rankings or ranking['position'] < unique_rankings[playlist_id]['position']:
                unique_rankings[playlist_id] = ranking
        
        # Return top 12 playlists
        top_rankings = sorted(unique_rankings.values(), key=lambda x: x['position'])[:12]
        
        if top_rankings:
            return jsonify({'rankings': top_rankings})
        else:
            # If no rankings data, return empty to trigger fallback
            return jsonify({'rankings': []})
        
    except Exception as e:
        print(f"Error in get_popular_rankings: {e}")
        return jsonify({'rankings': []})

@app.route('/rankings/country/<country_code>', methods=['GET'])
def get_country_rankings(country_code):
    """Get top playlists for a specific country using PlaylistRankings API with fallback"""
    try:
        popular_keywords = rankings_api.get_popular_keywords()
        country_rankings = []
        
        # Get country name for better search
        country_names = {
            'US': 'United States', 'GB': 'United Kingdom', 'CA': 'Canada', 'AU': 'Australia',
            'DE': 'Germany', 'FR': 'France', 'IT': 'Italy', 'ES': 'Spain', 'BR': 'Brazil',
            'MX': 'Mexico', 'JP': 'Japan', 'KR': 'South Korea', 'IN': 'India',
            'NL': 'Netherlands', 'SE': 'Sweden', 'NO': 'Norway', 'DK': 'Denmark', 'FI': 'Finland',
            'CH': 'Switzerland', 'AT': 'Austria', 'BE': 'Belgium', 'PT': 'Portugal', 'IE': 'Ireland',
            'PL': 'Poland', 'CZ': 'Czech Republic', 'HU': 'Hungary', 'RO': 'Romania', 'BG': 'Bulgaria',
            'HR': 'Croatia', 'SI': 'Slovenia', 'SK': 'Slovakia', 'LT': 'Lithuania', 'LV': 'Latvia',
            'EE': 'Estonia', 'GR': 'Greece', 'CY': 'Cyprus', 'MT': 'Malta', 'LU': 'Luxembourg',
            'IS': 'Iceland', 'RU': 'Russia', 'UA': 'Ukraine', 'BY': 'Belarus', 'MD': 'Moldova',
            'GE': 'Georgia', 'AM': 'Armenia', 'AZ': 'Azerbaijan', 'TR': 'Turkey', 'IL': 'Israel',
            'SA': 'Saudi Arabia', 'AE': 'United Arab Emirates', 'QA': 'Qatar', 'KW': 'Kuwait',
            'BH': 'Bahrain', 'OM': 'Oman', 'JO': 'Jordan', 'LB': 'Lebanon', 'SY': 'Syria',
            'IQ': 'Iraq', 'IR': 'Iran', 'AF': 'Afghanistan', 'PK': 'Pakistan', 'BD': 'Bangladesh',
            'LK': 'Sri Lanka', 'NP': 'Nepal', 'BT': 'Bhutan', 'MV': 'Maldives', 'MY': 'Malaysia',
            'SG': 'Singapore', 'TH': 'Thailand', 'VN': 'Vietnam', 'PH': 'Philippines', 'ID': 'Indonesia',
            'MM': 'Myanmar', 'LA': 'Laos', 'KH': 'Cambodia', 'BN': 'Brunei', 'TL': 'Timor-Leste',
            'CN': 'China', 'TW': 'Taiwan', 'HK': 'Hong Kong', 'MO': 'Macau', 'MN': 'Mongolia',
            'KP': 'North Korea', 'NZ': 'New Zealand', 'FJ': 'Fiji', 'PG': 'Papua New Guinea',
            'SB': 'Solomon Islands', 'VU': 'Vanuatu', 'NC': 'New Caledonia', 'PF': 'French Polynesia',
            'AR': 'Argentina', 'CL': 'Chile', 'PE': 'Peru', 'CO': 'Colombia', 'VE': 'Venezuela',
            'EC': 'Ecuador', 'BO': 'Bolivia', 'PY': 'Paraguay', 'UY': 'Uruguay', 'GY': 'Guyana',
            'SR': 'Suriname', 'GF': 'French Guiana', 'FK': 'Falkland Islands', 'ZA': 'South Africa',
            'EG': 'Egypt', 'NG': 'Nigeria', 'KE': 'Kenya', 'GH': 'Ghana', 'ET': 'Ethiopia',
            'TZ': 'Tanzania', 'UG': 'Uganda', 'DZ': 'Algeria', 'MA': 'Morocco', 'TN': 'Tunisia',
            'LY': 'Libya', 'SD': 'Sudan', 'SS': 'South Sudan', 'CM': 'Cameroon', 'CI': 'Ivory Coast',
            'BF': 'Burkina Faso', 'ML': 'Mali', 'NE': 'Niger', 'TD': 'Chad', 'CF': 'Central African Republic',
            'CG': 'Republic of the Congo', 'CD': 'Democratic Republic of the Congo', 'GA': 'Gabon',
            'GQ': 'Equatorial Guinea', 'ST': 'São Tomé and Príncipe', 'AO': 'Angola', 'ZM': 'Zambia',
            'ZW': 'Zimbabwe', 'BW': 'Botswana', 'NA': 'Namibia', 'SZ': 'Eswatini', 'LS': 'Lesotho',
            'MG': 'Madagascar', 'MU': 'Mauritius', 'SC': 'Seychelles', 'KM': 'Comoros', 'DJ': 'Djibouti',
            'SO': 'Somalia', 'ER': 'Eritrea', 'RW': 'Rwanda', 'BI': 'Burundi', 'MW': 'Malawi',
            'MZ': 'Mozambique', 'RE': 'Réunion', 'YT': 'Mayotte', 'CV': 'Cape Verde', 'GM': 'Gambia',
            'GN': 'Guinea', 'GW': 'Guinea-Bissau', 'SL': 'Sierra Leone', 'LR': 'Liberia', 'TG': 'Togo',
            'BJ': 'Benin', 'SN': 'Senegal', 'MR': 'Mauritania', 'EH': 'Western Sahara', 'SH': 'Saint Helena',
            'AC': 'Ascension Island', 'TA': 'Tristan da Cunha'
        }
        
        country_name = country_names.get(country_code, country_code)
        
                # Try PlaylistRankings API first (only if we have a valid API key)
        rankings_found = False
        if rankings_api.api_key and rankings_api.api_key != 'your_api_key_here':
            import time
            for i, keyword in enumerate(popular_keywords[:6]):  # Limit to 6 keywords
                # Add delay between API calls to avoid rate limiting
                if i > 0:
                    time.sleep(1)  # 1 second delay between calls
                try:
                    # Get rankings for this keyword from PlaylistRankings API
                    keyword_rankings = rankings_api.get_keyword_rankings(keyword)
                    
                    # Check if we have rankings for the specific country
                    if keyword_rankings and country_code in keyword_rankings:
                        rankings_found = True
                        country_playlists = keyword_rankings[country_code]
                        print(f"Found {len(country_playlists)} playlists for '{keyword}' in {country_code}")
                        
                        for ranking in country_playlists:
                            if ranking and 'playlist' in ranking and 'position' in ranking:
                                playlist_data = ranking['playlist']
                                position = ranking['position']
                                
                                # Get detailed playlist info from Spotify
                                try:
                                    if not generator.sp:
                                        client_id = os.getenv('SPOTIFY_CLIENT_ID')
                                        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
                                        if all([client_id, client_secret]):
                                            generator.authenticate_client(client_id, client_secret)
                                    
                                    if generator.sp:
                                        # Get detailed playlist info
                                        detailed_playlist = generator.sp.playlist(playlist_data['id'])
                                        formatted_playlist = format_playlist_for_frontend(detailed_playlist)
                                        
                                        if formatted_playlist:
                                            country_rankings.append({
                                                'id': playlist_data['id'],
                                                'name': playlist_data['name'],
                                                'position': position,
                                                'country': country_code,
                                                'keyword': keyword,
                                                'creator': formatted_playlist['creator'],
                                                'tracks': formatted_playlist['tracks'],
                                                'followers': formatted_playlist['followers'],

                                                'image': formatted_playlist['image'],
                                                'url': formatted_playlist['url'],
                                                'description': formatted_playlist['description'],
                                                'keywords': formatted_playlist['keywords']
                                            })
                                except Exception as e:
                                    print(f"Error getting detailed playlist info for {playlist_data['id']}: {e}")
                                    # Add basic info if detailed fetch fails
                                    country_rankings.append({
                                        'id': playlist_data['id'],
                                        'name': playlist_data['name'],
                                        'position': position,
                                        'country': country_code,
                                        'keyword': keyword,
                                        'creator': 'Unknown',
                                        'tracks': 0,
                                        'followers': 0,

                                        'image': None,
                                        'url': f"https://open.spotify.com/playlist/{playlist_data['id']}",
                                        'description': '',
                                        'keywords': [keyword]
                                    })
                    
                except Exception as e:
                    print(f"Error fetching rankings for keyword '{keyword}' in {country_code}: {e}")
                    continue
        
        # If PlaylistRankings API didn't work, use Spotify API fallback
        if not rankings_found:
            print(f"PlaylistRankings API failed for {country_code}, using Spotify fallback")
            
            # Authenticate if not already done
            if not generator.sp:
                client_id = os.getenv('SPOTIFY_CLIENT_ID')
                client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
                redirect_uri = os.getenv('REDIRECT_URI')
                generator.authenticate_user(client_id, client_secret, redirect_uri)
            
            # Search for popular playlists with country context
            for keyword in popular_keywords[:8]:  # Limit to 8 keywords
                try:
                    # Search for popular playlists in this genre/country
                    query = f"{keyword} popular {country_name}"
                    
                    # Use client credentials for public searches
                    if not generator.sp:
                        client_id = os.getenv('SPOTIFY_CLIENT_ID')
                        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
                        if all([client_id, client_secret]):
                            generator.authenticate_client(client_id, client_secret)
                    
                    if generator.sp:
                        playlists = generator.sp.search(q=query, type='playlist', limit=5)
                        
                        if 'playlists' in playlists and playlists['playlists']['items']:
                            for i, playlist in enumerate(playlists['playlists']['items']):
                                if playlist and playlist.get('id'):
                                    formatted_playlist = format_playlist_for_frontend(playlist)
                                    if formatted_playlist:
                                        country_rankings.append({
                                            'id': playlist.get('id'),
                                            'name': playlist.get('name', 'Unknown Playlist'),
                                            'position': i + 1,
                                            'country': country_code,
                                            'keyword': keyword,
                                            'creator': formatted_playlist['creator'],
                                            'tracks': formatted_playlist['tracks'],
                                            'followers': formatted_playlist['followers'],

                                            'image': formatted_playlist['image'],
                                            'url': formatted_playlist['url'],
                                            'description': formatted_playlist['description'],
                                            'keywords': formatted_playlist['keywords']
                                        })
                except Exception as e:
                    print(f"Error searching for {keyword} in {country_code}: {e}")
                    continue
        
        # Remove duplicates and sort by position
        unique_rankings = {}
        for ranking in country_rankings:
            playlist_id = ranking['id']
            if playlist_id not in unique_rankings or ranking['position'] < unique_rankings[playlist_id]['position']:
                unique_rankings[playlist_id] = ranking
        
        # Return top 15 playlists for the country
        top_rankings = sorted(unique_rankings.values(), key=lambda x: x['position'])[:15]
        
        return jsonify({'rankings': top_rankings})
        
    except Exception as e:
        print(f"Error in get_country_rankings: {e}")
        return jsonify({'rankings': []})

@app.route('/rankings/countries', methods=['GET'])
def get_popular_countries():
    """Get list of popular countries"""
    try:
        countries = rankings_api.get_popular_countries()
        return jsonify({'countries': countries})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate_playlists():
    """Generate mixed playlists"""
    try:
        data = request.get_json()
        selected_playlists = data.get('playlists', [])
        num_playlists = data.get('num_playlists', 3)
        tracks_per_playlist = data.get('tracks_per_playlist', 20)
        avoid_duplicates = data.get('avoid_duplicates', True)
        playlist_names = data.get('playlist_names', [])
        playlist_description = data.get('playlist_description', '').strip()
        
        if not selected_playlists:
            return jsonify({'error': 'Please select at least one playlist'}), 400
        
        # Check if user is authenticated
        if not generator.sp or not generator.user_id:
            return jsonify({'error': 'Please login to your Spotify account first. Go to /login to authenticate.'}), 401
        
        # Collect all tracks from selected playlists
        all_tracks = []
        for playlist in selected_playlists:
            try:
                playlist_id = playlist.get('id')
                if playlist_id:
                    tracks = generator.get_playlist_tracks_detailed(playlist_id)
                    all_tracks.extend(tracks)
                    print(f"Fetched {len(tracks)} tracks from playlist: {playlist.get('name', 'Unknown')}")
            except Exception as e:
                print(f"Error fetching tracks from playlist {playlist.get('name', 'Unknown')}: {e}")
                continue
        
        if not all_tracks:
            return jsonify({'error': 'No tracks found in selected playlists'}), 400
        
        print(f"Total tracks collected: {len(all_tracks)}")
        
        # Generate playlists
        created_playlists = []
        for i in range(num_playlists):
            # Shuffle all tracks and select the required number
            random.shuffle(all_tracks)
            selected_tracks = all_tracks[:tracks_per_playlist]
            
            # Use custom name or generate one
            if i < len(playlist_names) and playlist_names[i]:
                final_playlist_name = playlist_names[i]
            else:
                final_playlist_name = generator.generate_playlist_name(selected_playlists)
                if num_playlists > 1:
                    final_playlist_name = f"{final_playlist_name} #{i+1}"
            
            # Use custom description or generate one
            if playlist_description:
                final_description = playlist_description
            else:
                final_description = f"Auto-generated mix created on {time.strftime('%Y-%m-%d %H:%M:%S')}"
            
            print(f"Creating playlist: {final_playlist_name} with {len(selected_tracks)} tracks")
            
            # Create the playlist
            playlist = generator.create_playlist_for_user(
                final_playlist_name,
                final_description,
                selected_tracks,
                is_public=os.getenv('PUBLIC', 'false').lower() == 'true'
            )
            
            if playlist:
                created_playlists.append(playlist)
                print(f"✅ Successfully created playlist: {playlist.get('name')}")
            else:
                print(f"❌ Failed to create playlist: {final_playlist_name}")
        
        # Format results for frontend
        results = []
        for playlist in created_playlists:
            if playlist:
                try:
                    results.append({
                        'name': playlist.get('name', 'Unknown Playlist'),
                        'tracks': playlist.get('tracks', {}).get('total', 0),
                        'url': playlist.get('external_urls', {}).get('spotify', ''),
                        'image': playlist.get('images', [{}])[0].get('url') if playlist.get('images') else None
                    })
                except Exception as e:
                    print(f"Error formatting created playlist: {e}")
                    continue
        
        return jsonify({'playlists': results})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/playlist/<playlist_id>/tracks', methods=['GET'])
def get_playlist_tracks(playlist_id):
    """Get detailed tracks from a playlist"""
    try:
        # Authenticate if not already done
        if not generator.sp:
            client_id = os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            redirect_uri = os.getenv('REDIRECT_URI')
            
            if not all([client_id, client_secret, redirect_uri]):
                return jsonify({'error': 'Spotify credentials not configured'}), 500
            
            generator.authenticate_user(client_id, client_secret, redirect_uri)
        
        tracks = generator.get_playlist_tracks_detailed(playlist_id)
        return jsonify({'tracks': tracks})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recommendations', methods=['POST'])
def get_track_recommendations():
    """Get Spotify recommendations based on seed tracks"""
    try:
        data = request.get_json()
        seed_tracks = data.get('tracks', [])
        
        if not seed_tracks:
            return jsonify({'error': 'Please provide seed tracks'}), 400
        
        # Authenticate if not already done
        if not generator.sp:
            client_id = os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            redirect_uri = os.getenv('REDIRECT_URI')
            
            if not all([client_id, client_secret, redirect_uri]):
                return jsonify({'error': 'Spotify credentials not configured'}), 500
            
            generator.authenticate_user(client_id, client_secret, redirect_uri)
        
        recommendations = generator.get_recommendations(seed_tracks)
        
        # Format recommendations for frontend
        formatted_recommendations = []
        for track in recommendations:
            formatted_recommendations.append({
                'id': track['id'],
                'name': track['name'],
                'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                'album': track['album']['name'],
                'duration_ms': track['duration_ms'],
                'popularity': track['popularity'],
                'uri': track['uri'],
                'image': track['album']['images'][0]['url'] if track['album']['images'] else None
            })
        
        return jsonify({'recommendations': formatted_recommendations})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/user/playlists', methods=['GET'])
def get_user_playlists():
    """Get user's playlists"""
    try:
        # Authenticate if not already done
        if not generator.sp:
            client_id = os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            redirect_uri = os.getenv('REDIRECT_URI')
            
            if not all([client_id, client_secret, redirect_uri]):
                return jsonify({'error': 'Spotify credentials not configured'}), 500
            
            generator.authenticate_user(client_id, client_secret, redirect_uri)
        
        playlists = generator.get_user_playlists()
        
        # Format playlists for frontend
        formatted_playlists = []
        for playlist in playlists:
            formatted_playlist = format_playlist_for_frontend(playlist)
            if formatted_playlist:
                formatted_playlists.append(formatted_playlist)
        
        return jsonify({'playlists': formatted_playlists})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/status', methods=['GET'])
def get_auth_status():
    """Get authentication status"""
    try:
        is_authenticated = generator.sp is not None and generator.user_id is not None
        return jsonify({
            'authenticated': is_authenticated,
            'user_id': generator.user_id if is_authenticated else None,
            'user_name': session.get('user_name') if is_authenticated else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 3000))
    app.run(debug=True, host='0.0.0.0', port=port)
