import os
import json
import requests
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Load Google Drive credentials from GitHub Secret
SERVICE_ACCOUNT_FILE = "service_account.json"

gdrive_creds = os.getenv("GDRIVE_CREDENTIALS")
if gdrive_creds:
    with open(SERVICE_ACCOUNT_FILE, "w") as f:
        f.write(gdrive_creds)

# Authenticate with Google Drive
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
drive_service = build("drive", "v3", credentials=creds)

# Folder ID where reels are stored (Replace with your actual Folder ID)
FOLDER_ID = "YOUR_GOOGLE_DRIVE_FOLDER_ID"

def get_next_reel():
    """Fetch the next reel from Google Drive"""
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

def delete_reel(file_id):
    """Delete the posted reel from Google Drive"""
    try:
        drive_service.files().delete(fileId=file_id).execute()
        print("Reel deleted successfully.")
    except Exception as e:
        print(f"Error deleting reel: {e}")

# Instagram API details
INSTAGRAM_ACCESS_TOKEN = "YOUR_INSTAGRAM_ACCESS_TOKEN"
INSTAGRAM_USER_ID = "YOUR_INSTAGRAM_USER_ID"
INSTAGRAM_API_URL = f"https://graph.facebook.com/v18.0/{INSTAGRAM_USER_ID}/media"

def instagram_post(video_url):
    """Post the reel to Instagram"""
    payload = {
        "video_url": video_url,
        "caption": "Daily Reel! #Reels #Automation",
        "access_token": INSTAGRAM_ACCESS_TOKEN,
        "media_type": "REELS"
    }
    
    response = requests.post(INSTAGRAM_API_URL, data=payload)
    if response.status_code == 200:
        print("Reel posted successfully!")
    else:
        print("Failed to post reel:", response.text)

# Fetch the next reel
reel_url, reel_id = get_next_reel()
if reel_url:
    print(f"Next Reel: {reel_url}")

    # Post to Instagram
    instagram_post(reel_url)

    # Delete the reel after posting
    if reel_id:
        delete_reel(reel_id)
