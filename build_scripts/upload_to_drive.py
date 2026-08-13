"""
Upload built RouletVoc installer (.exe) to Google Drive.

Uses a Google Service Account for authentication.
Required environment variables:
  - GOOGLE_SERVICE_ACCOUNT_KEY: JSON string of the service account key
  - GOOGLE_DRIVE_FOLDER_ID: Target Google Drive folder ID

Behavior:
  - If a file with the same name already exists in the folder → updates it (no duplicates)
  - If it's a new file → creates it in the target folder
  - Prints the shareable Drive link in CI logs
"""

import os
import sys
import json
import glob

from google.oauth2 import service_account
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
    """Authenticate with Google Drive API using Service Account."""
    creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY')
    if not creds_json:
        print('[ERROR] GOOGLE_SERVICE_ACCOUNT_KEY environment variable is not set.')
        print('        Add it as a GitHub Secret with the JSON key file contents.')
        sys.exit(1)

    try:
        creds_info = json.loads(creds_json)
    except json.JSONDecodeError as e:
        print(f'[ERROR] Failed to parse GOOGLE_SERVICE_ACCOUNT_KEY as JSON: {e}')
        sys.exit(1)

    creds = service_account.Credentials.from_service_account_info(
        creds_info,
        scopes=['https://www.googleapis.com/auth/drive.file']
    )
    return build('drive', 'v3', credentials=creds)


def upload_to_drive(service, filepath, folder_id):
    """Upload or update a file in the specified Google Drive folder."""
    filename = os.path.basename(filepath)
    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)

    print(f'[FILE] {filename} ({file_size_mb:.1f} MB)')
    print(f'[FOLDER] Target folder ID: {folder_id}')

    # Check if a file with the same name already exists
    query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    existing = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)',
        pageSize=1
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
            fields='id, name, webViewLink'
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
            fields='id, name, webViewLink'
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
    print('RouletVoc -- Google Drive Auto-Upload')
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
