import streamlit as st
from collections import Counter
try:
    from docx import Document
    from docx.shared import Pt
except ImportError:
    st.error("Lütfen requirements.txt dosyasına 'python-docx' ekleyin.")
from io import BytesIO

st.set_page_config(page_title="Rorschach Psikogram", layout="wide")

# Kurumsal Sabit Tasarım
st.markdown("""
    <style>
    textarea { resize: none !important; border: 1px solid #ced4da !important; }
    .metric-container {
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        border-radius: 10px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: #1a1a1a;
    }
    .metric-label { font-size: 16px; font-weight: bold; margin-bottom: 5px; }
    .metric-value { font-size: 26px; font-weight: 900; }
    
    /* Yüksek Okunabilirlikli Kurumsal Renkler */
    .bg-sari { background-color: #FFD93D; border: 2px solid #E2B200; }
    .bg-kirmizi { background-color: #FF6B6B; border: 2px solid #D63031; }
    .bg-mor { background-color: #A29BFE; border: 2px solid #6C5CE7; }
    
    .footer { position: fixed; left: 0; bottom: 10px; width: 100%; text-align: center; color: #7f8c8d; font-size: 13px; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

st.title("Rorschach Psikogram")

# --- GRUPLAR ---
GRUP_1 = ["G", "D", "Dd", "Gbl", "Dbl"]
GRUP_2 = ["F", "F+", "F-", "F+-", "FC", "FC'", "Fclob", "C", "C'", "Clob", "CF", "C'F", "ClobF", "K", "Kan", "Kob", "Kp", "E", "EF", "FE"]
GRUP_3 = ["H", "Hd", "(H)", "A", "Ad", "(A)", "Nesne", "Bitki", "Anatomi", "Coğrafya", "Doğa"]
YAN_DAL = ["Ban", "Reddetme", "Şok"]
HEPSI_TANIMLI = set(GRUP_1 + GRUP_2 + GRUP_3 + YAN_DAL)

# --- GİRİŞ ---
st.write("Kart Yanıtları (Yanıtları ayırmak için her yanıtın sonuna ; koyun)")
kart_verileri = []
for i in range(1, 11):
    kart_verileri.append(st.text_area(f"Kart {i}", key=f"kart_{i}", height=100))

# Word Dosyası Oluşturma Fonksiyonu
def generate_docx(r_count, counts, calculations, extras):
    doc = Document()
    doc.add_heading('Rorschach Psikogram Raporu', 0)
    doc.add_paragraph(f'Toplam Yanıt (R): {r_count}')
    
    doc.add_heading('Kod Dağılımları', level=1)
    for k, v in counts.items():
        if v > 0:
            doc.add_paragraph(f'{k}: {v}')
    
    doc.add_heading('Psikogram Oranları', level=1)
    for name, val in calculations.items():
        doc.add_paragraph(f'{name}: %{val:.0f}')
    
    if extras:
        doc.add_heading('İstisna Kodlar', level=1)
        doc.add_paragraph(", ".join([f"{k} ({v})" for k, v in extras.items()]))

    doc.add_paragraph('\n\nHazırlayan: Kerem Birgül')
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

if st.button("Analizi Tamamla"):
    total_r = 0
    r_8910 = 0
    all_codes = []
    
    for i, data in enumerate(kart_verileri, 1):
        if data.strip():
            # Yanıtları ayır
            raw_responses = data.replace(';', '\n').split('\n')
            for resp in raw_responses:
                clean_resp = resp.strip()
                if not clean_resp or clean_resp.lower() == "reddetme": continue
                total_r += 1
                if i in [8, 9, 10]: r_8910 += 1
                for k in clean_resp.replace(",", " ").split():
                    if k: all_codes.append(k)

    if total_r > 0:
        st.subheader(f"R:{total_r}")
        counts = Counter(all_codes)
        
        # Kod Gösterimi
        c_list = st.columns(4)
        for idx, group in enumerate([GRUP_1, GRUP_2, GRUP_3, YAN_DAL]):
            with c_list[idx]:
                for k in group:
                    if counts[k] > 0: st.write(f"**{k}:** {counts[k]}")

        # İstisnaları Kutuya Al
        tanimsizlar = {k: v for k, v in counts.items() if k not in HEPSI_TANIMLI}
        if tanimsizlar:
            st.info(" ".join([f"**{k}:** {v} |" for k, v in tanimsizlar.items()]))

        st.divider()

        # Hesaplamalar
        calc = {
            "%G": (counts["G"]/total_r)*100,
            "%D": (counts["D"]/total_r)*100,
            "%F": (sum(counts[k] for k in ["F", "F+", "F-", "F+-"])/total_r)*100,
            "%A": ((counts["A"]+counts["Ad"])/total_r)*100,
            "%H": ((counts["H"]+counts["Hd"])/total_r)*100,
            "RC": (r_8910/total_r)*100
        }
        p_tri = (counts["FC"]+counts["FC'"]+counts["Fclob"])*0.5 + (counts["CF"]+counts["C'F"]+counts["ClobF"])*1 + (counts["C"]+counts["C'"]+counts["Clob"])*1.5
        calc["TRI"] = (counts["K"]/p_tri)*100 if p_tri > 0 else 0

        # Yeni Renkli Kutular
        col_1, col_2, col_3, col_4 = st.columns(4)
        with col_1: st.markdown(f'<div class="metric-container bg-sari"><div class="metric-label">%G / %D</div><div class="metric-value">%{calc["%G"]:.0f} / %{calc["%D"]:.0f}</div></div>', unsafe_allow_html=True)
        with col_2: st.markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">%F</div><div class="metric-value">%{calc["%F"]:.0f}</div></div>', unsafe_allow_html=True)
        with col_3: st.markdown(f'<div class="metric-container bg-mor"><div class="metric-label">%A / %H</div><div class="metric-value">%{calc["%A"]:.0f} / %{calc["%H"]:.0f}</div></div>', unsafe_allow_html=True)
        with col_4: st.markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">TRI / RC</div><div class="metric-value">%{calc["TRI"]:.0f} / %{calc["RC"]:.0f}</div></div>', unsafe_allow_html=True)

        # Word Çıktısı
        docx_file = generate_docx(total_r, counts, calc, tanimsizlar)
        st.download_button(
            label="📄 Raporu Word Olarak İndir",
            data=docx_file,
            file_name=f"Rorschach_Rapor_{total_r}R.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    else:
        st.warning("Henüz geçerli bir veri girmediniz.")

st.markdown('<div class="footer">Kerem Birgül</div>', unsafe_allow_html=True)
