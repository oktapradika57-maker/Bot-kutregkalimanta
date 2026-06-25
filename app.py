import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from datetime import datetime

# =========================================================
# ⚠️ UBAH DI SINI: MASUKKAN ID FOLDER GOOGLE DRIVE ANDA
# =========================================================
FOLDER_DRIVE_ID = 'MASUKKAN_ID_FOLDER_DRIVE_ANDA_DI_SINI'

# Konfigurasi Tampilan Halaman
st.set_page_config(page_title="Kinarya Utama Teknik - Kamera", layout="centered")

st.title("📸 Kamera Pengunggah Google Drive")
st.write("Ambil foto di bawah ini untuk langsung disimpan ke Google Drive pribadi Anda.")

kredensial_valid = False

# =========================================================
# MEMBACA KREDENSIAL OAUTH2 DARI STREAMLIT SECRETS
# =========================================================
try:
    if "gcp_oauth" in st.secrets:
        creds = Credentials(
            token=None,
            refresh_token=st.secrets["gcp_oauth"]["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=st.secrets["gcp_oauth"]["client_id"],
            client_secret=st.secrets["gcp_oauth"]["client_secret"]
        )
        service_drive = build('drive', 'v3', credentials=creds)
        kredensial_valid = True
    else:
        st.error("❌ Periksa Streamlit Secrets! Kotak '[gcp_oauth]' belum diisi.")
except Exception as e:
    st.error(f"❌ Gagal memuat kredensial: {e}")

# =========================================================
# PROSES AMBIL FOTO & UPLOAD
# =========================================================
if kredensial_valid:
    # Komponen kamera langsung tanpa form agar instan dan cepat
    foto_kamera = st.camera_input("Silakan Ambil Foto:")
    
    if foto_kamera:
        with st.spinner("Sedang mengunggah foto langsung ke Google Drive Anda..."):
            try:
                # Membuat nama file unik berdasarkan waktu saat foto diambil
                waktu_sekarang = datetime.now().strftime("%Y%m%d_%H%M%S")
                nama_file_foto = f"Foto_{waktu_sekarang}.png"
                
                # Konversi file foto ke byte stream
                buffer_foto = io.BytesIO(foto_kamera.read())
                
                file_metadata = {
                    'name': nama_file_foto,
                    'parents': [FOLDER_DRIVE_ID]
                }
                
                media = MediaIoBaseUpload(buffer_foto, mimetype="image/png", resumable=True)
                
                # Eksekusi upload langsung atas nama akun Gmail Anda
                uploaded_file = service_drive.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink'
                ).execute()
                
                st.success(f"🎉 Berhasil! Foto tersimpan di Drive dengan nama: {nama_file_foto}")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Gagal mengunggah ke Drive: {e}")
                st.info("Pastikan ID Folder di Baris 10 sudah benar dan akun Anda memiliki ruang penyimpanan.")
