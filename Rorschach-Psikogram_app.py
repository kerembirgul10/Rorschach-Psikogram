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
    
    # Google Sheet Adı (Seninkine göre kontrol et!)
    SHEET_NAME = "Rorschach_Veritabani" 
    sheet = client.open(SHEET_NAME)
    user_sheet = sheet.worksheet("Kullanıcılar")
    patient_sheet = sheet.worksheet("Hastalar")
except Exception as e:
    st.error(f"Veritabanı bağlantı hatası: {e}")
    st.stop()

# --- 2. TASARIM VE STİLLER ---
st.set_page_config(page_title="Rorschach Klinik Panel", layout="wide")

st.markdown("""
    <style>
    .metric-container {
        height: 110px; display: flex; flex-direction: column;
        justify-content: center; align-items: center;
        border-radius: 10px; margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: #1a1a1a;
    }
    .metric-label { font-size: 16px; font-weight: bold; margin-bottom: 5px; }
    .metric-value { font-size: 26px; font-weight: 900; }
    .bg-sari { background-color: #FFD93D; border: 2px solid #E2B200; }
    .bg-kirmizi { background-color: #FF6B6B; border: 2px solid #D63031; }
    .bg-mor { background-color: #A29BFE; border: 2px solid #6C5CE7; }
    
    .kart-wrapper {
        padding: 20px; border-radius: 15px; margin-top: 10px; margin-bottom: 30px;
        border: 1px solid rgba(0,0,0,0.1); box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    .kart-title-top {
        font-size: 20px; font-weight: 800; margin-bottom: 15px; color: #2c3e50;
        border-bottom: 2px solid rgba(0,0,0,0.1); padding-bottom: 5px; display: block;
    }
    .footer { position: fixed; left: 0; bottom: 10px; width: 100%; text-align: center; color: #7f8c8d; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. OTURUM DURUMU ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = ""

# --- 4. GİRİŞ VE KAYIT SAYFASI ---
def auth_page():
    st.title("🧠 Rorschach Klinik Panel")
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    with tab1:
        login_user = st.text_input("Kullanıcı Adı", key="l_user")
        login_pw = st.text_input("Şifre", type="password", key="l_pw")
        if st.button("Sisteme Giriş"):
            data = user_sheet.get_all_records()
            if data:
                users_df = pd.DataFrame(data)
                users_df.columns = users_df.columns.str.strip()
                if login_user in users_df['kullanici_adi'].values:
                    user_row = users_df[users_df['kullanici_adi'] == login_user]
                    if str(login_pw) == str(user_row['sifre'].values[0]):
                        st.session_state['logged_in'] = True
                        st.session_state['user'] = login_user
                        st.rerun()
                    else: st.error("Hatalı şifre.")
                else: st.error("Kullanıcı bulunamadı.")
            else: st.error("Önce Kayıt Olun.")

    with tab2:
        new_user = st.text_input("Kullanıcı Adı Belirle", key="r_user")
        new_pw = st.text_input("Şifre Belirle", type="password", key="r_pw")
        new_name = st.text_input("Adınız Soyadınız", key="r_name")
        if st.button("Kayıt Ol"):
            data = user_sheet.get_all_records()
            users_df = pd.DataFrame(data) if data else pd.DataFrame(columns=['kullanici_adi', 'sifre', 'isim'])
            if new_user in users_df['kullanici_adi'].values:
                st.warning("Bu kullanıcı adı dolu.")
            else:
                user_sheet.append_row([new_user, str(new_pw), new_name])
                st.success("Kayıt başarılı! Giriş yapabilirsiniz.")

# --- 5. ANA PANEL VE ANALİZ FORMU ---
def dashboard():
    st.sidebar.title(f"👤 {st.session_state['user']}")
    menu = st.sidebar.radio("Sayfalar", ["📁 Hastalarım", "➕ Yeni Hasta Ekle"])
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state['logged_in'] = False
        st.rerun()

    if menu == "📁 Hastalarım":
        st.header("Kayıtlı Protokoller")
        data = patient_sheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            my_patients = df[df['sahip'] == st.session_state['user']]
            if not my_patients.empty:
                for idx, p in my_patients.iterrows():
                    with st.expander(f"📄 {p['hasta_adi']} ({p['tarih']})"):
                        st.write(f"**Yaş:** {p['yas']}")
                        st.write(f"**Klinik Yorum:** {p['klinik_yorum']}")
            else: st.info("Henüz bir protokol kaydetmediniz.")
        else: st.info("Veritabanı boş.")

    elif menu == "➕ Yeni Hasta Ekle":
        analysis_form()

def analysis_form():
    st.header("🧪 Yeni Analiz ve Protokol Oluştur")
    
    # 1. BÖLÜM: BİLGİLER
    c1, c2 = st.columns([3, 1])
    with c1: h_isim = st.text_input("Hastanın Adı Soyadı")
    with c2: h_yas = st.number_input("Yaş", 0, 120)
    h_yorum = st.text_area("Görüşme Hakkında Klinik Yorumlar", height=100)

    # 2. BÖLÜM: KART TERCİHLERİ
    st.divider()
    st.write("**Kart Tercihleri**")
    def kt_arayuzu(label, prefix):
        st.write(label)
        cols = st.columns(10); s = []
        for i in range(1, 11):
            with cols[i-1]:
                if st.checkbox(f"{i}", key=f"{prefix}_{i}"): s.append(i)
        return s
    
    b_cards = kt_arayuzu("En Beğendiği", "b")
    b_reason = st.text_area("Beğenme Nedeni", key="br")
    w_cards = kt_arayuzu("En Beğenmediği", "w")
    w_reason = st.text_area("Beğenmeme Nedeni", key="wr")

    # 3. BÖLÜM: PROTOKOL
    st.divider()
    protokol_verileri = []
    renkler = ["#D1E9FF", "#FFD1D1", "#E9D1FF", "#D1D5FF", "#D1FFF9", "#DFFFDE", "#FFFBD1", "#FFE8D1", "#FFD1C2", "#E2E2E2"]
    
    for i in range(1, 11):
        st.markdown(f'<div class="kart-wrapper" style="background-color:{renkler[i-1]};"><span class="kart-title-top">KART {i}</span>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1: yanit = st.text_area("Yanıt", key=f"y_{i}")
        with col2: anket = st.text_area("Anket", key=f"a_{i}")
        kodlar = st.text_area("Kodlar (Noktalı virgülle ayırın)", key=f"k_{i}", placeholder="G F+ A; D F- H")
        st.markdown('</div>', unsafe_allow_html=True)
        protokol_verileri.append({"yanit": yanit, "anket": anket, "kodlar": kodlar})

    # 4. BÖLÜM: ANALİZ VE KAYIT
    if st.button("Analizi Tamamla, Kaydet ve Word Oluştur"):
        total_r = 0; r_8910 = 0; all_codes = []
        for i, data in enumerate(protokol_verileri, 1):
            if data["kodlar"].strip():
                resps = data["kodlar"].replace(';', '\n').split('\n')
                for r in resps:
                    clean = r.strip()
                    if not clean or clean.lower() == "reddetme": continue
                    total_r += 1
                    if i in [8, 9, 10]: r_8910 += 1
                    for k in clean.replace(",", " ").split():
                        if k: all_codes.append(k)

        if total_r > 0:
            counts = Counter(all_codes)
            calc = {
                "%G": (counts["G"]/total_r)*100, "%D": (counts["D"]/total_r)*100,
                "%F": (sum(counts[k] for k in ["F", "F+", "F-", "F+-"])/total_r)*100,
                "%A": ((counts["A"]+counts["Ad"])/total_r)*100,
                "%H": ((counts["H"]+counts["Hd"])/total_r)*100,
                "RC": (r_8910/total_r)*100
            }
            
            # Veritabanına Kaydet
            tarih = datetime.now().strftime("%d/%m/%Y %H:%M")
            patient_sheet.append_row([st.session_state['user'], h_isim, h_yas, h_yorum, str(b_cards), str(w_cards), json.dumps(protokol_verileri), tarih])
            st.success("Veriler veritabanına kaydedildi!")

            # Analiz Özeti Göster
            st.subheader(f"Analiz Özeti (R: {total_r})")
            res_cols = st.columns(4)
            res_cols[0].markdown(f'<div class="metric-container bg-sari"><div class="metric-label">%G / %D</div><div class="metric-value">%{calc["%G"]:.0f} / %{calc["%D"]:.0f}</div></div>', unsafe_allow_html=True)
            res_cols[1].markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">%F</div><div class="metric-value">%{calc["%F"]:.0f}</div></div>', unsafe_allow_html=True)
            res_cols[2].markdown(f'<div class="metric-container bg-mor"><div class="metric-label">%A / %H</div><div class="metric-value">%{calc["%A"]:.0f} / %{calc["%H"]:.0f}</div></div>', unsafe_allow_html=True)
            res_cols[3].markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">RC</div><div class="metric-value">%{calc["RC"]:.0f}</div></div>', unsafe_allow_html=True)

            # WORD OLUŞTURMA
            doc = Document()
            doc.add_heading('Rorschach Klinik Raporu', 0)
            doc.add_paragraph(f"Hasta: {h_isim} | Tarih: {tarih}")
            doc.add_heading('Klinik Yorum', level=1); doc.add_paragraph(h_yorum)
            # (Word kısmının detayları buraya eklenebilir)
            bio = BytesIO(); doc.save(bio)
            st.download_button("📄 Word Raporunu İndir", bio.getvalue(), f"{h_isim}_Rapor.docx")
        else:
            st.warning("Analiz için geçerli kod girilmedi.")

# --- ÇALIŞTIR ---
if not st.session_state['logged_in']:
    auth_page()
else:
    dashboard()

st.markdown('<div class="footer">Kerem Birgül</div>', unsafe_allow_html=True)
