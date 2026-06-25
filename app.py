import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from datetime import datetime

# =========================================================
# UBAH BAGIAN INI SAJA (BERADA DI BARIS 11)
# =========================================================
FOLDER_DRIVE_ID = '1En5tPkQsf1OQNpRgj1CcKpgQGo5LtCl5'

scope = ['https://www.googleapis.com/auth/drive']

st.title("📸 Kamera Pengunggah Google Drive")
st.write("Ambil foto di bawah ini untuk langsung disimpan ke Google Drive.")

kredensial_valid = False

# =========================================================
# MEMBACA KREDENSIAL SECRETS
# =========================================================
try:
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        # Mengatasi error pembacaan format private key baris baru
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        service_drive = build('drive', 'v3', credentials=creds)
        kredensial_valid = True
    else:
        st.error("❌ Secrets '[gcp_service_account]' belum dikonfigurasi di Streamlit Cloud.")
except Exception as e:
    st.error(f"❌ Gagal membaca Secrets: {e}")

# =========================================================
# PROSES AMBIL FOTO & UPLOAD
# =========================================================
if kredensial_valid:
    # Komponen kamera langsung tanpa form agar instan
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
                
                # Eksekusi upload menggunakan akun bot ke folder bersama Anda
                uploaded_file = service_drive.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink'
                ).execute()
                
                st.success(f"🎉 Berhasil! Foto tersimpan di Drive dengan nama: {nama_file_foto}")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Gagal mengunggah ke Drive: {e}")
                st.info("Pastikan Anda sudah membagikan (Share) folder Drive Anda ke email bot (sebagai Editor).")
