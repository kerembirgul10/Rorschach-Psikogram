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

# --- 1. GRUP TANIMLARI ---
GRUP_1 = ["G", "D", "Dd", "Gbl", "Dbl"]
GRUP_2 = ["F", "F+", "F-", "F+-", "FC", "FC'", "Fclob", "C", "C'", "Clob", "CF", "C'F", "ClobF", "K", "Kan", "Kob", "Kp", "E", "EF", "FE"]
GRUP_3 = ["H", "Hd", "(H)", "A", "Ad", "(A)", "Nesne", "Bitki", "Anatomi", "Coğrafya", "Doğa"]

# --- 2. GOOGLE SHEETS BAĞLANTISI (Önbelleğe Alındı) ---
@st.cache_resource
def get_gsheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_info = json.loads(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    return gspread.authorize(creds)

try:
    client = get_gsheet_client()
    sheet = client.open("Rorschach_Veritabani")
    user_sheet = sheet.worksheet("Kullanıcılar")
    patient_sheet = sheet.worksheet("Hastalar")
except Exception as e:
    st.error(f"Bağlantı hatası: {e}")
    st.stop()

# --- 3. TASARIM ---
st.set_page_config(page_title="Rorschach Klinik Panel", layout="wide")
st.markdown("""
    <style>
    textarea { resize: none !important; border: 1px solid #ced4da !important; border-radius: 5px !important; }
    .metric-container {
        height: 110px; display: flex; flex-direction: column;
        justify-content: center; align-items: center;
        border-radius: 10px; margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: #1a1a1a;
    }
    .metric-label { font-size: 14px; font-weight: bold; margin-bottom: 5px; }
    .metric-value { font-size: 24px; font-weight: 900; }
    .bg-sari { background-color: #FFD93D; border: 2px solid #E2B200; }
    .bg-kirmizi { background-color: #FF6B6B; border: 2px solid #D63031; }
    .bg-mor { background-color: #A29BFE; border: 2px solid #6C5CE7; }
    .kart-wrapper { padding: 20px; border-radius: 15px; margin-bottom: 25px; border: 1px solid rgba(0,0,0,0.1); }
    .kart-title-top { font-size: 18px; font-weight: 800; border-bottom: 2px solid rgba(0,0,0,0.1); margin-bottom: 10px; color: #000000 !important; }
    .footer { position: fixed; left: 0; bottom: 10px; width: 100%; text-align: center; color: #7f8c8d; font-size: 13px; }
    
    /* Seçili butonu kırmızı yapma simülasyonu */
    div[data-baseweb="tag"] { background-color: #FF6B6B !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user' not in st.session_state: st.session_state['user'] = ""

# --- 4. GİRİŞ VE KAYIT ---
def auth_page():
    st.title("Rorschach Klinik Panel")
    t1, t2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    with t1:
        u = st.text_input("Kullanıcı Adı", key="login_u")
        p = st.text_input("Şifre", type="password", key="login_p")
        if st.button("Sisteme Giriş"):
            df = pd.DataFrame(user_sheet.get_all_records())
            if u in df['kullanici_adi'].values:
                if str(p) == str(df[df['kullanici_adi']==u]['sifre'].values[0]):
                    st.session_state['logged_in'] = True; st.session_state['user'] = u; st.rerun()
                else: st.error("Hatalı şifre.")
            else: st.error("Kullanıcı bulunamadı.")
    with t2:
        nu = st.text_input("Yeni Kullanıcı Adı", key="reg_u")
        np = st.text_input("Şifre Belirle", type="password", key="reg_p")
        nn = st.text_input("Ad Soyad", key="reg_n")
        if st.button("Kaydol"):
            user_sheet.append_row([nu, str(np), nn]); st.success("Kayıt başarılı.")

# --- 5. ANALİZ FORMU ---
def analysis_form(edit_data=None):
    mode = "Düzenle" if edit_data else "Yeni"
    st.header(f"{mode} Hasta Protokolü")
    
    # Form kullanarak her tıklamada yenilemeyi önlüyoruz
    with st.form("main_form"):
        d_name = edit_data.get('hasta_adi', "") if edit_data else ""
        d_age = int(edit_data.get('yas', 0)) if edit_data else 0
        d_comment = edit_data.get('klinik_yorum', "") if edit_data else ""
        
        c1, c2 = st.columns([3, 1])
        h_isim = c1.text_input("Hastanın Adı Soyadı", value=d_name)
        h_yas = c2.number_input("Yaş", 0, 120, value=d_age)
        h_yorum = st.text_area("Klinik Yorumlar", value=d_comment, height=100)

        st.divider()
        st.subheader("Kart Tercihleri")
        
        # Yenileme yapmayan hızlı seçim alanı
        b_cards = st.multiselect("En Beğendiği Kartlar", options=list(range(1,11)), 
                                default=json.loads(edit_data.get('en_begendigi', "[]")) if edit_data else [])
        b_reason = st.text_area("Beğenme Nedeni", value=edit_data.get('en_begendigi_neden', "") if edit_data else "")
        
        w_cards = st.multiselect("En Beğenmediği Kartlar", options=list(range(1,11)), 
                                default=json.loads(edit_data.get('en_beğenmediği', "[]")) if edit_data else [])
        w_reason = st.text_area("Beğenmeme Nedeni", value=edit_data.get('en_beğenmediği_neden', "") if edit_data else "")

        st.divider()
        st.write("**Kart Protokolü**")
        renkler = ["#D1E9FF", "#FFD1D1", "#E9D1FF", "#D1D5FF", "#D1FFF9", "#DFFFDE", "#FFFBD1", "#FFE8D1", "#FFD1C2", "#E2E2E2"]
        saved_p = json.loads(edit_data['protokol_verisi']) if (edit_data and 'protokol_verisi' in edit_data) else [{"yanit":"","anket":"","kodlar":""} for _ in range(10)]

        form_data = []
        for i in range(1, 11):
            st.markdown(f'<div class="kart-wrapper" style="background-color:{renkler[i-1]};"><span class="kart-title-top">KART {i}</span>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            y = col1.text_area("Yanıt", key=f"y_{i}", value=saved_p[i-1].get('yanit',''))
            a = col2.text_area("Anket", key=f"a_{i}", value=saved_p[i-1].get('anket',''))
            k = st.text_area("Kodlar (Enter ile ayırın)", key=f"k_{i}", value=saved_p[i-1].get('kodlar',''))
            form_data.append({"yanit": y, "anket": a, "kodlar": k})
            st.markdown('</div>', unsafe_allow_html=True)

        submitted = st.form_submit_button("Analizi Kaydet ve Sonuçları Gör")

    if submitted:
        total_r = 0; r_8910 = 0; all_codes = []
        for i, d in enumerate(form_data, 1):
            if d["kodlar"].strip():
                lines = d["kodlar"].replace(';', '\n').split('\n')
                for line in lines:
                    line = line.strip()
                    if not line or line.lower() == "reddetme": continue
                    total_r += 1
                    if i in [8, 9, 10]: r_8910 += 1
                    for code in line.replace(",", " ").split(): all_codes.append(code)
        
        if total_r > 0:
            counts = Counter(all_codes)
            calc = {
                "%G": (counts["G"]/total_r)*100, "%D": (counts["D"]/total_r)*100,
                "%F": (sum(counts[k] for k in ["F", "F+", "F-", "F+-"])/total_r)*100,
                "%A": ((counts["A"]+counts["Ad"])/total_r)*100,
                "%H": ((counts["H"]+counts["Hd"])/total_r)*100, "RC": (r_8910/total_r)*100
            }
            p_tri = (counts.get("FC",0)+counts.get("FC'",0)+counts.get("Fclob",0))*0.5 + (counts.get("CF",0)+counts.get("C'F",0)+counts.get("ClobF",0))*1 + (counts.get("C",0)+counts.get("C'",0)+counts.get("Clob",0))*1.5
            calc["TRI"] = (counts["K"]/p_tri)*100 if p_tri > 0 else 0

            # Kayıt işlemi
            tarih = datetime.now().strftime("%d/%m/%Y %H:%M")
            new_row = [st.session_state['user'], h_isim, h_yas, h_yorum, json.dumps(b_cards), json.dumps(w_cards), json.dumps(form_data), tarih, b_reason, w_reason]
            if edit_data:
                cell = patient_sheet.find(edit_data['hasta_adi']); patient_sheet.update(f'A{cell.row}:J{cell.row}', [new_row])
            else: patient_sheet.append_row(new_row)
            
            # Sonuçları göster
            st.success("Veriler kaydedildi!")
            st.subheader(f"Analiz Sonuçları (R: {total_r})")
            m_cols = st.columns(4)
            m_cols[0].markdown(f'<div class="metric-container bg-sari"><div class="metric-label">%G / %D</div><div class="metric-value">%{calc["%G"]:.0f} / %{calc["%D"]:.0f}</div></div>', unsafe_allow_html=True)
            m_cols[1].markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">%F</div><div class="metric-value">%{calc["%F"]:.0f}</div></div>', unsafe_allow_html=True)
            m_cols[2].markdown(f'<div class="metric-container bg-mor"><div class="metric-label">%A / %H</div><div class="metric-value">%{calc["%A"]:.0f} / %{calc["%H"]:.0f}</div></div>', unsafe_allow_html=True)
            m_cols[3].markdown(f'<div class="metric-container bg-sari"><div class="metric-label">TRI / RC</div><div class="metric-value">%{calc["TRI"]:.0f} / %{calc["RC"]:.0f}</div></div>', unsafe_allow_html=True)

            st.subheader("Kod Frekansları")
            for grup_adi, grup_liste in [("Lokalizasyon", GRUP_1), ("Belirleyiciler", GRUP_2), ("İçerik", GRUP_3)]:
                st.write(f"**{grup_adi}:** " + " | ".join([f"{k}: {counts[k]}" for k in grup_liste if counts[k] > 0]))
        else: st.warning("Kod girilmedi.")

# --- 6. NAVİGASYON ---
if not st.session_state['logged_in']: auth_page()
else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    menu = st.sidebar.radio("Menü", ["Hastalarım", "Yeni Hasta Ekle"])
    if st.sidebar.button("Çıkış"): st.session_state['logged_in'] = False; st.rerun()

    if menu == "Hastalarım":
        data = patient_sheet.get_all_records()
        df_p = pd.DataFrame(data)
        my_p = df_p[df_p['sahip'] == st.session_state['user']]
        if not my_p.empty:
            p_list = [f"{r['hasta_adi']} ({r['tarih']})" for _, r in my_p.iterrows()]
            selected_p_str = st.selectbox("Bir hasta seçin:", ["Seçiniz..."] + p_list)
            if selected_p_str != "Seçiniz...":
                selected_name = selected_p_str.split(" (")[0]
                selected_row = my_p[my_p['hasta_adi'] == selected_name].iloc[0]
                analysis_form(selected_row.to_dict())
        else: st.info("Kayıt bulunamadı.")
    elif menu == "Yeni Hasta Ekle":
        analysis_form()

st.markdown('<div class="footer">Kerem Birgül</div>', unsafe_allow_html=True)
