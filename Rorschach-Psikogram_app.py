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
    from docx.shared import Pt, Inches
    from docx.enum.table import WD_TABLE_ALIGNMENT
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

# --- 4. ANALİZ VE WORD FONKSİYONU ---
def create_word_report(h_info, calc_results, protokol_list, total_r):
    doc = Document()
    doc.add_heading('Rorschach Klinik Analiz Raporu', 0)
    
    doc.add_heading('1. Hasta Bilgileri', level=1)
    doc.add_paragraph(f"Ad Soyad: {h_info['name']}\nYaş: {h_info['age']}\nTarih: {h_info['date']}")
    doc.add_heading('Klinik Gözlem ve Yorumlar:', level=2)
    doc.add_paragraph(h_info['comment'])

    doc.add_heading('2. Test Protokolü (Yanıtlar ve Kodlar)', level=1)
    table = doc.add_table(rows=1, cols=4)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Kart'
    hdr_cells[1].text = 'Yanıt'
    hdr_cells[2].text = 'Anket'
    hdr_cells[3].text = 'Kodlar'

    for i, p in enumerate(protokol_list, 1):
        row_cells = table.add_row().cells
        row_cells[0].text = str(i)
        row_cells[1].text = str(p.get('yanit', ''))
        row_cells[2].text = str(p.get('anket', ''))
        row_cells[3].text = str(p.get('kodlar', ''))

    doc.add_heading('3. Psikogram Analiz Sonuçları', level=1)
    doc.add_paragraph(f"Toplam Yanıt Sayısı (R): {total_r}")
    res_table = doc.add_table(rows=0, cols=2)
    res_table.style = 'Table Grid'
    for k, v in calc_results.items():
        row = res_table.add_row().cells
        row[0].text = k
        row[1].text = f"%{v:.0f}"

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 5. ANALİZ FORMU ---
def analysis_form(edit_data=None):
    mode = "Düzenle" if edit_data is not None else "Yeni"
    st.header(f"🧪 {mode} Hasta Protokolü")
    
    default_name = edit_data.get('hasta_adi', "") if edit_data else ""
    default_age = int(edit_data.get('yas', 0)) if edit_data else 0
    default_comment = edit_data.get('klinik_yorum', "") if edit_data else ""
    
    c1, c2 = st.columns([3, 1])
    h_isim = c1.text_input("Hastanın Adı Soyadı", value=default_name)
    h_yas = c2.number_input("Yaş", 0, 120, value=default_age)
    h_yorum = st.text_area("Klinik Yorumlar", value=default_comment, height=100)

    protokol_verileri = []
    renkler = ["#D1E9FF", "#FFD1D1", "#E9D1FF", "#D1D5FF", "#D1FFF9", "#DFFFDE", "#FFFBD1", "#FFE8D1", "#FFD1C2", "#E2E2E2"]
    
    if edit_data and 'protokol_verisi' in edit_data:
        try:
            saved_protokol = json.loads(edit_data['protokol_verisi'])
        except:
            saved_protokol = [{ "yanit": "", "anket": "", "kodlar": "" } for _ in range(10)]
    else:
        saved_protokol = [{ "yanit": "", "anket": "", "kodlar": "" } for _ in range(10)]

    for i in range(1, 11):
        st.markdown(f'<div class="kart-wrapper" style="background-color:{renkler[i-1]};"><span class="kart-title-top">KART {i}</span>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        v_yanit = col1.text_area("Yanıt", key=f"y_{i}", value=saved_protokol[i-1].get('yanit', ''))
        v_anket = col2.text_area("Anket", key=f"a_{i}", value=saved_protokol[i-1].get('anket', ''))
        v_kodlar = st.text_area("Kodlar", key=f"k_{i}", value=saved_protokol[i-1].get('kodlar', ''))
        st.markdown('</div>', unsafe_allow_html=True)
        protokol_verileri.append({"yanit": v_yanit, "anket": v_anket, "kodlar": v_kodlar})

    if st.button(f"Analizi ve Kaydı Tamamla"):
        total_r = 0; r_8910 = 0; all_codes = []
        for i, d in enumerate(protokol_verileri, 1):
            if d["kodlar"].strip():
                resps = d["kodlar"].replace(';', '\n').split('\n')
                for r in resps:
                    clean = r.strip(); 
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
                "%A": ((counts["A"]+counts["Ad"])/total_r)*100, "%H": ((counts["H"]+counts["Hd"])/total_r)*100,
                "RC": (r_8910/total_r)*100
            }
            p_tri = (counts.get("FC",0)+counts.get("FC'",0)+counts.get("Fclob",0))*0.5 + (counts.get("CF",0)+counts.get("C'F",0)+counts.get("ClobF",0))*1 + (counts.get("C",0)+counts.get("C'",0)+counts.get("Clob",0))*1.5
            calc["TRI"] = (counts["K"]/p_tri)*100 if p_tri > 0 else 0

            tarih = datetime.now().strftime("%d/%m/%Y %H:%M")
            new_row = [st.session_state['user'], h_isim, h_yas, h_yorum, "", "", json.dumps(protokol_verileri), tarih]
            
            if edit_data is not None:
                cell = patient_sheet.find(edit_data['hasta_adi'])
                patient_sheet.update(f'A{cell.row}:H{cell.row}', [new_row])
                st.success("Kayıt güncellendi!")
            else:
                patient_sheet.append_row(new_row)
                st.success("Yeni kayıt oluşturuldu!")

            res_cols = st.columns(4)
            res_cols[0].markdown(f'<div class="metric-container bg-sari"><div class="metric-label">%G / %D</div><div class="metric-value">%{calc["%G"]:.0f} / %{calc["%D"]:.0f}</div></div>', unsafe_allow_html=True)
            res_cols[1].markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">%F</div><div class="metric-value">%{calc["%F"]:.0f}</div></div>', unsafe_allow_html=True)
            res_cols[2].markdown(f'<div class="metric-container bg-mor"><div class="metric-label">%A / %H</div><div class="metric-value">%{calc["%A"]:.0f} / %{calc["%H"]:.0f}</div></div>', unsafe_allow_html=True)
            res_cols[3].markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">TRI/RC</div><div class="metric-value">%{calc["TRI"]:.0f}/%{calc["RC"]:.0f}</div></div>', unsafe_allow_html=True)

            report_data = create_word_report({'name': h_isim, 'age': h_yas, 'comment': h_yorum, 'date': tarih}, calc, protokol_verileri, total_r)
            st.download_button("📄 Word Raporunu İndir", report_data, f"{h_isim}_Analiz.docx")
        else:
            st.warning("Kod girilmediği için analiz yapılamıyor.")

