import streamlit as st
from drive_handler import (
    get_drive_service,
    get_file_id,
    load_json_from_drive,
    save_json_to_drive,
)

# Google DriveのフォルダIDとファイル名
FOLDER_ID = '1AQ9TZxgI4dR8QYPghHQVJmVDmCRQoPb1'  # ★ご自身のフォルダIDに書き換えてください
FILE_NAME = 'rabbit_data.json'


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
    save_json_to_drive(service, data, FOLDER_ID, FILE_NAME, file_id)
    st.success('Google Driveへ記録を保存しました！')


# 4. 履歴表示
st.subheader('過去の記録')
st.json(data.get('daily_logs', {}))