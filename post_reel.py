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
INSTAGRAM_API_VERSION = "v18.0"

# ===== ENVIRONMENT VALIDATION =====
def validate_environment():
    """Check all required environment variables"""
    required_vars = {
        "GDRIVE_CREDENTIALS": os.getenv("GDRIVE_CREDENTIALS"),
        "GDRIVE_FOLDER_ID": GDRIVE_FOLDER_ID,
        "INSTAGRAM_ACCESS_TOKEN": INSTAGRAM_ACCESS_TOKEN,
        "INSTAGRAM_USER_ID": INSTAGRAM_USER_ID
    }
    
    missing = [name for name, value in required_vars.items() if not value]
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        exit(1)

    # Verify Instagram token and user ID
    verify_instagram_credentials()

def verify_instagram_credentials():
    """Validate Instagram token and user ID"""
    try:
        # Check token permissions
        debug_url = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}/debug_token"
        debug_params = {
            "input_token": INSTAGRAM_ACCESS_TOKEN,
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        debug_resp = requests.get(debug_url, params=debug_params).json()
        
        if not debug_resp.get("data", {}).get("is_valid", False):
            print("❌ Invalid Instagram token")
            exit(1)

        # Verify user ID exists
        accounts_url = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}/me/accounts"
        accounts_params = {
            "fields": "instagram_business_account",
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        accounts_resp = requests.get(accounts_url, params=accounts_params).json()
        
        if not any(acc.get("instagram_business_account", {}).get("id") == INSTAGRAM_USER_ID 
                  for acc in accounts_resp.get("data", [])):
            print("❌ Instagram User ID doesn't match token permissions")
            exit(1)
            
        print("✅ Instagram credentials validated")
    except Exception as e:
        print(f"🚨 Instagram verification failed: {str(e)}")
        exit(1)

# ===== GOOGLE DRIVE SETUP =====
def init_gdrive_service():
    """Initialize Google Drive API"""
    try:
        with open(SERVICE_ACCOUNT_FILE, "w") as f:
            json.dump(json.loads(os.getenv("GDRIVE_CREDENTIALS")), f)
        
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        print(f"❌ Google Drive setup failed: {str(e)}")
        exit(1)

# ===== REEL HANDLING =====
def get_next_reel(drive_service):
    """Get oldest MP4 from Google Drive folder"""
    try:
        results = drive_service.files().list(
            q=f"'{GDRIVE_FOLDER_ID}' in parents and mimeType='video/mp4'",
            fields="files(id, name, mimeType, webContentLink)",
            orderBy="createdTime",
            pageSize=1,
            supportsAllDrives=True
        ).execute()
        
        if not results.get("files"):
            print("ℹ️ No reels found in folder")
            return None, None
            
        reel = results["files"][0]
        print(f"🎬 Found reel: {reel['name']}")
        return reel["webContentLink"], reel["id"]
    except Exception as e:
        print(f"❌ Failed to get reel: {str(e)}")
        return None, None

def delete_reel(drive_service, file_id):
    """Delete reel after successful posting"""
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
    try:
        # Step 1: Create container
        print("📤 Creating Instagram container...")
        create_url = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}/{INSTAGRAM_USER_ID}/media"
        params = {
            "video_url": video_url,
            "caption": "Posted via automation 🚀 #Tech",
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
        
        # Step 2: Check processing status
        print("⏳ Waiting for video processing...")
        status_url = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}/{container_id}"
        status_params = {
            "fields": "status_code",
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        
        for _ in range(10):  # Max 10 checks (150 seconds total)
            time.sleep(15)
            status = requests.get(status_url, params=status_params).json()
            if status.get("status_code") == "FINISHED":
                break
        else:
            print("❌ Video processing timed out")
            return False
        
        # Step 3: Publish
        print("📡 Publishing reel...")
        publish_url = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}/{INSTAGRAM_USER_ID}/media_publish"
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
        print(f"🚨 Instagram upload failed: {str(e)}")
        return False

# ===== MAIN EXECUTION =====
if __name__ == "__main__":
    print("🚀 Starting reel posting process...")
    
    # Validate environment first
    validate_environment()
    
    # Initialize services
    drive_service = init_gdrive_service()
    
    # Get next reel
    reel_url, reel_id = get_next_reel(drive_service)
    if not reel_url:
        exit(0)
        
    # Upload to Instagram
    if upload_to_instagram(reel_url):
        delete_reel(drive_service, reel_id)
    
    print("🏁 Process completed")
