import streamlit as st
from collections import Counter
from docx import Document
from io import BytesIO

st.set_page_config(page_title="Rorschach Psikogram", layout="wide")

# Kurumsal Tasarım ve Sabit Kutu CSS
st.markdown("""
    <style>
    textarea { resize: none !important; }
    .metric-container {
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        border-radius: 8px;
        margin-bottom: 15px;
        border: 1px solid #dcdde1;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .metric-label { font-size: 14px; font-weight: bold; color: #2f3640; margin-bottom: 5px; }
    .metric-value { font-size: 24px; font-weight: bold; color: #2f3640; }
    
    /* Kurumsal Renk Paleti */
    .bg-sari { background-color: #fcf3cf; border-left: 5px solid #f1c40f; }
    .bg-kirmizi { background-color: #fadbd8; border-left: 5px solid #e74c3c; }
    .bg-mor { background-color: #f5eef8; border-left: 5px solid #9b59b6; }
    
    .footer { position: fixed; left: 0; bottom: 10px; width: 100%; text-align: center; color: #95a5a6; font-size: 12px; }
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
kart_verileri = []
for i in range(1, 11):
    kart_verileri.append(st.text_area(f"Kart {i}", key=f"kart_{i}", height=100))

def generate_docx(r_count, counts, calculations, extras):
    doc = Document()
    doc.add_heading('Rorschach Psikogram Analiz Raporu', 0)
    doc.add_paragraph(f'Toplam Yanıt (R): {r_count}')
    
    doc.add_heading('Kod Dağılımları', level=1)
    for k, v in counts.items():
        doc.add_paragraph(f'{k}: {v}', style='List Bullet')
    
    doc.add_heading('Psikogram Hesaplamaları', level=1)
    for name, val in calculations.items():
        doc.add_paragraph(f'{name}: %{val:.0f}')
    
    if extras:
        doc.add_heading('Tanımsız Kodlar', level=1)
        doc.add_paragraph(", ".join(extras))

    doc.add_paragraph('\n\nAnaliz: Kerem Birgül')
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

if st.button("Analizi Gerçekleştir"):
    total_r = 0
    r_8910 = 0
    all_codes = []
    
    for i, data in enumerate(kart_verileri, 1):
        if data.strip():
            lines = data.replace(';', '\n').split('\n')
            for line in lines:
                clean = line.strip()
                if not clean or clean.lower() == "reddetme": continue
                total_r += 1
                if i in [8, 9, 10]: r_8910 += 1
                for k in clean.replace(",", " ").split():
                    if k: all_codes.append(k)

    if total_r > 0:
        st.subheader(f"R:{total_r}")
        counts = Counter(all_codes)
        
        # Kod Gösterimi
        cols = st.columns(4)
        for idx, group in enumerate([GRUP_1, GRUP_2, GRUP_3, YAN_DAL]):
            with cols[idx]:
                for k in group:
                    if counts[k] > 0: st.write(f"**{k}:** {counts[k]}")

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

        # Renkli Kutular
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="metric-container bg-sari"><div class="metric-label">%G / %D</div><div class="metric-value">%{calc["%G"]:.0f} / %{calc["%D"]:.0f}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">%F</div><div class="metric-value">%{calc["%F"]:.0f}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-container bg-mor"><div class="metric-label">%A / %H</div><div class="metric-value">%{calc["%A"]:.0f} / %{calc["%H"]:.0f}</div></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">TRI / RC</div><div class="metric-value">%{calc["TRI"]:.0f} / %{calc["RC"]:.0f}</div></div>', unsafe_allow_html=True)

        # Word İndirme Butonu
        docx_data = generate_docx(total_r, counts, calc, [k for k in counts if k not in HEPSI_TANIMLI])
        st.download_button(label="📄 Analiz Raporunu Word Olarak İndir", data=docx_data, file_name="Rorschach_Analiz.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.error("Veri girişi yapılmadı.")

st.markdown('<div class="footer">Kerem Birgül</div>', unsafe_allow_html=True)
