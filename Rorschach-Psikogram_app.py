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

# --- 1. GOOGLE SHEETS BAĞLANTISI ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_info = json.loads(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    client = gspread.authorize(creds)
    
    SHEET_NAME = "Rorschach_Veritabani" 
    sheet = client.open(SHEET_NAME)
    user_sheet = sheet.worksheet("Kullanıcılar")
    patient_sheet = sheet.worksheet("Hastalar")
except Exception as e:
    st.error(f"Veritabanı bağlantı hatası: {e}")
    st.stop()

# --- 2. TASARIM ---
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
    .metric-label { font-size: 16px; font-weight: bold; margin-bottom: 5px; }
    .metric-value { font-size: 26px; font-weight: 900; }
    .bg-sari { background-color: #FFD93D; border: 2px solid #E2B200; }
    .bg-kirmizi { background-color: #FF6B6B; border: 2px solid #D63031; }
    .bg-mor { background-color: #A29BFE; border: 2px solid #6C5CE7; }
    .kart-wrapper { padding: 20px; border-radius: 15px; margin-bottom: 25px; border: 1px solid rgba(0,0,0,0.1); }
    .kart-title-top { font-size: 18px; font-weight: 800; border-bottom: 2px solid rgba(0,0,0,0.1); margin-bottom: 10px; }
    .footer { position: fixed; left: 0; bottom: 10px; width: 100%; text-align: center; color: #7f8c8d; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. OTURUM DURUMU ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user' not in st.session_state: st.session_state['user'] = ""
if 'editing_patient' not in st.session_state: st.session_state['editing_patient'] = None

# --- 4. GİRİŞ VE KAYIT SAYFASI ---
def auth_page():
    st.title("🧠 Rorschach Klinik Panel")
    t1, t2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    with t1:
        u = st.text_input("Kullanıcı Adı", key="login_u")
        p = st.text_input("Şifre", type="password", key="login_p")
        if st.button("Sisteme Giriş"):
            df = pd.DataFrame(user_sheet.get_all_records())
            df.columns = df.columns.str.strip()
            if u in df['kullanici_adi'].values:
                correct_p = str(df[df['kullanici_adi']==u]['sifre'].values[0])
                if str(p) == correct_p:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = u
                    st.rerun()
                else: st.error("Hatalı şifre.")
            else: st.error("Kullanıcı bulunamadı.")
    with t2:
        nu = st.text_input("Yeni Kullanıcı Adı", key="reg_u")
        np = st.text_input("Şifre Belirle", type="password", key="reg_p")
        nn = st.text_input("Ad Soyad", key="reg_n")
        if st.button("Kaydol"):
            user_sheet.append_row([nu, str(np), nn])
            st.success("Kaydınız başarıyla oluşturuldu! Şimdi giriş yapabilirsiniz.")

# --- 5. WORD RAPOR FONKSİYONU ---
def create_word_report(h_info, calc_results, freq_results, protokol_list, total_r, preferences):
    doc = Document()
    doc.add_heading('Rorschach Klinik Analiz Raporu', 0)
    doc.add_heading('1. Hasta Bilgileri', level=1)
    doc.add_paragraph(f"Ad Soyad: {h_info['name']}\nYaş: {h_info['age']}\nTarih: {h_info['date']}")
    doc.add_heading('Klinik Yorumlar:', level=2)
    doc.add_paragraph(h_info['comment'])

    doc.add_heading('2. Kart Tercihleri', level=1)
    doc.add_paragraph(f"En Beğenilen Kartlar: {preferences['begendigi']}")
    doc.add_paragraph(f"Beğenme Nedeni: {preferences['b_neden']}")
    doc.add_paragraph(f"En Beğenilmeyen Kartlar: {preferences['beğenmediği']}")
    doc.add_paragraph(f"Beğenmeme Nedeni: {preferences['w_neden']}")

    doc.add_heading('3. Test Protokolü', level=1)
    table = doc.add_table(rows=1, cols=4); table.style = 'Table Grid'
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text, hdr[3].text = 'Kart', 'Yanıt', 'Anket', 'Kodlar'
    for i, p in enumerate(protokol_list, 1):
        row = table.add_row().cells
        row[0].text, row[1].text, row[2].text, row[3].text = str(i), str(p['yanit']), str(p['anket']), str(p['kodlar'])

    doc.add_heading('4. Psikogram Verileri', level=1)
    doc.add_paragraph(f"Toplam Yanıt Sayısı (R): {total_r}")
    for k, v in calc_results.items():
        doc.add_paragraph(f"{k}: %{v:.1f}")
    
    doc.add_heading('Kod Frekansları:', level=2)
    doc.add_paragraph(", ".join([f"{k}: {v}" for k, v in freq_results.items()]))
    bio = BytesIO(); doc.save(bio); return bio.getvalue()

# --- 6. ANALİZ FORMU ---
def analysis_form(edit_data=None):
    st.header(f"🧪 {'Düzenle' if edit_data else 'Yeni'} Protokol")
    
    d_name = edit_data.get('hasta_adi', "") if edit_data else ""
    d_age = int(edit_data.get('yas', 0)) if edit_data else 0
    d_comment = edit_data.get('klinik_yorum', "") if edit_data else ""
    d_b_neden = edit_data.get('en_begendigi_neden', "") if edit_data else ""
    d_w_neden = edit_data.get('en_beğenmediği_neden', "") if edit_data else ""
    
    c1, c2 = st.columns([3, 1])
    h_isim = c1.text_input("Hastanın Adı Soyadı", value=d_name)
    h_yas = c2.number_input("Yaş", 0, 120, value=d_age)
    h_yorum = st.text_area("Klinik Yorumlar", value=d_comment, height=100)

    # --- KART TERCİHLERİ ---
    st.divider(); st.subheader("🖼️ Kart Tercihleri")
    def get_prefs(label, prefix, saved_val):
        st.write(label)
        try: saved_list = json.loads(saved_val) if saved_val else []
        except: saved_list = []
        cols = st.columns(10); selected = []
        for i in range(1, 11):
            with cols[i-1]:
                if st.checkbox(f"{i}", key=f"{prefix}_{i}", value=(i in saved_list)): selected.append(i)
        return selected

    b_cards = get_prefs("En Beğendiği Kartlar", "b", edit_data.get('en_begendigi', "[]") if edit_data else "[]")
    b_reason = st.text_area("Beğenme Nedeni", value=d_b_neden, key="br_area")
    w_cards = get_prefs("En Beğenilmeyen Kartlar", "w", edit_data.get('en_beğenmediği', "[]") if edit_data else "[]")
    w_reason = st.text_area("Beğenmeme Nedeni", value=d_w_neden, key="wr_area")

    # --- PROTOKOL ---
    st.divider(); protokol_verileri = []
    renkler = ["#D1E9FF", "#FFD1D1", "#E9D1FF", "#D1D5FF", "#D1FFF9", "#DFFFDE", "#FFFBD1", "#FFE8D1", "#FFD1C2", "#E2E2E2"]
    try: saved_p = json.loads(edit_data['protokol_verisi']) if edit_data else [{"yanit":"","anket":"","kodlar":""} for _ in range(10)]
    except: saved_p = [{"yanit":"","anket":"","kodlar":""} for _ in range(10)]

    for i in range(1, 11):
        st.markdown(f'<div class="kart-wrapper" style="background-color:{renkler[i-1]};"><span class="kart-title-top">KART {i}</span>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        v_y = col1.text_area("Yanıt", key=f"y_{i}", value=saved_p[i-1].get('yanit',''))
        v_a = col2.text_area("Anket", key=f"a_{i}", value=saved_p[i-1].get('anket',''))
        v_k = st.text_area("Kodlar (G F+ A)", key=f"k_{i}", value=saved_p[i-1].get('kodlar',''))
        st.markdown('</div>', unsafe_allow_html=True)
        protokol_verileri.append({"yanit": v_y, "anket": v_a, "kodlar": v_k})

    if st.button("Verileri Kaydet ve Analiz Et"):
        total_r = 0; all_codes = []
        for i, d in enumerate(protokol_verileri, 1):
            if d["kodlar"].strip():
                items = d["kodlar"].replace(';', ' ').replace(',', ' ').split()
                for item in items:
                    if item.lower() != "reddetme":
                        total_r += 1; all_codes.append(item)
        
        if total_r > 0:
            counts = Counter(all_codes)
            calc = {"%G": (counts["G"]/total_r)*100, "%D": (counts["D"]/total_r)*100, "%F": (sum(counts[k] for k in ["F", "F+", "F-", "F+-"])/total_r)*100, "%A": ((counts["A"]+counts["Ad"])/total_r)*100}
            
            tarih = datetime.now().strftime("%d/%m/%Y %H:%M")
            new_row = [st.session_state['user'], h_isim, h_yas, h_yorum, json.dumps(b_cards), json.dumps(w_cards), json.dumps(protokol_verileri), tarih, b_reason, w_reason]
            
            if edit_data:
                cell = patient_sheet.find(edit_data['hasta_adi'])
                patient_sheet.update(f'A{cell.row}:J{cell.row}', [new_row])
                st.success("Kayıt güncellendi!")
            else:
                patient_sheet.append_row(new_row)
                st.success("Kayıt oluşturuldu!")

            # Analiz Paneli
            res_cols = st.columns(4)
            res_cols[0].markdown(f'<div class="metric-container bg-sari"><div class="metric-label">%G</div><div class="metric-value">%{calc["%G"]:.0f}</div></div>', unsafe_allow_html=True)
            res_cols[1].markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">%F</div><div class="metric-value">%{calc["%F"]:.0f}</div></div>', unsafe_allow_html=True)
            res_cols[2].markdown(f'<div class="metric-container bg-mor"><div class="metric-label">%A</div><div class="metric-value">%{calc["%A"]:.0f}</div></div>', unsafe_allow_html=True)
            res_cols[3].markdown(f'<div class="metric-container bg-sari"><div class="metric-label">R</div><div class="metric-value">{total_r}</div></div>', unsafe_allow_html=True)

            st.subheader("📈 Kod Frekansları")
            st.table(pd.DataFrame(counts.items(), columns=['Kod', 'Adet']).T)

            prefs = {"begendigi": b_cards, "b_neden": b_reason, "beğenmediği": w_cards, "w_neden": w_reason}
            report = create_word_report({'name': h_isim, 'age': h_yas, 'comment': h_yorum, 'date': tarih}, calc, counts, protokol_verileri, total_r, prefs)
            st.download_button("📄 Word Raporu İndir", report, f"{h_isim}_Rapor.docx")
        else: st.warning("Kod girilmedi.")

# --- 7. ANA ÇALIŞTIRICI ---
if not st.session_state['logged_in']:
    auth_page()
else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    menu = st.sidebar.radio("Menü", ["📁 Hastalarım", "➕ Yeni Hasta Ekle"])
    if st.sidebar.button("Güvenli Çıkış"): st.session_state['logged_in'] = False; st.rerun()

    if menu == "📁 Hastalarım":
        st.header("Kayıtlı Protokoller")
        df_p = pd.DataFrame(patient_sheet.get_all_records())
        df_p.columns = df_p.columns.str.strip()
        my_p = df_p[df_p['sahip'] == st.session_state['user']]
        if not my_p.empty:
            for idx, row in my_p.iterrows():
                if st.button(f"👤 {row['hasta_adi']} ({row['tarih']})", key=f"btn_{idx}"):
                    st.session_state['editing_patient'] = row.to_dict()
            if st.session_state['editing_patient']:
                st.divider()
                if st.button("❌ Kapat"): st.session_state['editing_patient'] = None; st.rerun()
                analysis_form(st.session_state['editing_patient'])
        else: st.info("Henüz hasta kaydınız yok.")
    elif menu == "➕ Yeni Hasta Ekle":
        st.session_state['editing_patient'] = None
        analysis_form()

st.markdown('<div class="footer">Kerem Birgül</div>', unsafe_allow_html=True)
