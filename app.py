import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import json
from datetime import datetime

# ==========================================
# 1. KONFIGURASI UTAMA (WAJIB DIISI)
# ==========================================
FOLDER_DRIVE_ID = '1En5tPkQsf1OQNpRgj1CcKpgQGo5LtCl5'

# GANTI DENGAN DATA ASLI ANDA DI SINI:
SPREADSHEET_NAME = 'Data Form Streamlit'  # <-- Ganti nama Sheet Anda
USER_EMAIL_ASLI = 'oktapradika57@gmail.com'   # <-- Ganti dengan Gmail Anda (Contoh: bahrul@gmail.com)

scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

st.title("📸 Form Absensi / Input Kamera Langsung")
kredensial_valid = False

try:
    if "gcp_json" in st.secrets:
        # Membaca format JSON mentah dari Secrets untuk menghindari error padding/TOML
        creds_dict = json.loads(st.secrets["gcp_json"])
        
        # Memperbaiki pembacaan text \n pada private key
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client_sheets = gspread.authorize(creds)
        service_drive = build('drive', 'v3', credentials=creds)
        kredensial_valid = True
    else:
        st.error("❌ Komponen Secrets 'gcp_json' tidak ditemukan. Pastikan Langkah 1 sudah dilakukan.")
except Exception as e:
    st.error(f"❌ Gagal memuat kredensial dari Streamlit Secrets: {e}")

# ==========================================
# 2. FUNGSI UPLOAD FOTO + TRANSFER KEPEMILIKAN
# ==========================================
def upload_foto_to_drive(bytes_foto, file_name):
    try:
        file_metadata = {
            'name': file_name,
            'parents': [FOLDER_DRIVE_ID]
        }
        media = MediaIoBaseUpload(bytes_foto, mimetype="image/png", resumable=True)
        
        # Langkah A: Upload file ke folder menggunakan akun robot
        uploaded_file = service_drive.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        file_id = uploaded_file.get('id')
        
        # Langkah B: Langsung pindahkan kepemilikan file ke Email Utama Anda agar memakai kuota Anda sendiri
        permission_metadata = {
            'type': 'user',
            'role': 'owner',
            'emailAddress': USER_EMAIL_ASLI
        }
        
        service_drive.permissions().create(
            fileId=file_id,
            body=permission_metadata,
            transferOwnership=True
        ).execute()
        
        return uploaded_file.get('webViewLink')
    except Exception as e:
        st.error(f"Gagal upload foto ke Drive atau gagal transfer kepemilikan: {e}")
        return None

# ==========================================
# 3. TAMPILAN INTERFACE FORM STREAMLIT
# ==========================================
if kredensial_valid:
    st.write("Silakan isi nama, keterangan, dan ambil foto langsung dari kamera HP Anda.")
    
    with st.form(key='input_form', clear_on_submit=True):
        nama = st.text_input("Nama Lengkap:")
        catatan = st.text_area("Catatan/Keterangan:")
        foto_kamera = st.camera_input("Ambil Foto Langsung dari Kamera:")
        
        submit_button = st.form_submit_button(label='Kirim Data & Foto')

    if submit_button:
        if nama and foto_kamera:
            if USER_EMAIL_ASLI == 'TULIS_EMAIL_GMAIL_ASLI_ANDA_DI_SINI':
                st.error("❌ Eror: Anda belum mengubah USER_EMAIL_ASLI di dalam kode script!")
            else:
                with st.spinner("Sedang memproses, mengunggah, dan mentransfer kuota file..."):
                    waktu_sekarang = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nama_file_foto = f"{waktu_sekarang}_{nama}.png"
                    
                    buffer_foto = io.BytesIO(foto_kamera.read())
                    url_foto = upload_foto_to_drive(buffer_foto, nama_file_foto)
                    
                    if url_foto:
                        try:
                            sheet = client_sheets.open(SPREADSHEET_NAME).sheet1
                            timestamp_sheet = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            baris_baru = [nama, catatan, url_foto, timestamp_sheet]
                            sheet.append_row(baris_baru)
                            
                            st.success("🎉 Sukses Besar! Data tersimpan dan foto berhasil masuk ke Drive menggunakan kuota Anda!")
                        except Exception as e:
                            st.error(f"Gagal menulis data ke Google Sheets: {e}")
        else:
            st.warning("Mohon isi Kolom Nama dan Ambil Foto terlebih dahulu!")
else:
    st.warning("⚠️ Form dikunci sementara karena kredensial belum siap.")
