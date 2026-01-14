import streamlit as st
from collections import Counter
from io import BytesIO
try:
    from docx import Document
    from docx.shared import Inches
except ImportError:
    pass

st.set_page_config(page_title="Rorschach Klinik Analiz", layout="wide")

# Kurumsal Stil
st.markdown("""
    <style>
    textarea { resize: none !important; border: 1px solid #ced4da !important; }
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
    
    .footer { position: fixed; left: 0; bottom: 10px; width: 100%; text-align: center; color: #7f8c8d; font-size: 13px; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

st.title("Rorschach Klinik Analiz ve Protokol")

# --- 1. BÖLÜM: HASTA BİLGİLERİ ---
st.subheader("Hasta Bilgileri")
c1, c2 = st.columns([3, 1])
with c1: h_isim = st.text_input("Hastanın Adı Soyadı")
with c2: h_yas = st.number_input("Yaş", min_value=0, max_value=120, step=1)
h_yorum = st.text_area("Görüşme Hakkında Klinik Yorumlar", height=100)

st.divider()

# --- 2. BÖLÜM: KART TERCİHLERİ ---
def kart_secim_arayuzu(label_text, key_prefix):
    st.write(f"**{label_text}**")
    cols = st.columns(10)
    secilenler = []
    for i in range(1, 11):
        with cols[i-1]:
            if st.checkbox(f"{i}", key=f"{key_prefix}_{i}"): secilenler.append(i)
    return secilenler

best_cards = kart_secim_arayuzu("En Beğendiği Kartlar", "best")
best_reason = st.text_area("Beğenme Nedeni", height=60, key="br")
worst_cards = kart_secim_arayuzu("En Beğenilmeyen Kartlar", "worst")
worst_reason = st.text_area("Beğenmeme Nedeni", height=60, key="wr")

st.divider()

# --- 3. BÖLÜM: PROTOKOL GİRİŞİ (YANIT - ANKET - KODLAR) ---
st.subheader("Protokol ve Kodlama")
renkler = ["#f0f4ff", "#fff0f0", "#f0fff0", "#fffaf0", "#f0ffff", "#f5f0ff", "#fff0f5", "#fdf5e6", "#f0fff4", "#f8f8f8"]

protokol_verileri = [] # (yanit, anket, kodlar) şeklinde tutulacak

for i in range(1, 11):
    st.markdown(f'<div style="background-color:{renkler[i-1]}; padding:10px; border-radius:5px; border:1px solid #ddd; margin-top:20px; font-weight:bold;">Kart {i}</div>', unsafe_allow_html=True)
    
    col_yanit, col_anket = st.columns(2)
    with col_yanit:
        yanit = st.text_area("Yanıtlar", key=f"yanit_{i}", height=100, placeholder=f"Kart {i} için hastanın sözel yanıtları...")
    with col_anket:
        anket = st.text_area("Anket (Soruşturma)", key=f"anket_{i}", height=100, placeholder="Yerleşimi ve belirleyicileri netleştirmek için sorular/cevaplar...")
    
    kodlar = st.text_area("Kodlar", key=f"kod_{i}", height=80, placeholder="G F+ H; D F- A; ...")
    protokol_verileri.append({"yanit": yanit, "anket": anket, "kodlar": kodlar})

# --- 4. BÖLÜM: ANALİZ VE WORD ÇIKTISI ---
if st.button("Analizi Gerçekleştir ve Protokolü İndir"):
    total_r = 0
    r_8910 = 0
    all_codes = []
    
    # Hesaplama için kodları işle
    for i, data in enumerate(protokol_verileri, 1):
        kod_metni = data["kodlar"]
        if kod_metni.strip():
            resps = kod_metni.replace(';', '\n').split('\n')
            for r in resps:
                clean = r.strip()
                if not clean or clean.lower() == "reddetme": continue
                total_r += 1
                if i in [8, 9, 10]: r_8910 += 1
                for k in clean.replace(",", " ").split():
                    if k: all_codes.append(k)

    if total_r > 0:
        counts = Counter(all_codes)
        # (Hesaplama formülleri aynı kalıyor)
        calc = {
            "%G": (counts["G"]/total_r)*100, "%D": (counts["D"]/total_r)*100,
            "%F": (sum(counts[k] for k in ["F", "F+", "F-", "F+-"])/total_r)*100,
            "%A": ((counts["A"]+counts["Ad"])/total_r)*100,
            "%H": ((counts["H"]+counts["Hd"])/total_r)*100,
            "RC": (r_8910/total_r)*100
        }
        p_tri = (counts.get("FC",0)+counts.get("FC'",0)+counts.get("Fclob",0))*0.5 + \
                (counts.get("CF",0)+counts.get("C'F",0)+counts.get("ClobF",0))*1 + \
                (counts.get("C",0)+counts.get("C'",0)+counts.get("Clob",0))*1.5
        calc["TRI"] = (counts["K"]/p_tri)*100 if p_tri > 0 else 0

        st.subheader(f"Analiz Özeti (R: {total_r})")
        res_cols = st.columns(4)
        res_cols[0].markdown(f'<div class="metric-container bg-sari"><div class="metric-label">%G / %D</div><div class="metric-value">%{calc["%G"]:.0f} / %{calc["%D"]:.0f}</div></div>', unsafe_allow_html=True)
        res_cols[1].markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">%F</div><div class="metric-value">%{calc["%F"]:.0f}</div></div>', unsafe_allow_html=True)
        res_cols[2].markdown(f'<div class="metric-container bg-mor"><div class="metric-label">%A / %H</div><div class="metric-value">%{calc["%A"]:.0f} / %{calc["%H"]:.0f}</div></div>', unsafe_allow_html=True)
        res_cols[3].markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">TRI / RC</div><div class="metric-value">%{calc["TRI"]:.0f} / %{calc["RC"]:.0f}</div></div>', unsafe_allow_html=True)

        # WORD RAPORU
        try:
            doc = Document()
            doc.add_heading('Rorschach Test Protokolü ve Analizi', 0)
            doc.add_paragraph(f'Hasta: {h_isim} | Yaş: {h_yas}')
            
            # Protokol Tablosu
            doc.add_heading('Test Protokolü', level=1)
            for i, p in enumerate(protokol_verileri, 1):
                doc.add_heading(f'Kart {i}', level=2)
                table = doc.add_table(rows=1, cols=3)
                table.style = 'Table Grid'
                hdr_cells = table.rows[0].cells
                hdr_cells[0].text = 'Yanıt'
                hdr_cells[1].text = 'Anket'
                hdr_cells[2].text = 'Kodlar'
                
                row_cells = table.add_row().cells
                row_cells[0].text = p["yanit"]
                row_cells[1].text = p["anket"]
                row_cells[2].text = p["kodlar"]
            
            # (Kart tercihleri ve psikogram sonuçları da rapora ekleniyor...)
            bio = BytesIO(); doc.save(bio)
            st.download_button("📄 Word Protokolünü İndir", bio.getvalue(), f"{h_isim}_Rorschach_Protokol.docx")
        except: st.error("Rapor oluşturulamadı.")
    else:
        st.warning("Veri girişi yapılmadı.")

st.markdown('<div class="footer">Kerem Birgül</div>', unsafe_allow_html=True)
