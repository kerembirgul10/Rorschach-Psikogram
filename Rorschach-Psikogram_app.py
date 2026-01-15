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
GRUP_4 = ["Ban", "Reddetme", "Şok", "Pop", "O", "V"]
TUM_GRUPLAR = GRUP_1 + GRUP_2 + GRUP_3 + GRUP_4

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
    st.error(f"Baglanti hatasi: {e}")
    st.stop()

# --- 3. TASARIM ---
st.set_page_config(page_title="Rorschach Klinik Panel", layout="wide")
st.markdown("""
    <style>
    textarea { border: 1px solid #ced4da !important; border-radius: 5px !important; }
    .metric-container {
        height: 100px; display: flex; flex-direction: column; justify-content: center; align-items: center;
        border-radius: 10px; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: #1a1a1a;
        width: 100%;
    }
    .metric-label { font-size: 13px; font-weight: bold; margin-bottom: 2px; }
    .metric-value { font-size: 20px; font-weight: 900; }
    .c-g { background-color: #FFD93D; border: 2px solid #E2B200; }
    .c-d { background-color: #FFB347; border: 2px solid #E67E22; }
    .c-f { background-color: #FF6B6B; border: 2px solid #D63031; }
    .c-a { background-color: #A29BFE; border: 2px solid #6C5CE7; }
    .c-h { background-color: #D1A3FF; border: 2px solid #8E44AD; }
    .c-tri { background-color: #74B9FF; border: 2px solid #0984E3; }
    .c-rc { background-color: #55E6C1; border: 2px solid #20BF6B; }
    .kart-wrapper { padding: 20px; border-radius: 15px; margin-bottom: 25px; border: 1px solid rgba(0,0,0,0.1); }
    .kart-title-top { font-size: 18px; font-weight: 800; border-bottom: 2px solid rgba(0,0,0,0.1); margin-bottom: 10px; color: #000000 !important; }
    .footer { position: fixed; left: 0; bottom: 10px; width: 100%; text-align: center; color: #7f8c8d; font-size: 13px; }
    [data-testid="stSidebar"] { display: none; }
    button[kind="primary"] { background-color: #2ECC71 !important; color: white !important; border: none !important; }
    </style>
""", unsafe_allow_html=True)

# Otomatik büyüme için yükseklik hesaplayıcı
def get_auto_height(text, min_h=68):
    if not text: return min_h
    lines = text.count('\n') + 1
    return max(min_h, lines * 28)

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user' not in st.session_state: st.session_state['user'] = ""
if 'page' not in st.session_state: st.session_state['page'] = "Hastalarim"
if 'editing_patient' not in st.session_state: st.session_state['editing_patient'] = None
if 'form_id' not in st.session_state: st.session_state['form_id'] = datetime.now().timestamp()

# --- 4. WORD RAPOR (Grup 4 ve Düzenli Sıralama) ---
def create_word_report(h_info, calc, counts, total_r, b_cards, w_cards, b_reason, w_reason, protokol, selected_date):
    doc = Document()
    doc.add_heading(h_info['name'], 0)
    doc.add_heading('Hasta Bilgileri', level=1)
    doc.add_paragraph(f"Yas: {h_info['age']}\nUygulama Tarihi: {selected_date}")
    doc.add_heading('Klinik Yorumlar', level=2)
    doc.add_paragraph(h_info['comment'])
    
    doc.add_heading('Test Protokolu', level=1)
    table = doc.add_table(rows=1, cols=4); table.style = 'Table Grid'
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text, hdr[3].text = 'Kart', 'Yanit', 'Anket', 'Kodlar'
    for i, p in enumerate(protokol, 1):
        row = table.add_row().cells
        row[0].text, row[1].text = str(i), str(p.get('yanit', ''))
        row[2].text, row[3].text = str(p.get('anket', '')), str(p.get('kodlar', ''))
    
    doc.add_heading('Psikogram Analizi', level=1)
    for k, v in calc.items(): doc.add_paragraph(f"{k}: %{v:.1f}")
    
    doc.add_heading('Kod Frekanslari', level=2)
    for g_n, g_l in [("Lokalizasyon", GRUP_1), ("Belirleyiciler", GRUP_2), ("Icerik", GRUP_3), ("Ozel Kodlar", GRUP_4)]:
        kodlar = [f"{k}: {counts[k]}" for k in g_l if counts[k] > 0]
        if kodlar: doc.add_paragraph(f"{g_n}: " + " | ".join(kodlar))
    
    diger_k = [f"{k}: {counts[k]}" for k in counts if k not in TUM_GRUPLAR and counts[k] > 0]
    if diger_k: doc.add_paragraph("Diger Kodlar: " + " | ".join(diger_k))
    
    bio = BytesIO(); doc.save(bio); return bio.getvalue()

