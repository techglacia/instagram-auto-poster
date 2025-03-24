import os

print("Current environment variables:")
print(f"INSTAGRAM_ACCESS_TOKEN: {'exists' if os.getenv('INSTAGRAM_ACCESS_TOKEN') else 'missing'}")
print(f"INSTAGRAM_USER_ID: {'exists' if os.getenv('INSTAGRAM_USER_ID') else 'missing'}")
print(f"GDRIVE_CREDENTIALS: {'exists' if os.getenv('GDRIVE_CREDENTIALS') else 'missing'}")
print(f"GDRIVE_FOLDER_ID: {'exists' if os.getenv('GDRIVE_FOLDER_ID') else 'missing'}")
