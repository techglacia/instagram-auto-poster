import os
import json
import time
import requests
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# --- Configuration ---
SERVICE_ACCOUNT_FILE = "service_account.json"
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", "1GpQI3AlCV1j6an2ahynEOs7F79Dp3nUv")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID")

# --- Constants ---
INSTAGRAM_API_VERSION = "v18.0"
MAX_STATUS_CHECKS = 10
STATUS_CHECK_INTERVAL = 15  # Seconds

# --- Initialize Google Drive Service ---
def init_gdrive_service():
    """Initialize Google Drive API service"""
    try:
        # Load credentials from environment
        gdrive_creds = os.getenv("GDRIVE_CREDENTIALS")
        if not gdrive_creds:
            raise ValueError("GDRIVE_CREDENTIALS environment variable missing")

        # Save credentials to file
        creds_data = json.loads(gdrive_creds)
        with open(SERVICE_ACCOUNT_FILE, "w") as f:
            json.dump(creds_data, f)

        # Authenticate
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        print(f"🚨 Google Drive initialization failed: {e}")
        exit(1)

# --- Reel Management ---
def get_next_reel(drive_service):
    """Get the oldest reel from Google Drive folder"""
    try:
        result = drive_service.files().list(
            q=f"'{GDRIVE_FOLDER_ID}' in parents and mimeType='video/mp4'",
            fields="files(id, name, createdTime)",
            orderBy="createdTime",
            pageSize=1,
            supportsAllDrives=True
        ).execute()

        if not result.get("files"):
            print("ℹ️ No reels found in Google Drive folder")
            return None, None

        reel = result["files"][0]
        return (
            f"https://drive.google.com/uc?export=download&id={reel['id']}",
            reel["id"]
        )
    except Exception as e:
        print(f"🚨 Error fetching reels: {e}")
        return None, None

def delete_reel(drive_service, file_id):
    """Delete reel from Google Drive"""
    try:
        drive_service.files().delete(
            fileId=file_id,
            supportsAllDrives=True
        ).execute()
        print("✅ Reel deleted from Google Drive")
    except Exception as e:
        print(f"⚠️ Failed to delete reel: {e}")

# --- Instagram Integration ---
def check_container_status(container_id):
    """Check status of Instagram media container"""
    url = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}/{container_id}"
    params = {
        "fields": "status_code",
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    
    for _ in range(MAX_STATUS_CHECKS):
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return None
        
        data = response.json()
        if data.get("status_code") == "FINISHED":
            return True
        time.sleep(STATUS_CHECK_INTERVAL)
    
    return False

def upload_reel_container(video_url, caption):
    """Create Instagram media container"""
    url = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}/{INSTAGRAM_USER_ID}/media"
    params = {
        "video_url": video_url,
        "caption": caption,
        "media_type": "REELS",
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    
    response = requests.post(url, params=params)
    if response.status_code != 200:
        print(f"📤 Upload failed: {response.text}")
        return None
    
    return response.json().get("id")

def publish_reel(container_id):
    """Publish the Instagram reel"""
    url = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}/{INSTAGRAM_USER_ID}/media_publish"
    params = {
        "creation_id": container_id,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    
    response = requests.post(url, params=params)
    if response.status_code == 200:
        return response.json().get("id")
    print(f"📡 Publish failed: {response.text}")
    return None

# --- Main Workflow ---
def main():
    # Validate environment variables
    if not all([INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_USER_ID]):
        print("🚨 Missing Instagram credentials in environment variables")
        exit(1)

    # Initialize services
    drive_service = init_gdrive_service()

    # Get next reel
    reel_url, reel_id = get_next_reel(drive_service)
    if not reel_url:
        print("ℹ️ No reels to process")
        return

    print(f"🎬 Processing reel: {reel_url}")

    # Upload to Instagram
    container_id = upload_reel_container(reel_url, "Daily Reel! #Automated")
    if not container_id:
        exit(1)

    # Check processing status
    if not check_container_status(container_id):
        print("🚨 Video processing timed out")
        exit(1)

    # Publish reel
    publication_id = publish_reel(container_id)
    if publication_id:
        print(f"✅ Successfully published reel ID: {publication_id}")
        delete_reel(drive_service, reel_id)
    else:
        print("🚨 Failed to publish reel")

if __name__ == "__main__":
    main()
