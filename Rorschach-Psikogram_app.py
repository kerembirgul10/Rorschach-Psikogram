import streamlit as st
from collections import Counter
from io import BytesIO
try:
    from docx import Document
    from docx.shared import Pt
except ImportError:
    pass

st.set_page_config(page_title="Rorschach Klinik Analiz", layout="wide")

# Kurumsal Stil Ayarları
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
    
    .kart-wrapper {
        padding: 20px; border-radius: 15px; margin-top: 10px; margin-bottom: 30px;
        border: 1px solid rgba(0,0,0,0.1); box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    .kart-title-top {
        font-size: 20px; font-weight: 800; margin-bottom: 15px; color: #2c3e50;
        border-bottom: 2px solid rgba(0,0,0,0.1); padding-bottom: 5px; display: block;
    }
    .footer { position: fixed; left: 0; bottom: 10px; width: 100%; text-align: center; color: #7f8c8d; font-size: 13px; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

st.title("Rorschach Klinik Analiz ve Protokol")

# --- GRUPLARIN TANIMLANMASI ---
GRUP_1 = ["G", "D", "Dd", "Gbl", "Dbl"]
GRUP_2 = ["F", "F+", "F-", "F+-", "FC", "FC'", "Fclob", "C", "C'", "Clob", "CF", "C'F", "ClobF", "K", "Kan", "Kob", "Kp", "E", "EF", "FE"]
GRUP_3 = ["H", "Hd", "(H)", "A", "Ad", "(A)", "Nesne", "Bitki", "Anatomi", "Coğrafya", "Doğa"]
YAN_DAL = ["Ban", "Reddetme", "Şok"]

# --- 1. BÖLÜM: HASTA BİLGİLERİ ---
st.subheader("Hasta Bilgileri")
c1, c2 = st.columns([3, 1])
with c1: h_isim = st.text_input("Hastanın Adı Soyadı")
with c2: h_yas = st.number_input("Yaş", min_value=0, max_value=120, step=1)
h_yorum = st.text_area("Görüşme Hakkında Klinik Yorumlar", height=120)

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

# --- 3. BÖLÜM: PROTOKOL GİRİŞİ ---
st.subheader("Protokol ve Kodlama")
canli_renkler = ["#D1E9FF", "#FFD1D1", "#E9D1FF", "#D1D5FF", "#D1FFF9", "#DFFFDE", "#FFFBD1", "#FFE8D1", "#FFD1C2", "#E2E2E2"]
protokol_verileri = []

for i in range(1, 11):
    st.markdown(f'<div class="kart-wrapper" style="background-color:{canli_renkler[i-1]};"><span class="kart-title-top">KART {i}</span>', unsafe_allow_html=True)
    col_yanit, col_anket = st.columns(2)
    with col_yanit: yanit = st.text_area("Yanıtlar", key=f"yanit_{i}", height=100)
    with col_anket: anket = st.text_area("Anket", key=f"anket_{i}", height=100)
    kodlar = st.text_area("Kodlar", key=f"kod_{i}", height=80, placeholder="G F+ A; D F- H; ...")
    st.markdown('</div>', unsafe_allow_html=True)
    protokol_verileri.append({"yanit": yanit, "anket": anket, "kodlar": kodlar})

# --- 4. BÖLÜM: ANALİZ VE WORD ÇIKTISI ---
if st.button("Analizi Gerçekleştir ve Raporu Hazırla"):
    total_r = 0
    r_8910 = 0
    all_codes = []
    
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
        
        # Oran Hesaplamaları
        calc = {
            "%G": (counts["G"]/total_r)*100,
            "%D": (counts["D"]/total_r)*100,
            "%F": (sum(counts[k] for k in ["F", "F+", "F-", "F+-"])/total_r)*100,
            "%A": ((counts["A"]+counts["Ad"])/total_r)*100,
            "%H": ((counts["H"]+counts["Hd"])/total_r)*100,
            "RC": (r_8910/total_r)*100
        }
        p_tri = (counts.get("FC",0)+counts.get("FC'",0)+counts.get("Fclob",0))*0.5 + \
                (counts.get("CF",0)+counts.get("C'F",0)+counts.get("ClobF",0))*1 + \
                (counts.get("C",0)+counts.get("C'",0)+counts.get("Clob",0))*1.5
        calc["TRI"] = (counts["K"]/p_tri)*100 if p_tri > 0 else 0

        # EKRAN: Analiz Özeti ve Grup Frekansları
        st.subheader(f"Analiz Özeti (R: {total_r})")
        
        # Kod Sayıları (Frekanslar)
        st.write("**Kod Frekans Dağılımı:**")
        freq_cols = st.columns(4)
        for idx, group in enumerate([GRUP_1, GRUP_2, GRUP_3, YAN_DAL]):
            with freq_cols[idx]:
                for k in group:
                    if counts[k] > 0:
                        st.write(f"- **{k}:** {counts[k]}")

        # Renkli Metrik Kutuları
        res_cols = st.columns(4)
        res_cols[0].markdown(f'<div class="metric-container bg-sari"><div class="metric-label">%G / %D</div><div class="metric-value">%{calc["%G"]:.0f} / %{calc["%D"]:.0f}</div></div>', unsafe_allow_html=True)
        res_cols[1].markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">%F</div><div class="metric-value">%{calc["%F"]:.0f}</div></div>', unsafe_allow_html=True)
        res_cols[2].markdown(f'<div class="metric-container bg-mor"><div class="metric-label">%A / %H</div><div class="metric-value">%{calc["%A"]:.0f} / %{calc["%H"]:.0f}</div></div>', unsafe_allow_html=True)
        res_cols[3].markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">TRI / RC</div><div class="metric-value">%{calc["TRI"]:.0f} / %{calc["RC"]:.0f}</div></div>', unsafe_allow_html=True)

        # WORD RAPORU OLUŞTURMA
        try:
            doc = Document()
            doc.add_heading('Rorschach Klinik Analiz Raporu', 0)
            
            # 1. Hasta Bilgileri
            doc.add_heading('1. Hasta Bilgileri ve Klinik Gözlem', level=1)
            p = doc.add_paragraph()
            p.add_run(f'Ad Soyad: ').bold = True
            p.add_run(f'{h_isim}\n')
            p.add_run(f'Yaş: ').bold = True
            p.add_run(f'{h_yas}\n')
            doc.add_heading('Klinik Yorumlar:', level=2)
            doc.add_paragraph(h_yorum if h_yorum else "Yorum girilmedi.")
            
            # 2. Kart Tercihleri
            doc.add_heading('2. Kart Tercihleri', level=1)
            doc.add_paragraph(f"En Beğendiği Kartlar: {', '.join(map(str, best_cards))}\nNeden: {best_reason}")
            doc.add_paragraph(f"En Beğenilmeyen Kartlar: {', '.join(map(str, worst_cards))}\nNeden: {worst_reason}")

            # 3. Protokol Tabloları
            doc.add_heading('3. Test Protokolü', level=1)
            for i, p_data in enumerate(protokol_verileri, 1):
                doc.add_heading(f'Kart {i}', level=2)
                table = doc.add_table(rows=2, cols=3)
                table.style = 'Table Grid'
                table.rows[0].cells[0].text = 'Yanıt'
                table.rows[0].cells[1].text = 'Anket'
                table.rows[0].cells[2].text = 'Kodlar'
                table.rows[1].cells[0].text = p_data["yanit"]
                table.rows[1].cells[1].text = p_data["anket"]
                table.rows[1].cells[2].text = p_data["kodlar"]

            # 4. Psikogram Verileri (FREKANSLAR BURAYA EKLENDİ)
            doc.add_heading('4. Psikogram Analiz Verileri', level=1)
            doc.add_paragraph(f"Toplam Yanıt Sayısı (R): {total_r}").bold = True
            
            doc.add_heading('Kod Frekansları:', level=2)
            f_table = doc.add_table(rows=1, cols=2)
            f_table.style = 'Table Grid'
            for k, v in counts.items():
                row = f_table.add_row().cells
                row[0].text = str(k)
                row[1].text = str(v)

            doc.add_heading('Hesaplanan Oranlar:', level=2)
            res_table = doc.add_table(rows=1, cols=2)
            res_table.style = 'Table Grid'
            for k, v in calc.items():
                row_cells = res_table.add_row().cells
                row_cells[0].text = str(k)
                row_cells[1].text = f"%{v:.0f}"

            doc.add_paragraph(f"\nHazırlayan: Kerem Birgül")

            bio = BytesIO()
            doc.save(bio)
            st.download_button(
                label="📄 Eksiksiz Raporu Word Olarak İndir",
                data=bio.getvalue(),
                file_name=f"{h_isim}_Rorschach_Tam_Rapor.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except Exception as e:
            st.error(f"Hata: {e}")
    else:
        st.warning("Henüz kod girilmedi.")

st.markdown('<div class="footer">Kerem Birgül</div>', unsafe_allow_html=True)