# --- 6. GİRİŞ VE PANEL ---
def auth_page():
    st.title("🧠 Rorschach Klinik Panel")
    t1, t2 = st.tabs(["Giriş", "Kayıt"])
    with t1:
        u = st.text_input("Kullanıcı")
        p = st.text_input("Şifre", type="password")
        if st.button("Giriş"):
            df = pd.DataFrame(user_sheet.get_all_records())
            df.columns = df.columns.str.strip()
            if u in df['kullanici_adi'].values and str(p) == str(df[df['kullanici_adi']==u]['sifre'].values[0]):
                st.session_state['logged_in'] = True; st.session_state['user'] = u; st.rerun()
            else: st.error("Hatalı giriş.")
    with t2:
        nu = st.text_input("Yeni Kullanıcı")
        np = st.text_input("Yeni Şifre", type="password")
        nn = st.text_input("Ad Soyad")
        if st.button("Kaydol"):
            user_sheet.append_row([nu, str(np), nn]); st.success("Kaydolundu!")

if not st.session_state['logged_in']:
    auth_page()
else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    menu = st.sidebar.radio("Menü", ["📁 Hastalarım", "➕ Yeni Hasta Ekle"])
    if st.sidebar.button("Güvenli Çıkış"): st.session_state['logged_in'] = False; st.rerun()

    if menu == "📁 Hastalarım":
        st.header("Kayıtlı Protokoller")
        data_p = patient_sheet.get_all_records()
        if data_p:
            df_p = pd.DataFrame(data_p)
            df_p.columns = df_p.columns.str.strip() # SÜTUN TEMİZLİĞİ BURADA
            
            if 'sahip' in df_p.columns:
                my_p = df_p[df_p['sahip'] == st.session_state['user']]
                if not my_p.empty:
                    for idx, row in my_p.iterrows():
                        if st.button(f"👤 {row.get('hasta_adi', 'İsimsiz')} ({row.get('tarih', '-')})", key=f"btn_{idx}"):
                            st.session_state['editing_patient'] = row.to_dict()
                    
                    if st.session_state['editing_patient']:
                        st.divider()
                        if st.button("❌ Düzenlemeyi Kapat"): 
                            st.session_state['editing_patient'] = None; st.rerun()
                        analysis_form(st.session_state['editing_patient'])
                else: st.info("Hasta kaydınız bulunmuyor.")
            else:
                st.error("Hata: Google Sheets 'Hastalar' sekmesinde 'sahip' sütunu bulunamadı.")
        else: st.info("Veritabanı boş.")

    elif menu == "➕ Yeni Hasta Ekle":
        st.session_state['editing_patient'] = None
        analysis_form()

st.markdown('<div class="footer">Kerem Birgül</div>', unsafe_allow_html=True)
