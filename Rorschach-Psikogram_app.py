import streamlit as st
from collections import Counter
from io import BytesIO
try:
    from docx import Document
except ImportError:
    pass

st.set_page_config(page_title="Rorschach Klinik Analiz", layout="wide")

# Gelişmiş Tasarım ve Dinamik Kart Renkleri
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
    
    /* Kart Seçim Butonları Stili */
    .stCheckbox > label > div[data-bv="true"] {
        background-color: #ff4b4b !important;
        border-color: #ff4b4b !important;
    }
    
    /* Kartlara Özel Renkli Arka Planlar */
    .kart-box { padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #ddd; }
    .k1 { background-color: #f0f4ff; } .k2 { background-color: #fff0f0; } .k3 { background-color: #f0fff0; }
    .k4 { background-color: #fffaf0; } .k5 { background-color: #f0ffff; } .k6 { background-color: #f5f0ff; }
    .k7 { background-color: #fff0f5; } .k8 { background-color: #fdf5e6; } .k9 { background-color: #f0fff4; }
    .k10 { background-color: #f8f8f8; }

    .footer { position: fixed; left: 0; bottom: 10px; width: 100%; text-align: center; color: #7f8c8d; font-size: 13px; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

st.title("Rorschach Psikogram ve Klinik Raporlama")

# --- 1. BÖLÜM: HASTA BİLGİLERİ ---
st.subheader("Hasta Bilgileri")
c1, c2 = st.columns([3, 1])
with c1:
    h_isim = st.text_input("Hastanın Adı Soyadı")
with c2:
    h_yas = st.number_input("Yaş", min_value=0, max_value=120, step=1)
h_yorum = st.text_area("Görüşme Hakkında Klinik Yorumlar", height=120)

st.divider()

# --- 2. BÖLÜM: KART TERCİHLERİ (ALT ALTA VE İŞARETLEMELİ) ---
st.subheader("Kart Tercihleri")

def kart_secim_arayuzu(label_text, key_prefix):
    st.write(f"**{label_text}**")
    cols = st.columns(10)
    secilenler = []
    for i in range(1, 11):
        with cols[i-1]:
            if st.checkbox(f"{i}", key=f"{key_prefix}_{i}"):
                secilenler.append(i)
    return secilenler

# En Beğenilen Kartlar
best_cards = kart_secim_arayuzu("En Beğendiği Kartlar", "best")
best_reason = st.text_area("Beğenme Nedeni", height=70, key="br")

st.write("") # Boşluk

# En Beğenilmeyen Kartlar
worst_cards = kart_secim_arayuzu("En Beğenilmeyen Kartlar", "worst")
worst_reason = st.text_area("Beğenmeme Nedeni", height=70, key="wr")

st.divider()

# --- 3. BÖLÜM: KART KODLARI (ALT ALTA VE RENKLİ) ---
st.subheader("Kart Yanıtları")
GRUP_1 = ["G", "D", "Dd", "Gbl", "Dbl"]
GRUP_2 = ["F", "F+", "F-", "F+-", "FC", "FC'", "Fclob", "C", "C'", "Clob", "CF", "C'F", "ClobF", "K", "Kan", "Kob", "Kp", "E", "EF", "FE"]
GRUP_3 = ["H", "Hd", "(H)", "A", "Ad", "(A)", "Nesne", "Bitki", "Anatomi", "Coğrafya", "Doğa"]
YAN_DAL = ["Ban", "Reddetme", "Şok"]
HEPSI_TANIMLI = set(GRUP_1 + GRUP_2 + GRUP_3 + YAN_DAL)

kart_verileri = []
renkler = ["f0f4ff", "fff0f0", "f0fff0", "fffaf0", "f0ffff", "f5f0ff", "fff0f5", "fdf5e6", "f0fff4", "f8f8f8"]

for i in range(1, 11):
    st.markdown(f'<div style="background-color:#{renkler[i-1]}; padding:10px; border-radius:5px; border:1px solid #ddd; margin-bottom:5px; font-weight:bold;">Kart {i}</div>', unsafe_allow_html=True)
    v = st.text_area("", key=f"k_input_{i}", height=80, label_visibility="collapsed", placeholder=f"Kart {i} kodlarını buraya girin...")
    kart_verileri.append(v)

# --- 4. BÖLÜM: HESAPLAMA VE RAPOR ---
if st.button("Analizi Gerçekleştir ve Raporu Hazırla"):
    total_r = 0
    r_8910 = 0
    all_codes = []
    
    for i, data in enumerate(kart_verileri, 1):
        if data.strip():
            resps = data.replace(';', '\n').split('\n')
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
        p_tri = (counts.get("FC",0)+counts.get("FC'",0)+counts.get("Fclob",0))*0.5 + \
                (counts.get("CF",0)+counts.get("C'F",0)+counts.get("ClobF",0))*1 + \
                (counts.get("C",0)+counts.get("C'",0)+counts.get("Clob",0))*1.5
        calc["TRI"] = (counts["K"]/p_tri)*100 if p_tri > 0 else 0

        st.subheader(f"Psikogram Sonuçları (R: {total_r})")
        res_cols = st.columns(4)
        res_cols[0].markdown(f'<div class="metric-container bg-sari"><div class="metric-label">%G / %D</div><div class="metric-value">%{calc["%G"]:.0f} / %{calc["%D"]:.0f}</div></div>', unsafe_allow_html=True)
        res_cols[1].markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">%F</div><div class="metric-value">%{calc["%F"]:.0f}</div></div>', unsafe_allow_html=True)
        res_cols[2].markdown(f'<div class="metric-container bg-mor"><div class="metric-label">%A / %H</div><div class="metric-value">%{calc["%A"]:.0f} / %{calc["%H"]:.0f}</div></div>', unsafe_allow_html=True)
        res_cols[3].markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">TRI / RC</div><div class="metric-value">%{calc["TRI"]:.0f} / %{calc["RC"]:.0f}</div></div>', unsafe_allow_html=True)

        try:
            doc = Document()
            doc.add_heading('Rorschach Klinik Analiz Raporu', 0)
            doc.add_paragraph(f'Hasta: {h_isim} ({h_yas} Yaş)')
            doc.add_heading('Klinik Notlar', level=1); doc.add_paragraph(h_yorum)
            doc.add_heading('Kart Tercihleri', level=1)
            doc.add_paragraph(f"Beğenilenler: {best_cards} - Neden: {best_reason}")
            doc.add_paragraph(f"Beğenilmeyenler: {worst_cards} - Neden: {worst_reason}")
            doc.add_heading('Psikogram', level=1)
            for k, v in calc.items(): doc.add_paragraph(f"{k}: %{v:.0f}")
            bio = BytesIO(); doc.save(bio)
            st.download_button("📄 Klinik Raporu İndir", bio.getvalue(), f"{h_isim}_Rapor.docx")
        except: st.info("Rapor oluşturuluyor...")
    else:
        st.warning("Veri girişi yapılmadı.")

st.markdown('<div class="footer">Kerem Birgül</div>', unsafe_allow_html=True)
