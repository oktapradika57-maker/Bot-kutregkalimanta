import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# 1. KONFIGURASI ID GOOGLE SPREADSHEET & DRIVE
# ==========================================
FOLDER_DRIVE_ID = '1En5tPkQsf1OQNpRgj1CcKpgQGo5LtCl5'
SPREADSHEET_NAME = 'Data Form Streamlit'  # <-- Ganti dengan nama Sheet Anda

scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client_sheets = gspread.authorize(creds)
    service_drive = build('drive', 'v3', credentials=creds)
except Exception as e:
    st.error(f"Gagal memuat kredensial dari Streamlit Secrets: {e}")
    st.stop()

# ==========================================
# 2. FUNGSI MEMBERI TIMESTAMPS PADA FOTO
# ==========================================
def beri_timestamp_pada_foto(foto_mentah):
    # Buka foto menggunakan Pillow
    img = Image.open(foto_mentah)
    draw = ImageDraw.Draw(img)
    
    # Ambil waktu saat ini untuk teks watermark
    waktu_teks = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Menentukan ukuran font proporsional berdasarkan lebar gambar
    lebar_gambar, tinggi_gambar = img.size
    ukuran_font = int(lebar_gambar * 0.035)  # Font berukuran ~3.5% dari lebar foto
    
    try:
        # Menggunakan font bawaan jika ada
        font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
        
    # Posisi teks: Pojok kanan bawah (dengan margin)
    margin = 20
    posisi_x = lebar_gambar - (ukuran_font * 11) - margin  # Estimasi panjang teks
    posisi_y = tinggi_gambar - ukuran_font - margin
    
    # Gambar bayangan hitam (agar teks tetap terbaca di latar terang)
    draw.text((posisi_x + 2, posisi_y + 2), waktu_teks, fill="black", font=font)
    # Gambar teks utama berwarna kuning/putih mencolok
    draw.text((posisi_x, posisi_y), waktu_teks, fill="yellow", font=font)
    
    # Simpan kembali ke dalam bentuk bytes memory buffer
    buffer_foto = io.BytesIO()
    img.save(buffer_foto, format="PNG")
    buffer_foto.seek(0)
    return buffer_foto

# ==========================================
# 3. FUNGSI UNTUK UPLOAD FOTO KE GOOGLE DRIVE
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
        
        service_drive.permissions().create(
            fileId=uploaded_file.get('id'),
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        return uploaded_file.get('webViewLink')
    except Exception as e:
        st.error(f"Gagal upload foto ke Drive: {e}")
        return None

# ==========================================
# 4. TAMPILAN INTERFACE FORM STREAMLIT
# ==========================================
st.title("📸 Form Absensi / Input Kamera Langsung")
st.write("Silakan isi nama, keterangan, dan ambil foto langsung dari kamera HP Anda.")

with st.form(key='input_form', clear_on_submit=True):
    nama = st.text_input("Nama Lengkap:")
    catatan = st.text_area("Catatan/Keterangan:")
    
    # FITUR BARU: Mengaktifkan Kamera HP/Laptop Langsung
    foto_kamera = st.camera_input("Ambil Foto Langsung dari Kamera:")
    
    submit_button = st.form_submit_button(label='Kirim Data & Foto')

if submit_button:
    if nama and foto_kamera:
        with st.spinner("Sedang memproses, menempelkan timestamp, dan mengunggah..."):
            waktu_sekarang = datetime.now().strftime("%Y%m%d_%H%M%S")
            nama_file_foto = f"{waktu_sekarang}_{nama}.png"
            
            # 1. Beri watermark timestamp pada hasil foto kamera
            foto_ber_timestamp = beri_timestamp_pada_foto(foto_kamera)
            
            # 2. Upload foto yang sudah dimodifikasi ke Drive
            url_foto = upload_foto_to_drive(foto_ber_timestamp, nama_file_foto)
            
            if url_foto:
                # 3. Masukkan data ke Sheets
                try:
                    sheet = client_sheets.open(SPREADSHEET_NAME).sheet1
                    timestamp_sheet = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    baris_baru = [nama, catatan, url_foto, timestamp_sheet]
                    sheet.append_row(baris_baru)
                    
                    st.success("🎉 Sukses! Foto ber-timestamp dan data Anda berhasil disimpan!")
                except Exception as e:
                    st.error(f"Gagal menyimpan data ke Sheets: {e}")
    else:
        st.warning("Mohon isi Kolom Nama dan Ambil Foto terlebih dahulu!")
