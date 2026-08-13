"""
Script to run locally to generate Google Drive OAuth 2.0 Refresh Token.
Requires: pip install google-auth-oauthlib
"""
import os
import sys
import glob
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# Full drive scope is needed to search, update and write files in the shared folder
SCOPES = ['https://www.googleapis.com/auth/drive']

def find_client_secrets():
    """Look for client secret JSON files in the current folder or Downloads."""
    # Search patterns
    paths = [
        'client_secrets.json',
        'client_secret_*.json',
        os.path.expanduser('~/Downloads/client_secret_*.json')
    ]
    
    found_files = []
    for path in paths:
        found_files.extend(glob.glob(path))
        
    if found_files:
        # Return the most recently created file matching the pattern
        return max(found_files, key=os.path.getctime)
    return None

def main():
    print("=" * 60)
    print("🔑 Google Drive OAuth 2.0 Token Generator")
    print("=" * 60)
    
    # Try to auto-detect client secret JSON file
    secret_file = find_client_secrets()
    client_config = None
    
    if secret_file:
        print(f"[INFO] Auto-detected client secret file: {secret_file}")
        try:
            with open(secret_file, 'r') as f:
                client_config = json.load(f)
            # Standard Google credentials format check
            if 'installed' not in client_config and 'web' not in client_config:
                print("[WARNING] File format is not standard Google client secrets. Falling back to manual input.")
                client_config = None
        except Exception as e:
            print(f"[WARNING] Failed to read {secret_file}: {e}. Falling back to manual input.")
            client_config = None

    if not client_config:
        print("Please enter the OAuth Client ID credentials from GCP.")
        print("Or click 'Download JSON' in the GCP Console and place the file in your Downloads folder.\n")

        client_id = input("1. Enter Client ID: ").strip().replace('\n', '').replace('\r', '')
        if not client_id:
            print("[ERROR] Client ID cannot be empty.")
            sys.exit(1)

        client_secret = input("2. Enter Client Secret: ").strip().replace('\n', '').replace('\r', '')
        if not client_secret:
            print("[ERROR] Client Secret cannot be empty.")
            sys.exit(1)

        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

    try:
        # Extract client_id for printout later
        config_key = 'installed' if 'installed' in client_config else 'web'
        client_id = client_config[config_key]['client_id']
        client_secret = client_config[config_key]['client_secret']
        
        # Run local server to capture authorization code
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        print("\n[INFO] Opening your browser for authentication...")
        print("Note: If you get a 'Google hasn't verified this app' warning:")
        print("Click 'Advanced' -> 'Go to RouletVoc (unsafe)' to proceed.")
        
        creds = flow.run_local_server(port=0)
        
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! Copy these 3 values to your GitHub Secrets:")
        print("=" * 60)
        print(f"GOOGLE_DRIVE_CLIENT_ID:\n{client_id}\n")
        print(f"GOOGLE_DRIVE_CLIENT_SECRET:\n{client_secret}\n")
        print(f"GOOGLE_DRIVE_REFRESH_TOKEN:\n{creds.refresh_token}\n")
        print("=" * 60)
        print("Also ensure GOOGLE_DRIVE_FOLDER_ID is set to your target folder ID.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Authentication failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
