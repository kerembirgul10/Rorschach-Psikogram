import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from collections import Counter
from io import BytesIO
import json
from datetime import datetime

# WORD kütüphanesi
try:
    from docx import Document
except ImportError:
    pass

# --- 1. GOOGLE SHEETS BAĞLANTISI ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_info = json.loads(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)
    
    # DOSYA ADINI BURADAN KONTROL ET
    SHEET_NAME = "Rorschach_Veritabani" 
    sheet = client.open(SHEET_NAME)
    
    # SEKME İSİMLERİNİ BURADAN KONTROL ET
    user_sheet = sheet.worksheet("Kullanıcılar")
    patient_sheet = sheet.worksheet("Hastalar")
    
except gspread.exceptions.SpreadsheetNotFound:
    st.error(f"Hata: '{SHEET_NAME}' isimli bir Google Sheet dosyası bulunamadı.")
    st.stop()
except gspread.exceptions.WorksheetNotFound as e:
    st.error(f"Hata: Dosya bulundu ama '{e}' isimli sekme (sayfa) bulunamadı. Lütfen sekme ismini kontrol edin.")
    st.stop()
except Exception as e:
    st.error(f"Beklenmedik Bağlantı Hatası: {e}")
    st.stop()

# --- 2. TASARIM AYARLARI ---
st.set_page_config(page_title="Rorschach Klinik Panel", layout="wide")

st.markdown("""
    <style>
    .kart-wrapper { padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 1px solid rgba(0,0,0,0.1); }
    .footer { position: fixed; left: 0; bottom: 10px; width: 100%; text-align: center; color: #7f8c8d; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. OTURUM YÖNETİMİ ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = ""

# --- 4. GİRİŞ VE KAYIT SAYFASI (GÜNCEL) ---
def auth_page():
    st.title("🧠 Rorschach Klinik Analiz")
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    with tab1:
        login_user = st.text_input("Kullanıcı Adı", key="l_user")
        login_pw = st.text_input("Şifre", type="password", key="l_pw")
        if st.button("Giriş Yap"):
            data = user_sheet.get_all_records()
            if data:
                users_df = pd.DataFrame(data)
                # Sütun isimlerindeki olası boşlukları temizleyelim
                users_df.columns = users_df.columns.str.strip()
                
                if login_user in users_df['kullanici_adi'].values:
                    user_row = users_df[users_df['kullanici_adi'] == login_user]
                    correct_pw = str(user_row['sifre'].values[0])
                    if str(login_pw) == correct_pw:
                        st.session_state['logged_in'] = True
                        st.session_state['user'] = login_user
                        st.rerun()
                    else:
                        st.error("Hatalı şifre.")
                else:
                    st.error("Kullanıcı bulunamadı.")
            else:
                st.error("Veritabanı boş. Önce kayıt olun.")

    with tab2:
        new_user = st.text_input("Yeni Kullanıcı Adı", key="r_user")
        new_pw = st.text_input("Yeni Şifre", type="password", key="r_pw")
        new_name = st.text_input("Adınız Soyadınız", key="r_name")
        if st.button("Kayıt Ol"):
            data = user_sheet.get_all_records()
            users_df = pd.DataFrame(data) if data else pd.DataFrame(columns=['kullanici_adi', 'sifre', 'isim'])
            users_df.columns = users_df.columns.str.strip()
            
            if not users_df.empty and new_user in users_df['kullanici_adi'].values:
                st.warning("Bu kullanıcı adı zaten alınmış.")
            elif not new_user or not new_pw:
                st.error("Kullanıcı adı ve şifre boş bırakılamaz.")
            else:
                user_sheet.append_row([new_user, str(new_pw), new_name])
                st.success("Kaydınız başarıyla oluşturuldu! Şimdi giriş yapabilirsiniz.")
# --- 5. ANA PANEL (DASHBOARD) ---
def dashboard():
    st.sidebar.title(f"Hoş geldin, {st.session_state['user']}")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state['logged_in'] = False
        st.rerun()
        
    page = st.sidebar.radio("Menü", ["Hastalarım", "Yeni Analiz"])
    
    if page == "Hastalarım":
        st.header("📋 Kayıtlı Hastalar")
        p_df = pd.DataFrame(patient_sheet.get_all_records())
        if not p_df.empty:
            my_patients = p_df[p_df['sahip'] == st.session_state['user']]
            if not my_patients.empty:
                for idx, row in my_patients.iterrows():
                    with st.expander(f"👤 {row['hasta_adi']} - {row['tarih']}"):
                        st.write(f"**Yaş:** {row['yas']}")
                        st.write(f"**Klinik Not:** {row['klinik_yorum']}")
                        # Burada detaylı verileri de gösterebilirsin
            else:
                st.info("Henüz bir hasta kaydetmediniz.")
        else:
            st.info("Veritabanı boş.")

    elif page == "Yeni Analiz":
        analysis_form()

# --- 6. ANALİZ FORMU ---
def analysis_form():
    st.header("🧪 Yeni Rorschach Protokolü")
    # (Daha önce yaptığımız tüm analiz kodunu buraya entegre ediyoruz)
    # Örnek olarak sadece isim alıp kaydetme kısmını gösteriyorum:
    h_isim = st.text_input("Hastanın Adı Soyadı")
    h_yas = st.number_input("Yaş", 0, 120)
    h_yorum = st.text_area("Klinik Notlar")
    
    # ... (Diğer tüm kod giriş alanları buraya gelecek) ...

    if st.button("Analizi Kaydet"):
        # Verileri Google Sheets'e gönder
        tarih_simdi = datetime.now().strftime("%d/%m/%Y %H:%M")
        patient_sheet.append_row([st.session_state['user'], h_isim, h_yas, h_yorum, "", "", "", tarih_simdi])
        st.success(f"{h_isim} başarıyla kaydedildi!")

# --- UYGULAMA ÇALIŞTIRICI ---
if not st.session_state['logged_in']:
    auth_page()
else:
    dashboard()

st.markdown('<div class="footer">Kerem Birgül</div>', unsafe_allow_html=True)
