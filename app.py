import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from datetime import datetime

# Amankan aplikasi agar tidak langsung blank hitam jika terjadi error di tingkat awal
st.set_page_index = 0

# ==========================================
# 1. KONFIGURASI ID GOOGLE SPREADSHEET & DRIVE
# ==========================================
FOLDER_DRIVE_ID = '1En5tPkQsf1OQNpRgj1CcKpgQGo5LtCl5'
SPREADSHEET_NAME = 'Data Form Streamlit'  # <-- Ganti dengan nama Sheet Anda yang asli

scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Judul Utama Aplikasi (Diletakkan di atas agar halaman tidak blank)
st.title("📸 Form Absensi / Input Kamera Langsung")

# Inisialisasi variabel kontrol
kredensial_valid = False

try:
    # Memeriksa apakah komponen rahasia terdaftar di Streamlit Cloud
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        # Otorisasi layanan Google menggunakan kredensial Secrets
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client_sheets = gspread.authorize(creds)
        service_drive = build('drive', 'v3', credentials=creds)
        kredensial_valid = True
    else:
        st.error("❌ Komponen '[gcp_service_account]' tidak ditemukan di menu Secrets Streamlit Anda. Mohon periksa kembali konfigurasi App Settings Anda.")
except Exception as e:
    st.error(f"❌ Terjadi kesalahan saat membaca rahasia (Secrets): {e}")
    st.info("Saran: Pastikan teks di menu Secrets sudah di-Save dengan format TOML yang benar dan tidak memunculkan warna merah.")

# ==========================================
# 2. FUNGSI UNTUK UPLOAD FOTO KE GOOGLE DRIVE
# ==========================================
def upload_foto_to_drive(bytes_foto, file_name):
    try:
        file_metadata = {
            'name': file_name,
            'parents': [FOLDER_DRIVE_ID]
        }
        media = MediaIoBaseUpload(bytes_foto, mimetype="image/png", resumable=True)
        
        uploaded_file = service_drive.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        return uploaded_file.get('webViewLink')
    except Exception as e:
        st.error(f"Gagal upload foto ke Drive: {e}")
        return None

# ==========================================
# 3. TAMPILAN INTERFACE FORM STREAMLIT
# ==========================================
if kredensial_valid:
    st.write("Silakan isi nama, keterangan, dan ambil foto langsung dari kamera HP Anda.")

    with st.form(key='input_form', clear_on_submit=True):
        nama = st.text_input("Nama Lengkap:")
        catatan = st.text_area("Catatan/Keterangan:")
        
        # Fitur Kamera Utama
        foto_kamera = st.camera_input("Ambil Foto Langsung dari Kamera:")
        
        submit_button = st.form_submit_button(label='Kirim Data & Foto')

    if submit_button:
        if nama and foto_kamera:
            with st.spinner("Sedang memproses dan mengunggah data..."):
                waktu_sekarang = datetime.now().strftime("%Y%m%d_%H%M%S")
                nama_file_foto = f"{waktu_sekarang}_{nama}.png"
                
                # Konversi foto langsung ke file bytes memory buffer
                buffer_foto = io.BytesIO(foto_kamera.read())
                
                url_foto = upload_foto_to_drive(buffer_foto, nama_file_foto)
                
                if url_foto:
                    try:
                        sheet = client_sheets.open(SPREADSHEET_NAME).sheet1
                        timestamp_sheet = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        baris_baru = [nama, catatan, url_foto, timestamp_sheet]
                        sheet.append_row(baris_baru)
                        
                        st.success("🎉 Sukses! Data dan Foto berhasil disimpan!")
                    except Exception as e:
                        st.error(f"Gagal menyimpan data ke Sheets: {e}")
        else:
            st.warning("Mohon isi Kolom Nama dan Ambil Foto terlebih dahulu!")
else:
    st.warning("⚠️ Form dikunci sementara karena kredensial Google API belum siap.")
