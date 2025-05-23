import argparse
import json
import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def upload_to_drive(filepath: str, folder_id: str) -> str:
    creds = service_account.Credentials.from_service_account_info(
        json.loads(os.environ["GOOGLE_CREDENTIALS"]),
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    drive = build("drive", "v3", credentials=creds)

    file_metadata: dict[str, str | list[str]] = {
        "name": Path(filepath).name,
        "parents": [folder_id],                     # target folder
        "mimeType": "application/vnd.google.colaboratory",
    }

    media = MediaFileUpload(filepath, mimetype="application/x-ipynb+json")

    create_kwargs: dict[str, object] = {
        "body": file_metadata,
        "media_body": media,
        "fields": "id",
        "supportsAllDrives": True,                  # must be True for Shared Drives
    }

    file_id = (
        drive.files()
        .create(**create_kwargs)                   # type: ignore[arg-type]
        .execute()
        .get("id")
    )

    colab_link = f"https://colab.research.google.com/drive/{file_id}"
    print(colab_link)
    return colab_link


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload a notebook to Google Drive.")
    parser.add_argument("notebook", help="Path to the .ipynb file")
    parser.add_argument("--folder", required=True, help="Destination folder ID")
    args = parser.parse_args()

    upload_to_drive(args.notebook, args.folder)
