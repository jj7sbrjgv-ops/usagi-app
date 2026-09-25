import io
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'utest.json'


def get_drive_service():
    import streamlit as st  # secrets参照用

    if "gcp_service_account" in st.secrets:
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
    else:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
    return build('drive', 'v3', credentials=creds)


def get_file_id(service, file_name, folder_id):
  query = f"'{folder_id}' in parents and name = '{file_name}' and trashed = false"
  results = (
      service.files()
      .list(
          q=query,
          fields='files(id, name)',
          supportsAllDrives=True,
          includeItemsFromAllDrives=True,
      )
      .execute()
  )
  items = results.get('files', [])
  if items:
    return items[0]['id']
  return None


def load_json_from_drive(service, file_id):
  request = service.files().get_media(fileId=file_id)
  file_stream = io.BytesIO()
  downloader = MediaIoBaseDownload(file_stream, request)
  done = False
  while not done:
    _, done = downloader.next_chunk()
  file_stream.seek(0)
  return json.loads(file_stream.read().decode('utf-8'))


def save_json_to_drive(service, data, folder_id, file_name, file_id=None):
  temp_path = 'temp_data.json'
  with open(temp_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

  media = MediaFileUpload(temp_path, mimetype='application/json')

  if file_id:
    service.files().update(
        fileId=file_id, media_body=media, supportsAllDrives=True
    ).execute()
  else:
    file_metadata = {
        'name': file_name,
        'parents': [folder_id],
    }
    service.files().create(
        body=file_metadata, media_body=media, supportsAllDrives=True
    ).execute()