# --- 5. ANALIZ FORMU ---
def analysis_form(edit_data=None):
    f_id = st.session_state['form_id'] if edit_data is None else f"edit_{edit_data.get('hasta_adi')}"
    
    st.header(f"{'Duzenle' if edit_data else 'Yeni'} Hasta Protokolu")
    c_info1, c_info2, c_info3 = st.columns([3, 1, 2])
    h_isim = c_info1.text_input("Hastanin Adi Soyadi", value=edit_data.get('hasta_adi', "") if edit_data else "", key=f"name_{f_id}")
    h_yas = c_info2.number_input("Yas", 0, 120, value=int(edit_data.get('yas', 0)) if edit_data else 0, key=f"age_{f_id}")
    
    if edit_data and edit_data.get('tarih'):
        try: default_date = datetime.strptime(edit_data['tarih'], "%d/%m/%Y").date()
        except: default_date = datetime.now().date()
    else: default_date = datetime.now().date()
    h_tarih = c_info3.date_input("Test Uygulama Tarihi", value=default_date, format="DD/MM/YYYY", key=f"date_{f_id}")
    tarih_str = h_tarih.strftime("%d/%m/%Y")
    
    # Dinamik Klinik Yorum Kutusu
    y_comm = edit_data.get('klinik_yorum', "") if edit_data else ""
    h_yorum = st.text_area("Klinik Yorumlar", value=y_comm, height=get_auto_height(y_comm, 100), key=f"comment_{f_id}")

    st.divider(); st.subheader("Kart Tercihleri")
    def box_selector(label, key_prefix, saved_val):
        st.write(label)
        saved_list = json.loads(saved_val) if saved_val else []
        state_key = f"{key_prefix}_list_{f_id}"
        if state_key not in st.session_state: st.session_state[state_key] = saved_list
        cols = st.columns(10)
        for i in range(1, 11):
            is_sel = i in st.session_state[state_key]
            if cols[i-1].button(str(i), key=f"{state_key}_{i}", type="primary" if is_sel else "secondary"):
                if is_sel: st.session_state[state_key].remove(i)
                else: st.session_state[state_key].append(i)
                st.rerun()
        return st.session_state[state_key]

    b_cards = box_selector("En Begendigi Kartlar", "best", edit_data.get('en_begendigi', "[]") if edit_data else "[]")
    b_r_txt = edit_data.get('en_begendigi_neden', "") if edit_data else ""
    b_reason = st.text_area("Begenme Nedeni", value=b_r_txt, height=get_auto_height(b_r_txt), key=f"br_{f_id}")
    
    w_cards = box_selector("En Begenmedigi Kartlar", "worst", edit_data.get('en_beğenmediği', "[]") if edit_data else "[]")
    w_r_txt = edit_data.get('en_beğenmediği_neden', "") if edit_data else ""
    w_reason = st.text_area("Begenmeme Nedeni", value=w_r_txt, height=get_auto_height(w_r_txt), key=f"wr_{f_id}")

    st.divider()
    protokol_verileri = []
    renkler = ["#D1E9FF", "#FFD1D1", "#E9D1FF", "#D1D5FF", "#D1FFF9", "#DFFFDE", "#FFFBD1", "#FFE8D1", "#FFD1C2", "#E2E2E2"]
    saved_p = json.loads(edit_data['protokol_verisi']) if (edit_data and 'protokol_verisi' in edit_data) else [{"yanit":"","anket":"","kodlar":""} for _ in range(10)]

    for i in range(1, 11):
        st.markdown(f'<div class="kart-wrapper" style="background-color:{renkler[i-1]};"><span class="kart-title-top">KART {i}</span>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        y_txt = saved_p[i-1].get('yanit','')
        a_txt = saved_p[i-1].get('anket','')
        k_txt = saved_p[i-1].get('kodlar','')
        
        y = col1.text_area("Yanit", key=f"y_{i}_{f_id}", value=y_txt, height=get_auto_height(y_txt))
        a = col2.text_area("Anket", key=f"a_{i}_{f_id}", value=a_txt, height=get_auto_height(a_txt))
        k = st.text_area("Kodlar", key=f"k_{i}_{f_id}", value=k_txt, height=get_auto_height(k_txt))
        st.markdown('</div>', unsafe_allow_html=True)
        protokol_verileri.append({"yanit": y, "anket": a, "kodlar": k})

    btn_col1, btn_col2 = st.columns(2)
    save_clicked = btn_col1.button("Sadece Kaydet")
    calc_clicked = btn_col2.button("Psikogrami Hesapla")

    if save_clicked or calc_clicked:
        new_row = [st.session_state['user'], h_isim, h_yas, h_yorum, json.dumps(b_cards), json.dumps(w_cards), json.dumps(protokol_verileri), tarih_str, b_reason, w_reason]
        if edit_data:
            cell = patient_sheet.find(edit_data['hasta_adi']); patient_sheet.update(f'A{cell.row}:J{cell.row}', [new_row])
        else: patient_sheet.append_row(new_row)
        st.success("Kaydedildi.")

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
                    for code in line.replace(",", " ").split(): 
                        clean_code = code.replace("’", "'").replace("‘", "'").strip()
                        all_codes.append(clean_code)
        
        if total_r > 0:
            counts = Counter(all_codes)
            calc = {"%G": (counts["G"]/total_r)*100, "%D": (counts["D"]/total_r)*100, "%F": (sum(counts[k] for k in ["F", "F+", "F-", "F+-"])/total_r)*100, "%A": ((counts["A"]+counts["Ad"])/total_r)*100, "%H": ((counts["H"]+counts["Hd"])/total_r)*100, "RC": (r_8910/total_r)*100}
            p_tri = (counts.get("FC",0)+counts.get("FC'",0)+counts.get("Fclob",0))*0.5 + (counts.get("CF",0)+counts.get("C'F",0)+counts.get("ClobF",0))*1 + (counts.get("C",0)+counts.get("C'",0)+counts.get("Clob",0))*1.5
            calc["TRI"] = (counts["K"]/p_tri)*100 if p_tri > 0 else 0
            
            st.subheader(f"Analiz (R: {total_r})")
            m_cols = st.columns(7)
            m_cols[0].markdown(f'<div class="metric-container c-g"><div class="metric-label">%G</div><div class="metric-value">%{calc["%G"]:.0f}</div></div>', unsafe_allow_html=True)
            m_cols[1].markdown(f'<div class="metric-container c-d"><div class="metric-label">%D</div><div class="metric-value">%{calc["%D"]:.0f}</div></div>', unsafe_allow_html=True)
            m_cols[2].markdown(f'<div class="metric-container c-f"><div class="metric-label">%F</div><div class="metric-value">%{calc["%F"]:.0f}</div></div>', unsafe_allow_html=True)
            m_cols[3].markdown(f'<div class="metric-container c-a"><div class="metric-label">%A</div><div class="metric-value">%{calc["%A"]:.0f}</div></div>', unsafe_allow_html=True)
            m_cols[4].markdown(f'<div class="metric-container c-h"><div class="metric-label">%H</div><div class="metric-value">%{calc["%H"]:.0f}</div></div>', unsafe_allow_html=True)
            m_cols[5].markdown(f'<div class="metric-container c-tri"><div class="metric-label">TRI</div><div class="metric-value">%{calc["TRI"]:.0f}</div></div>', unsafe_allow_html=True)
            m_cols[6].markdown(f'<div class="metric-container c-rc"><div class="metric-label">RC</div><div class="metric-value">%{calc["RC"]:.0f}</div></div>', unsafe_allow_html=True)

            st.write("**Kod Frekanslari:**")
            for g_n, g_l in [("Lokalizasyon", GRUP_1), ("Belirleyiciler", GRUP_2), ("Icerik", GRUP_3), ("Ozel Kodlar", GRUP_4)]:
                kodlar = [f"{k}: {counts[k]}" for k in g_l if counts[k] > 0]
                if kodlar: st.write(f"**{g_n}:** " + " | ".join(kodlar))
            
            d_codes = [f"{k}: {counts[k]}" for k in counts if k not in TUM_GRUPLAR]
            if d_codes: st.write("**Diger Kodlar:** " + " | ".join(d_codes))

            report = create_word_report({'name': h_isim, 'age': h_yas, 'comment': h_yorum, 'date': tarih_str}, calc, counts, total_r, b_cards, w_cards, b_reason, w_reason, protokol_verileri, tarih_str)
            st.download_button("Word Indir", report, f"{h_isim}_Rorschach.docx")

# --- 6. NAVIGASYON ---

# --- 6. NAVIGASYON VE GIRIS EKRANI ---
if not st.session_state['logged_in']:
    st.title("Rorschach Klinik Panel")
    
    # Giriş ve Kayıt sekmelerini burada oluşturuyoruz
    t1, t2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    with t1:
        u = st.text_input("Kullanıcı Adı", key="login_u")
        p = st.text_input("Şifre", type="password", key="login_p")
        if st.button("Giriş"):
            df = pd.DataFrame(user_sheet.get_all_records())
            df.columns = df.columns.str.strip()
            if u in df['kullanici_adi'].values:
                if str(p) == str(df[df['kullanici_adi']==u]['sifre'].values[0]):
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = u
                    st.rerun()
                else:
                    st.error("Hatalı şifre.")
            else:
                st.error("Kullanıcı bulunamadı.")
                
    with t2:
        st.subheader("Yeni Hesap Oluştur")
        nu = st.text_input("Yeni Kullanıcı Adı", key="reg_u")
        np = st.text_input("Şifre Belirle", type="password", key="reg_p")
        nn = st.text_input("Ad Soyad", key="reg_n")
        
        if st.button("Kayıt Ol"):
            if nu and np and nn:
                user_sheet.append_row([nu, str(np), nn])
                st.success("Kaydınız başarıyla oluşturuldu! Şimdi giriş yapabilirsiniz.")
            else:
                st.warning("Lütfen tüm alanları doldurun.")

else:
    # Buradan sonrası mevcut giriş yapmış kullanıcı menüsü (Üst Menü) devam eder...
    c_user, c_nav1, c_nav2, c_out = st.columns([1, 1, 1, 1])
    # ... (Önceki yazdığımız navigasyon kodları buraya gelecek)
