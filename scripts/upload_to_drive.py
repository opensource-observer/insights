import argparse
import os
import json
import google.auth
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_to_drive(filepath, folder_id):
    creds = service_account.Credentials.from_service_account_info(
        json.loads(os.environ["GOOGLE_CREDENTIALS"]),
        scopes=["https://www.googleapis.com/auth/drive"]
    )

    service = build("drive", "v3", credentials=creds)

    file_metadata = {
        "name": os.path.basename(filepath),
        "parents": [folder_id],
        "mimeType": "application/vnd.google.colaboratory"
    }

    media = MediaFileUpload(filepath, mimetype="application/x-ipynb+json")

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    file_id = uploaded_file.get("id")
    colab_link = f"https://colab.research.google.com/drive/{file_id}"

    print(colab_link)
    return colab_link

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", help="Path to the notebook")
    parser.add_argument("--folder", help="Google Drive folder ID", required=True)
    args = parser.parse_args()

    upload_to_drive(args.notebook, args.folder)
