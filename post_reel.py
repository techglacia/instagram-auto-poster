import os
import json
import requests
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Load Google Drive credentials from GitHub Secret
SERVICE_ACCOUNT_FILE = "service_account.json"
gdrive_creds = os.getenv("GDRIVE_CREDENTIALS")

if gdrive_creds:
    try:
        with open(SERVICE_ACCOUNT_FILE, "w") as f:
            f.write(json.dumps(json.loads(gdrive_creds)))  # Ensure valid JSON
    except Exception as e:
        print(f"Error writing service account file: {e}")
        exit()
else:
    print("⚠️ Missing Google Drive credentials!")
    exit()

# Authenticate with Google Drive
SCOPES = ["https://www.googleapis.com/auth/drive"]
try:
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    drive_service = build("drive", "v3", credentials=creds)
except Exception as e:
    print(f"⚠️ Google Drive authentication failed: {e}")
    exit()

# Folder ID where reels are stored (Replace with your actual Folder ID)
FOLDER_ID = "1GpQI3AlCV1j6an2ahynEOs7F79Dp3nUv"

def get_next_reel():
    """Fetch the next reel from Google Drive"""
    try:
        results = (
            drive_service.files()
            .list(q=f"'{FOLDER_ID}' in parents and mimeType='video/mp4'", 
                  fields="files(id, name)", 
                  orderBy="createdTime")
            .execute()
        )
        files = results.get("files", [])

        if not files:
            print("No reels found in the folder.")
            return None, None

        # Pick the first reel in the list
        reel_id = files[0]["id"]
        reel_name = files[0]["name"]

        # Generate a direct download link
        reel_url = f"https://drive.google.com/uc?export=download&id={reel_id}"

        return reel_url, reel_id
    except Exception as e:
        print(f"Error fetching reels: {e}")
        return None, None

def delete_reel(file_id):
    """Delete the posted reel from Google Drive"""
    try:
        drive_service.files().delete(fileId=file_id).execute()
        print("✅ Reel deleted successfully.")
    except Exception as e:
        print(f"⚠️ Error deleting reel: {e}")

# Instagram API details
INSTAGRAM_ACCESS_TOKEN = os.getenv("EAAJnCNEZCqUIBOy0kjcqr8I7BDjqmafbY8Ru10Q6BnK50vGQZCKyrRTIYJqVgwbMldZCSLZAKptF9ZBhzaZBCyQcfSy4K7t265RuCErtKauCuGNbCDasru97Yo7KQtdA31Y9g3lut0J0gEPQkTclgZCafhnt5Tz43GJW9htStf8g30XfOJRTSgcyw7XBHKZB5DO42LAdllZAf9c8aamyIr5FMrBVHKhZCv")
INSTAGRAM_USER_ID = os.getenv("17841472944697055")

if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_USER_ID:
    print("⚠️ Missing Instagram API credentials!")
    exit()

INSTAGRAM_API_URL = f"https://graph.facebook.com/v18.0/{INSTAGRAM_USER_ID}/media"

def instagram_post(video_url):
    """Post the reel to Instagram"""
    try:
        payload = {
            "video_url": video_url,
            "caption": "Daily Reel! #Reels #Automation",
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        response = requests.post(INSTAGRAM_API_URL, data=payload)
        if response.status_code == 200:
            container_id = response.json().get("id")
            print(f"✅ Video uploaded! Container ID: {container_id}")

            publish_url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_USER_ID}/media_publish"
            publish_payload = {
                "creation_id": container_id,
                "access_token": INSTAGRAM_ACCESS_TOKEN
            }
            publish_response = requests.post(publish_url, data=publish_payload)
            if publish_response.status_code == 200:
                print("🎉 Reel published successfully!")
                return True
            else:
                print(f"❌ Failed to publish reel: {publish_response.text}")
                return False
        else:
            print(f"❌ Failed to upload reel: {response.text}")
            return False
    except Exception as e:
        print(f"⚠️ Error posting to Instagram: {e}")
        return False

# Fetch the next reel
reel_url, reel_id = get_next_reel()
if reel_url:
    print(f"Next Reel: {reel_url}")

    if instagram_post(reel_url):
        if reel_id:
            delete_reel(reel_id)
