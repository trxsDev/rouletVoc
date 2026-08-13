"""
Upload built RouletVoc installer (.exe) to Google Drive.

Uses Google Drive OAuth 2.0 User Credentials (via Refresh Token).
Required environment variables:
  - GOOGLE_DRIVE_CLIENT_ID: OAuth Client ID
  - GOOGLE_DRIVE_CLIENT_SECRET: OAuth Client Secret
  - GOOGLE_DRIVE_REFRESH_TOKEN: OAuth Refresh Token
  - GOOGLE_DRIVE_FOLDER_ID: Target Google Drive folder ID

Behavior:
  - If a file with the same name already exists in the folder → updates it (no duplicates)
  - If it's a new file → creates it in the target folder
  - Prints the shareable Drive link in CI logs
"""

import os
import sys
import glob

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def get_installer_path():
    """Find the built installer .exe in the dist/ directory."""
    dist_dir = os.path.join(os.getcwd(), 'dist')

    # Look for Inno Setup output: *_Setup_*.exe
    patterns = [
        os.path.join(dist_dir, '*_Setup_*.exe'),
        os.path.join(dist_dir, '*.exe'),
    ]

    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            # Return the largest .exe (the installer, not a small helper)
            return max(matches, key=os.path.getsize)

    return None


def authenticate():
    """Authenticate with Google Drive API using OAuth 2.0 User Credentials."""
    client_id = os.environ.get('GOOGLE_DRIVE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_DRIVE_CLIENT_SECRET')
    refresh_token = os.environ.get('GOOGLE_DRIVE_REFRESH_TOKEN')

    if not all([client_id, client_secret, refresh_token]):
        print('[ERROR] Missing OAuth environment variables (CLIENT_ID, CLIENT_SECRET, or REFRESH_TOKEN).')
        print('        Make sure they are configured as Repository Secrets in GitHub.')
        sys.exit(1)

    # Reconstruct credentials using Refresh Token
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )
    
    return build('drive', 'v3', credentials=creds)


def upload_to_drive(service, filepath, folder_id):
    """Upload or update a file in the specified Google Drive folder."""
    filename = os.path.basename(filepath)
    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)

    print(f'[FILE] {filename} ({file_size_mb:.1f} MB)')
    print(f'[FOLDER] Target folder ID: {folder_id}')

    # Check if a file with the same name already exists
    # supportsAllDrives=True is used to ensure compatibility
    query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    existing = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)',
        pageSize=1,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    media = MediaFileUpload(
        filepath,
        mimetype='application/octet-stream',
        resumable=True
    )

    if existing.get('files'):
        # Update existing file (keeps the same link, no duplicates)
        file_id = existing['files'][0]['id']
        print(f'[UPDATE] Found existing file (ID: {file_id}), updating...')

        updated = service.files().update(
            fileId=file_id,
            media_body=media,
            fields='id, name, webViewLink',
            supportsAllDrives=True
        ).execute()

        print(f'[OK] Updated successfully: {updated.get("name")}')
        file_id = updated['id']
    else:
        # Create new file
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }

        created = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink',
            supportsAllDrives=True
        ).execute()

        print(f'[OK] Uploaded successfully: {created.get("name")}')
        file_id = created['id']

    # Print the shareable link
    view_link = f'https://drive.google.com/file/d/{file_id}/view'
    print('')
    print('[LINK] Google Drive link:')
    print(f'       {view_link}')
    print('')

    return file_id


def main():
    print('=' * 60)
    print('RouletVoc -- Google Drive Auto-Upload (OAuth 2.0)')
    print('=' * 60)

    # 1. Validate environment
    folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
    if not folder_id:
        print('[ERROR] GOOGLE_DRIVE_FOLDER_ID environment variable is not set.')
        print('        Add it as a GitHub Secret with your Drive folder ID.')
        sys.exit(1)

    # 2. Find the installer
    installer_path = get_installer_path()
    if not installer_path:
        print('[ERROR] No installer .exe found in dist/ directory.')
        print('        Make sure PyInstaller and Inno Setup ran successfully.')
        sys.exit(1)

    print(f'[INFO] Found installer: {installer_path}')

    # 3. Authenticate
    service = authenticate()
    print('[OK] Authenticated with Google Drive API')

    # 4. Upload
    upload_to_drive(service, installer_path, folder_id)

    print('=' * 60)
    print('[DONE] Installer is now available on Google Drive.')
    print('=' * 60)


if __name__ == '__main__':
    main()
