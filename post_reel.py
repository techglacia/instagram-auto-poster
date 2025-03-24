import gdown
import requests

# Instagram API Credentials
ACCESS_TOKEN = "YOUR_INSTAGRAM_ACCESS_TOKEN"
INSTAGRAM_USER_ID = "YOUR_INSTAGRAM_USER_ID"
FOLDER_URL = "https://drive.google.com/drive/folders/YOUR_FOLDER_ID"

# Step 1: Download the latest reel
gdown.download_folder(FOLDER_URL, quiet=True, output="reel.mp4")

# Step 2: Upload the video to Instagram
upload_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/media"
params = {
    "video_url": "https://yourpublicstorage.com/reel.mp4",
    "caption": "Your daily reel! #reels #viral",
    "access_token": ACCESS_TOKEN
}

response = requests.post(upload_url, data=params)
result = response.json()
creation_id = result.get("id")

# Step 3: Publish the uploaded reel
publish_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/media_publish"
publish_params = {
    "creation_id": creation_id,
    "access_token": ACCESS_TOKEN
}

publish_response = requests.post(publish_url, data=publish_params)
print(publish_response.json())
