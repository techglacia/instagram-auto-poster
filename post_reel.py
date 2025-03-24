import os
import json
import time
import requests
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# ===== CONFIGURATION =====
SERVICE_ACCOUNT_FILE = "service_account.json"
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID")

# ===== VALIDATION =====
def validate_environment():
    """Validate all required environment variables"""
    required_vars = {
        "INSTAGRAM_ACCESS_TOKEN": INSTAGRAM_ACCESS_TOKEN,
        "INSTAGRAM_USER_ID": INSTAGRAM_USER_ID,
        "GDRIVE_CREDENTIALS": os.getenv("GDRIVE_CREDENTIALS"),
        "GDRIVE_FOLDER_ID": GDRIVE_FOLDER_ID
    }
    
    missing = [name for name, value in required_vars.items() if not value]
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        exit(1)

validate_environment()

# ===== GOOGLE DRIVE SETUP =====
try:
    with open(SERVICE_ACCOUNT_FILE, "w") as f:
        json.dump(json.loads(os.getenv("GDRIVE_CREDENTIALS")), f)
    
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    drive_service = build("drive", "v3", credentials=creds)
    print("✅ Google Drive authenticated")
except Exception as e:
    print(f"❌ Google Drive setup failed: {str(e)}")
    exit(1)

# ===== REEL HANDLING =====
def get_next_reel():
    """Get oldest reel from Google Drive folder"""
    try:
        results = drive_service.files().list(
            q=f"'{GDRIVE_FOLDER_ID}' in parents and mimeType='video/mp4'",
            fields="files(id, name)",
            orderBy="createdTime",
            pageSize=1,
            supportsAllDrives=True
        ).execute()
        
        if not results.get("files"):
            print("ℹ️ No reels found in folder")
            return None, None
            
        reel = results["files"][0]
        reel_url = f"https://drive.google.com/uc?export=download&id={reel['id']}"
        print(f"🎬 Found reel: {reel['name']}")
        return reel_url, reel["id"]
    except Exception as e:
        print(f"❌ Failed to get reel: {str(e)}")
        return None, None

def delete_reel(file_id):
    """Delete reel after posting"""
    try:
        drive_service.files().delete(
            fileId=file_id,
            supportsAllDrives=True
        ).execute()
        print("✅ Deleted reel from Google Drive")
    except Exception as e:
        print(f"⚠️ Failed to delete reel: {str(e)}")

# ===== INSTAGRAM UPLOAD =====
def upload_to_instagram(video_url):
    """Upload and publish reel to Instagram"""
    # Step 1: Create container
    try:
        create_url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_USER_ID}/media"
        params = {
            "video_url": video_url,
            "caption": "Check out this reel! #automated",
            "media_type": "REELS",
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        
        response = requests.post(create_url, params=params)
        if response.status_code != 200:
            print(f"❌ Container creation failed: {response.text}")
            return False
            
        container_id = response.json().get("id")
        if not container_id:
            print("❌ No container ID received")
            return False
        
        # Step 2: Check status
        status_url = f"https://graph.facebook.com/v18.0/{container_id}"
        for _ in range(10):  # Check up to 10 times
            time.sleep(15)
            status = requests.get(status_url, params={"fields": "status_code", "access_token": INSTAGRAM_ACCESS_TOKEN})
            if status.json().get("status_code") == "FINISHED":
                break
        else:
            print("❌ Video processing timed out")
            return False
        
        # Step 3: Publish
        publish_url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_USER_ID}/media_publish"
        publish_params = {
            "creation_id": container_id,
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        
        publish_response = requests.post(publish_url, params=publish_params)
        if publish_response.status_code == 200:
            print("✅ Reel published successfully!")
            return True
        else:
            print(f"❌ Publish failed: {publish_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Instagram upload failed: {str(e)}")
        return False

# ===== MAIN EXECUTION =====
if __name__ == "__main__":
    print("🚀 Starting reel posting process...")
    
    reel_url, reel_id = get_next_reel()
    if not reel_url:
        exit(0)
        
    if upload_to_instagram(reel_url):
        delete_reel(reel_id)
    
    print("🏁 Process completed")
