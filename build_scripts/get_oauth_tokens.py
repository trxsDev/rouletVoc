"""
Script to run locally to generate Google Drive OAuth 2.0 Refresh Token.
Requires: pip install google-auth-oauthlib
"""
import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

# Full drive scope is needed to search, update and write files in the shared folder
SCOPES = ['https://www.googleapis.com/auth/drive']

def main():
    print("=" * 60)
    print("🔑 Google Drive OAuth 2.0 Token Generator")
    print("=" * 60)
    print("Please enter the OAuth Client ID credentials from GCP.")
    print("If you haven't created them, go to Google Cloud Console:")
    print("APIs & Services -> Credentials -> Create Credentials -> OAuth client ID (Desktop App)\n")

    client_id = input("1. Enter Client ID: ").strip()
    if not client_id:
        print("[ERROR] Client ID cannot be empty.")
        sys.exit(1)

    client_secret = input("2. Enter Client Secret: ").strip()
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
        # Run local server to capture authorization code
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        print("\n[INFO] Opening your browser for authentication...")
        print("Note: If you get a 'Google hasn't verified this app' warning:")
        print("Click 'Advanced' -> 'Go to RouletVoc Uploader (unsafe)' to proceed.")
        
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
