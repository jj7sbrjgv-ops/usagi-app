import io
import json
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# --- 設定情報 ---
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'utest.json'

# Google DriveのフォルダIDとファイル名
FOLDER_ID = '1AQ9TZxgI4dR8QYPghHQVJmVDmCRQoPb1'  # ★ご自身のフォルダIDに書き換えてください
FILE_NAME = 'rabbit_data.json'


# --- Google Drive API 関連関数 ---
def get_drive_service():
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


def save_json_to_drive(service, data, folder_id, file_id=None):
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
        'name': FILE_NAME,
        'parents': [folder_id],
    }
    service.files().create(
        body=file_metadata, media_body=media, supportsAllDrives=True
    ).execute()


# --- Streamlit 画面制御 ---
st.title('🐰 ウサギの体調管理（Google Drive連携）')

service = get_drive_service()

# 1. まず file_id を取得
file_id = get_file_id(service, FILE_NAME, FOLDER_ID)

# 2. データを読み込み（ファイルがない場合や 'daily_logs' が無い場合も安全に初期化）
if file_id:
  data = load_json_from_drive(service, file_id)
else:
  data = {}

if not isinstance(data, dict) or 'daily_logs' not in data:
  data = {'daily_logs': {}}


# 3. 入力フォーム
with st.form('log_form'):
  date_str = str(
      st.date_input('日付', value=st.session_state.get('date', None))
  )
  pellet = st.number_input('ペレット量 (g)', min_value=0, value=30)
  notes = st.text_area('メモ・体調の様子')
  submitted = st.form_submit_button('保存する')

  if submitted:
    data['daily_logs'][date_str] = {
        'pellet_g': pellet,
        'notes': notes,
    }
    save_json_to_drive(service, data, FOLDER_ID, file_id)
    st.success('Google Driveへ記録を保存しました！')


# 4. 履歴表示
st.subheader('過去の記録')
st.json(data.get('daily_logs', {}))