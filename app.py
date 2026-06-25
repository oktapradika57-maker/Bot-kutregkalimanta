import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from datetime import datetime

# ==========================================
# 1. KONFIGURASI ID GOOGLE SPREADSHEET & DRIVE
# ==========================================
# SILAKAN GANTI DENGAN ID FOLDER DRIVE DAN NAMA SPREADSHEET ANDA
FOLDER_DRIVE_ID = 'TULIS_ID_FOLDER_GOOGLE_DRIVE_ANDA_DI_SINI'
SPREADSHEET_NAME = 'TULIS_NAMA_GOOGLE_SHEET_ANDA_DI_SINI'

# Setup Cakupan Akses API
scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

try:
    # Mengambil kredensial secara aman dari Streamlit Secrets TOML
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    
    # Otorisasi layanan Google Sheets & Drive
    client_sheets = gspread.authorize(creds)
    service_drive = build('drive', 'v3', credentials=creds)
except Exception as e:
    st.error(f"Gagal memuat kredensial dari Streamlit Secrets: {e}")
    st.stop()

# ==========================================
# 2. FUNGSI UNTUK UPLOAD FOTO KE GOOGLE DRIVE
# ==========================================
def upload_foto_to_drive(file_uploaded, file_name):
    try:
        file_metadata = {
            'name': file_name,
            'parents': [FOLDER_DRIVE_ID]
        }
        media = MediaIoBaseUpload(io.BytesIO(file_uploaded.read()), mimetype=file_uploaded.type, resumable=True)
        
        # Proses Upload ke Google Drive
        uploaded_file = service_drive.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        # Mengubah izin file foto agar bisa dilihat oleh semua orang yang memiliki link
        service_drive.permissions().create(
            fileId=uploaded_file.get('id'),
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        return uploaded_file.get('webViewLink')
    except Exception as e:
        st.error(f"Gagal upload foto ke Drive: {e}")
        return None

# ==========================================
# 3. TAMPILAN INTERFACE FORM STREAMLIT
# ==========================================
st.title("📋 Form Input Data ke Google Sheets")
st.write("Silakan isi teks dan unggah foto melalui form di bawah ini.")

# Membuat Form di Streamlit
with st.form(key='input_form', clear_on_submit=True):
    nama = st.text_input("Nama Lengkap:")
    catatan = st.text_area("Catatan/Keterangan:")
    foto = st.file_uploader("Unggah Foto (PNG/JPG):", type=['png', 'jpg', 'jpeg'])
    
    submit_button = st.form_submit_button(label='Kirim Data')

# Logika ketika tombol kirim ditekan
if submit_button:
    if nama and foto:
        with st.spinner("Sedang memproses dan mengunggah data..."):
            waktu_sekarang = datetime.now().strftime("%Y%m%d_%H%M%S")
            nama_file_foto = f"{waktu_sekarang}_{nama}.png"
            
            # 1. Upload foto ke Drive terlebih dahulu untuk mendapatkan URL-nya
            url_foto = upload_foto_to_drive(foto, nama_file_foto)
            
            if url_foto:
                # 2. Input data teks + URL foto ke Google Sheets
                try:
                    sheet = client_sheets.open(SPREADSHEET_NAME).sheet1
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Susun data dalam bentuk baris array
                    baris_baru = [nama, catatan, url_foto, timestamp]
                    
                    # Tambahkan ke baris paling bawah di Spreadsheet
                    sheet.append_row(baris_baru)
                    
                    st.success("🎉 Data dan link foto berhasil disimpan ke Google Sheets!")
                except Exception as e:
                    st.error(f"Gagal menyimpan data ke Sheets: {e}")
            else:
                st.error("Proses dibatalkan karena foto gagal diunggah.")
    else:
        st.warning("Mohon isi Kolom Nama dan Unggah Foto terlebih dahulu!")
