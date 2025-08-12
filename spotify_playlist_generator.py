#!/usr/bin/env python3
"""
Spotify Playlist Generator
A tool to combine multiple playlists and generate new mixed playlists.
"""

import os
import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.text import Text
from tabulate import tabulate
import time

# Load environment variables
load_dotenv('.env')

console = Console()

class SpotifyPlaylistGenerator:
    def __init__(self):
        self.sp = None
        self.user_id = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Spotify API"""
        try:
            scope = "playlist-read-private playlist-modify-public playlist-modify-private user-library-read"
            
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=os.getenv('SPOTIFY_CLIENT_ID'),
                client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
                redirect_uri=os.getenv('REDIRECT_URI'),
                scope=scope
            ))
            
            # Get user info
            user_info = self.sp.current_user()
            self.user_id = user_info['id']
            
            console.print(f"✅ Successfully authenticated as: [bold green]{user_info['display_name']}[/bold green]")
            
        except Exception as e:
            console.print(f"❌ Authentication failed: {str(e)}", style="bold red")
            console.print("Please check your SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env")
            console.print("Also ensure your redirect URI in Spotify Developer Dashboard matches: http://127.0.0.1:3000/callback")
            exit(1)
    
    def search_playlists(self, query, limit=20):
        """Search for playlists on Spotify"""
        try:
            results = self.sp.search(q=query, type='playlist', limit=limit)
            return results['playlists']['items']
        except Exception as e:
            console.print(f"❌ Error searching playlists: {str(e)}", style="bold red")
            return []
    
    def get_user_playlists(self):
        """Get all user playlists"""
        playlists = []
        offset = 0
        limit = 50
        
        while True:
            results = self.sp.current_user_playlists(limit=limit, offset=offset)
            playlists.extend(results['items'])
            
            if len(results['items']) < limit:
                break
            offset += limit
        
        return playlists
    
    def display_playlists(self, playlists, title="Playlists"):
        """Display playlists in a nice table"""
        table = Table(title=title)
        table.add_column("Index", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("Creator", style="blue")
        table.add_column("Tracks", style="green")
        table.add_column("Public", style="yellow")
        
        for i, playlist in enumerate(playlists, 1):
            creator = playlist['owner']['display_name'] if 'owner' in playlist else "Unknown"
            table.add_row(
                str(i),
                playlist['name'][:40] + "..." if len(playlist['name']) > 40 else playlist['name'],
                creator[:20] + "..." if len(creator) > 20 else creator,
                str(playlist['tracks']['total']),
                "Yes" if playlist['public'] else "No"
            )
        
        console.print(table)
    
    def get_playlist_tracks(self, playlist_id):
        """Get all tracks from a playlist"""
        tracks = []
        offset = 0
        limit = 100
        
        while True:
            results = self.sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
            tracks.extend(results['items'])
            
            if len(results['items']) < limit:
                break
            offset += limit
        
        return tracks
    
    def generate_playlist_name(self, source_playlists):
        """Generate a creative name for the new playlist"""
        names = [p['name'] for p in source_playlists]
        if len(names) == 1:
            return f"Mixed from {names[0]}"
        elif len(names) == 2:
            return f"{names[0]} + {names[1]} Mix"
        else:
            return f"Mixed from {len(names)} Playlists"
    
    def create_mixed_playlist(self, tracks, playlist_name, is_public=False):
        """Create a new playlist with the given tracks"""
        try:
            # Create the playlist
            playlist = self.sp.user_playlist_create(
                user=self.user_id,
                name=playlist_name,
                public=is_public,
                description=f"Auto-generated mix created on {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Add tracks to the playlist
            track_uris = [track['track']['uri'] for track in tracks if track['track']]
            
            # Spotify API has a limit of 100 tracks per request
            for i in range(0, len(track_uris), 100):
                batch = track_uris[i:i+100]
                self.sp.playlist_add_items(playlist['id'], batch)
            
            return playlist
            
        except Exception as e:
            console.print(f"❌ Error creating playlist: {str(e)}", style="bold red")
            return None
    
    def generate_mixed_playlists(self, selected_playlists, num_playlists, tracks_per_playlist, avoid_duplicates=True):
        """Generate multiple mixed playlists"""
        # Collect all tracks from selected playlists
        all_tracks = []
        for playlist in selected_playlists:
            console.print(f"📥 Loading tracks from: {playlist['name']}")
            tracks = self.get_playlist_tracks(playlist['id'])
            all_tracks.extend(tracks)
        
        console.print(f"📊 Total tracks collected: {len(all_tracks)}")
        
        # Remove duplicates if requested
        if avoid_duplicates:
            unique_tracks = {}
            for track in all_tracks:
                if track['track']:
                    track_id = track['track']['id']
                    if track_id not in unique_tracks:
                        unique_tracks[track_id] = track
            
            all_tracks = list(unique_tracks.values())
            console.print(f"📊 Unique tracks after deduplication: {len(all_tracks)}")
        
        if len(all_tracks) < tracks_per_playlist:
            console.print(f"⚠️  Warning: Only {len(all_tracks)} tracks available, but {tracks_per_playlist} requested per playlist", style="yellow")
            tracks_per_playlist = len(all_tracks)
        
        created_playlists = []
        
        for i in range(num_playlists):
            # Shuffle tracks and select the required number
            random.shuffle(all_tracks)
            selected_tracks = all_tracks[:tracks_per_playlist]
            
            # Generate playlist name
            playlist_name = f"{self.generate_playlist_name(selected_playlists)} #{i+1}"
            
            console.print(f"🎵 Creating playlist {i+1}/{num_playlists}: {playlist_name}")
            
            # Create the playlist
            playlist = self.create_mixed_playlist(
                selected_tracks, 
                playlist_name, 
                is_public=os.getenv('PUBLIC', 'false').lower() == 'true'
            )
            
            if playlist:
                created_playlists.append(playlist)
                console.print(f"✅ Created: {playlist['name']} ({len(selected_tracks)} tracks)")
            else:
                console.print(f"❌ Failed to create playlist {i+1}", style="bold red")
        
        return created_playlists

def main():
    """Main application function"""
    console.print(Panel.fit(
        "[bold blue]🎵 Spotify Playlist Generator[/bold blue]\n"
        "Search for playlists and create mixed playlists!",
        border_style="blue"
    ))
    
    # Initialize the generator
    generator = SpotifyPlaylistGenerator()
    
    selected_playlists = []
    
    while True:
        console.print("\n[bold]Step 1: Search for playlists[/bold]")
        console.print("Enter a search term to find playlists (e.g., 'workout', 'chill', 'party')")
        
        search_query = Prompt.ask("Search term")
        if not search_query.strip():
            console.print("❌ Please enter a search term.", style="red")
            continue
        
        console.print(f"\n🔍 Searching for playlists: '{search_query}'")
        playlists = generator.search_playlists(search_query, limit=20)
        
        if not playlists:
            console.print("❌ No playlists found for that search term.", style="red")
            continue
        
        # Display search results
        generator.display_playlists(playlists, f"Search Results for '{search_query}'")
        
        # Get user selections
        console.print("\n[bold]Select playlists to add to your mix[/bold]")
        console.print("Enter playlist numbers separated by commas (e.g., 1,3,5)")
        console.print("Or type 'search' to search again, or 'done' when finished")
        
        while True:
            try:
                selection = Prompt.ask("Playlist numbers")
                
                if selection.lower() == 'search':
                    break
                elif selection.lower() == 'done':
                    if not selected_playlists:
                        console.print("❌ Please select at least one playlist before proceeding.", style="red")
                        continue
                    else:
                        break
                
                selected_indices = [int(x.strip()) - 1 for x in selection.split(',')]
                
                # Validate selections
                if all(0 <= i < len(playlists) for i in selected_indices):
                    new_playlists = [playlists[i] for i in selected_indices]
                    
                    # Check for duplicates
                    for playlist in new_playlists:
                        if playlist not in selected_playlists:
                            selected_playlists.append(playlist)
                    
                    console.print(f"✅ Added {len(new_playlists)} playlists to your selection")
                    console.print(f"📋 Total playlists selected: {len(selected_playlists)}")
                    break
                else:
                    console.print("❌ Invalid playlist numbers. Please try again.", style="red")
            except ValueError:
                console.print("❌ Please enter valid numbers separated by commas, 'search', or 'done'.", style="red")
        
        if selection.lower() == 'done':
            break
    
    # Show final selection
    console.print(f"\n✅ Final selection: {len(selected_playlists)} playlists")
    generator.display_playlists(selected_playlists, "Selected Playlists")
    
    # Get generation parameters
    console.print("\n[bold]Step 2: Configure generation settings[/bold]")
    
    num_playlists = IntPrompt.ask(
        "How many new playlists to create?",
        default=3,
        show_default=True
    )
    
    tracks_per_playlist = IntPrompt.ask(
        "How many tracks per playlist?",
        default=20,
        show_default=True
    )
    
    avoid_duplicates = Confirm.ask(
        "Avoid duplicate tracks across new playlists?",
        default=True
    )
    
    # Confirm and generate
    console.print(f"\n[bold]Step 3: Generate playlists[/bold]")
    console.print(f"Creating {num_playlists} playlists with {tracks_per_playlist} tracks each...")
    
    if Confirm.ask("Proceed with generation?"):
        created_playlists = generator.generate_mixed_playlists(
            selected_playlists,
            num_playlists,
            tracks_per_playlist,
            avoid_duplicates
        )
        
        # Display results
        if created_playlists:
            console.print(f"\n🎉 Successfully created {len(created_playlists)} playlists!")
            
            table = Table(title="Created Playlists")
            table.add_column("Name", style="magenta")
            table.add_column("Tracks", style="green")
            table.add_column("URL", style="cyan")
            
            for playlist in created_playlists:
                table.add_row(
                    playlist['name'],
                    str(playlist['tracks']['total']),
                    playlist['external_urls']['spotify']
                )
            
            console.print(table)
        else:
            console.print("❌ No playlists were created.", style="bold red")
    else:
        console.print("❌ Generation cancelled.", style="yellow")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n❌ Operation cancelled by user.", style="yellow")
    except Exception as e:
        console.print(f"\n❌ An unexpected error occurred: {str(e)}", style="bold red")
        console.print("Please check your internet connection and try again.")
