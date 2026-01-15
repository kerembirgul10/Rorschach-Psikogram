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
    from docx.shared import Pt
except ImportError:
    pass

# --- 1. GRUP TANIMLARI ---
GRUP_1 = ["G", "D", "Dd", "Gbl", "Dbl"]
GRUP_2 = ["F", "F+", "F-", "F+-", "FC", "FC'", "Fclob", "C", "C'", "Clob", "CF", "C'F", "ClobF", "K", "Kan", "Kob", "Kp", "E", "EF", "FE"]
GRUP_3 = ["H", "Hd", "(H)", "A", "Ad", "(A)", "Nesne", "Bitki", "Anatomi", "Coğrafya", "Doğa"]

# --- 2. GOOGLE SHEETS BAĞLANTISI ---
@st.cache_resource
def get_gsheet_client():
    creds_info = json.loads(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_info, scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
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
        height: 110px; display: flex; flex-direction: column; justify-content: center; align-items: center;
        border-radius: 10px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: #1a1a1a;
    }
    .metric-label { font-size: 14px; font-weight: bold; margin-bottom: 5px; }
    .metric-value { font-size: 24px; font-weight: 900; }
    .bg-sari { background-color: #FFD93D; border: 2px solid #E2B200; }
    .bg-kirmizi { background-color: #FF6B6B; border: 2px solid #D63031; }
    .bg-mor { background-color: #A29BFE; border: 2px solid #6C5CE7; }
    .kart-wrapper { padding: 20px; border-radius: 15px; margin-bottom: 25px; border: 1px solid rgba(0,0,0,0.1); }
    .kart-title-top { font-size: 18px; font-weight: 800; border-bottom: 2px solid rgba(0,0,0,0.1); margin-bottom: 10px; color: #000000 !important; }
    .footer { position: fixed; left: 0; bottom: 10px; width: 100%; text-align: center; color: #7f8c8d; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user' not in st.session_state: st.session_state['user'] = ""
if 'editing_patient' not in st.session_state: st.session_state['editing_patient'] = None

# --- 4. WORD RAPOR OLUŞTURUCU ---
def create_word_report(h_info, calc, counts, protokol, total_r, b_cards, w_cards, b_reason, w_reason):
    doc = Document()
    doc.add_heading('Rorschach Klinik Analiz Raporu', 0)
    doc.add_heading('Hasta Bilgileri', level=1)
    doc.add_paragraph(f"Ad Soyad: {h_info['name']}\nYaş: {h_info['age']}\nTarih: {h_info['date']}")
    doc.add_heading('Klinik Yorumlar', level=2)
    doc.add_paragraph(h_info['comment'])
    
    doc.add_heading('Kart Tercihleri', level=1)
    doc.add_paragraph(f"Beğenilen: {b_cards} (Nedeni: {b_reason})")
    doc.add_paragraph(f"Beğenilmeyen: {w_cards} (Nedeni: {w_reason})")

    doc.add_heading('Psikogram', level=1)
    doc.add_paragraph(f"Toplam Yanıt (R): {total_r}")
    for k, v in calc.items():
        doc.add_paragraph(f"{k}: %{v:.1f}")
    
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 5. ANALİZ FORMU ---
def analysis_form(edit_data=None):
    st.header(f"{'Düzenle' if edit_data else 'Yeni'} Hasta Protokolü")
    
    c_info1, c_info2 = st.columns([3, 1])
    h_isim = c_info1.text_input("Hastanın Adı Soyadı", value=edit_data.get('hasta_adi', "") if edit_data else "")
    h_yas = c_info2.number_input("Yaş", 0, 120, value=int(edit_data.get('yas', 0)) if edit_data else 0)
    h_yorum = st.text_area("Klinik Yorumlar", value=edit_data.get('klinik_yorum', "") if edit_data else "", height=100)

    st.divider()
    st.subheader("Kart Tercihleri")
    
    def box_selector(label, key_prefix, saved_val):
        st.write(label)
        saved_list = json.loads(saved_val) if saved_val else []
        if f"{key_prefix}_list" not in st.session_state: st.session_state[f"{key_prefix}_list"] = saved_list
        cols = st.columns(10)
        for i in range(1, 11):
            is_sel = i in st.session_state[f"{key_prefix}_list"]
            if cols[i-1].button(str(i), key=f"{key_prefix}_{i}", type="primary" if is_sel else "secondary"):
                if is_sel: st.session_state[f"{key_prefix}_list"].remove(i)
                else: st.session_state[f"{key_prefix}_list"].append(i)
                st.rerun()
        return st.session_state[f"{key_prefix}_list"]

    b_cards = box_selector("En Beğendiği Kartlar", "best", edit_data.get('en_begendigi', "[]") if edit_data else "[]")
    b_reason = st.text_area("Beğenme Nedeni", value=edit_data.get('en_begendigi_neden', "") if edit_data else "")
    w_cards = box_selector("En Beğenmediği Kartlar", "worst", edit_data.get('en_beğenmediği', "[]") if edit_data else "[]")
    w_reason = st.text_area("Beğenmeme Nedeni", value=edit_data.get('en_beğenmediği_neden', "") if edit_data else "")

    st.divider()
    protokol_verileri = []
    renkler = ["#D1E9FF", "#FFD1D1", "#E9D1FF", "#D1D5FF", "#D1FFF9", "#DFFFDE", "#FFFBD1", "#FFE8D1", "#FFD1C2", "#E2E2E2"]
    saved_p = json.loads(edit_data['protokol_verisi']) if (edit_data and 'protokol_verisi' in edit_data) else [{"yanit":"","anket":"","kodlar":""} for _ in range(10)]

    for i in range(1, 11):
        st.markdown(f'<div class="kart-wrapper" style="background-color:{renkler[i-1]};"><span class="kart-title-top">KART {i}</span>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        y = col1.text_area("Yanıt", key=f"y_{i}", value=saved_p[i-1].get('yanit',''))
        a = col2.text_area("Anket", key=f"a_{i}", value=saved_p[i-1].get('anket',''))
        k = st.text_area("Kodlar", key=f"k_{i}", value=saved_p[i-1].get('kodlar',''))
        st.markdown('</div>', unsafe_allow_html=True)
        protokol_verileri.append({"yanit": y, "anket": a, "kodlar": k})

    # BUTONLAR
    btn_col1, btn_col2 = st.columns(2)
    save_clicked = btn_col1.button("Sadece Kaydet")
    calc_clicked = btn_col2.button("Psikogramı Hesapla")

    if save_clicked or calc_clicked:
        tarih = datetime.now().strftime("%d/%m/%Y %H:%M")
        new_row = [st.session_state['user'], h_isim, h_yas, h_yorum, json.dumps(b_cards), json.dumps(w_cards), json.dumps(protokol_verileri), tarih, b_reason, w_reason]
        
        if edit_data:
            cell = patient_sheet.find(edit_data['hasta_adi']); patient_sheet.update(f'A{cell.row}:J{cell.row}', [new_row])
        else:
            patient_sheet.append_row(new_row)
        st.success("Veriler Sisteme Kaydedildi.")

    if calc_clicked:
        total_r = 0; r_8910 = 0; all_codes = []
        for i, d in enumerate(protokol_verileri, 1):
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
            calc = {"%G": (counts["G"]/total_r)*100, "%D": (counts["D"]/total_r)*100, "%F": (sum(counts[k] for k in ["F", "F+", "F-", "F+-"])/total_r)*100, "%A": ((counts["A"]+counts["Ad"])/total_r)*100, "%H": ((counts["H"]+counts["Hd"])/total_r)*100, "RC": (r_8910/total_r)*100}
            p_tri = (counts.get("FC",0)+counts.get("FC'",0)+counts.get("Fclob",0))*0.5 + (counts.get("CF",0)+counts.get("C'F",0)+counts.get("ClobF",0))*1 + (counts.get("C",0)+counts.get("C'",0)+counts.get("Clob",0))*1.5
            calc["TRI"] = (counts["K"]/p_tri)*100 if p_tri > 0 else 0

            st.subheader(f"Analiz (R: {total_r})")
            m_cols = st.columns(4)
            m_cols[0].markdown(f'<div class="metric-container bg-sari"><div class="metric-label">%G / %D</div><div class="metric-value">%{calc["%G"]:.0f} / %{calc["%D"]:.0f}</div></div>', unsafe_allow_html=True)
            m_cols[1].markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">%F</div><div class="metric-value">%{calc["%F"]:.0f}</div></div>', unsafe_allow_html=True)
            m_cols[2].markdown(f'<div class="metric-container bg-mor"><div class="metric-label">%A / %H</div><div class="metric-value">%{calc["%A"]:.0f} / %{calc["%H"]:.0f}</div></div>', unsafe_allow_html=True)
            m_cols[3].markdown(f'<div class="metric-container bg-sari"><div class="metric-label">TRI / RC</div><div class="metric-value">%{calc["TRI"]:.0f} / %{calc["RC"]:.0f}</div></div>', unsafe_allow_html=True)

            st.write("**Kod Dağılımı:**")
            for g_n, g_l in [("Lokalizasyon", GRUP_1), ("Belirleyiciler", GRUP_2), ("İçerik", GRUP_3)]:
                st.write(f"**{g_n}:** " + " | ".join([f"{k}: {counts[k]}" for k in g_l if counts[k] > 0]))

            # WORD İNDİR
            report = create_word_report({'name': h_isim, 'age': h_yas, 'comment': h_yorum, 'date': tarih}, calc, counts, protokol_verileri, total_r, b_cards, w_cards, b_reason, w_reason)
            st.download_button("📄 Word Olarak İndir", report, f"{h_isim}_Rorschach.docx")
        else:
            st.warning("Hesaplama için kod girilmedi.")

# --- 6. NAVİGASYON ---
if not st.session_state['logged_in']:
    st.title("Rorschach Klinik Panel")
    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")
    if st.button("Giriş"):
        df = pd.DataFrame(user_sheet.get_all_records())
        if u in df['kullanici_adi'].values and str(p) == str(df[df['kullanici_adi']==u]['sifre'].values[0]):
            st.session_state['logged_in'] = True; st.session_state['user'] = u; st.rerun()
else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    menu = st.sidebar.radio("Menü", ["Hastalarım", "Yeni Hasta Ekle"])
    if st.sidebar.button("Çıkış"): st.session_state['logged_in'] = False; st.rerun()

    if menu == "Hastalarım":
        st.header("Hastalarım")
        search = st.text_input("Hasta Ara...")
        data = pd.DataFrame(patient_sheet.get_all_records())
        my_p = data[data['sahip'] == st.session_state['user']]
        if not my_p.empty:
            filtered = my_p[my_p['hasta_adi'].str.contains(search, case=False)]
            for _, row in filtered.iterrows():
                if st.button(row['hasta_adi'], key=f"p_{_}"): st.session_state['editing_patient'] = row.to_dict()
            if st.session_state['editing_patient']:
                st.divider()
                if st.button("Kapat"): st.session_state['editing_patient'] = None; st.rerun()
                analysis_form(st.session_state['editing_patient'])
        else: st.info("Kayıt yok.")
    elif menu == "Yeni Hasta Ekle":
        st.session_state['editing_patient'] = None; analysis_form()

st.markdown('<div class="footer">Kerem Birgül</div>', unsafe_allow_html=True)
