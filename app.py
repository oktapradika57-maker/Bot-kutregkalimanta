def upload_foto_to_drive(bytes_foto, file_name):
    try:
        file_metadata = {
            'name': file_name,
            'parents': [FOLDER_DRIVE_ID]
        }
        media = MediaIoBaseUpload(bytes_foto, mimetype="image/png", resumable=True)
        
        # PROSES UPLOAD UTAMA
        uploaded_file = service_drive.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        file_id = uploaded_file.get('id')
        
        # 1. TAMBAHKAN LINK PERMISSION AGAR BISA DILIHAT PUBLIK
        service_drive.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        # 2. SOLUSI KUOTA: Transfer kepemilikan file ke email asli Anda
        # GANTI 'email_anda_yang_punya_drive@gmail.com' dengan email asli Google Drive Anda
        try:
            service_drive.permissions().create(
                fileId=file_id,
                body={
                    'type': 'user',
                    'role': 'owner',
                    'emailAddress': 'email_anda_yang_punya_drive@gmail.com' 
                },
                transferOwnership=True
            ).execute()
        except Exception as ownership_error:
            # Jika transfer kepemilikan gagal karena batasan tipe akun,
            # sistem akan tetap melanjutkan karena folder utama Anda sudah dibagikan.
            pass
            
        return uploaded_file.get('webViewLink')
    except Exception as e:
        st.error(f"Gagal upload foto ke Drive: {e}")
        return None
