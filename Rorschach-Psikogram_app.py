import streamlit as st
from collections import Counter
from io import BytesIO
try:
    from docx import Document
except ImportError:
    pass

st.set_page_config(page_title="Rorschach Klinik Analiz", layout="wide")

# Kurumsal Stil ve Sabit Tasarım
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

st.title("Rorschach Psikogram ve Klinik Raporlama")

# --- 1. BÖLÜM: HASTA BİLGİLERİ VE KLİNİK GÖRÜŞME ---
st.subheader("Hasta Bilgileri ve Klinik Notlar")
c_info1, c_info2 = st.columns([3, 1])
with c_info1:
    h_isim = st.text_input("Hastanın Adı Soyadı")
with c_info2:
    h_yas = st.number_input("Yaş", min_value=0, max_value=120, step=1)

h_yorum = st.text_area("Görüşme Hakkında Klinik Yorumlar", height=150, placeholder="Hastanın tutumu, test sırasındaki davranışları vb...")

st.divider()

# --- 2. BÖLÜM: KART TERCİHLERİ ---
st.subheader("Kart Tercihleri")
col_b1, col_b2 = st.columns(2)

with col_b1:
    st.write("**En Beğendiği Kart(lar)**")
    beğenilen_kartlar = st.multiselect("Kart seçin", options=[f"Kart {i}" for i in range(1, 11)], key="best")
    beğenilen_neden = st.text_area("Beğenme Nedeni", height=80, key="best_reason")

with col_b2:
    st.write("**En Beğenmediği Kart(lar)**")
    beğenilmeyen_kartlar = st.multiselect("Kart seçin", options=[f"Kart {i}" for i in range(1, 11)], key="worst")
    beğenilmeyen_neden = st.text_area("Beğenmeme Nedeni", height=80, key="worst_reason")

st.divider()

# --- 3. BÖLÜM: KOD GİRİŞİ ---
st.subheader("Kart Yanıtları (Kodlar)")
GRUP_1 = ["G", "D", "Dd", "Gbl", "Dbl"]
GRUP_2 = ["F", "F+", "F-", "F+-", "FC", "FC'", "Fclob", "C", "C'", "Clob", "CF", "C'F", "ClobF", "K", "Kan", "Kob", "Kp", "E", "EF", "FE"]
GRUP_3 = ["H", "Hd", "(H)", "A", "Ad", "(A)", "Nesne", "Bitki", "Anatomi", "Coğrafya", "Doğa"]
YAN_DAL = ["Ban", "Reddetme", "Şok"]
HEPSI_TANIMLI = set(GRUP_1 + GRUP_2 + GRUP_3 + YAN_DAL)

kart_verileri = []
# Kartları 2 sütun halinde gösterelim ki çok yer kaplamasın
c_k1, c_k2 = st.columns(2)
for i in range(1, 11):
    target_col = c_k1 if i <= 5 else c_k2
    with target_col:
        kart_verileri.append(st.text_area(f"Kart {i} Kodları", key=f"kart_{i}", height=80, help="Yanıtları ; ile ayırın."))

# --- 4. BÖLÜM: ANALİZ VE RAPORLAMA ---
if st.button("Analizi Gerçekleştir ve Raporu Hazırla"):
    total_r = 0
    r_8910 = 0
    all_codes = []
    
    for i, data in enumerate(kart_verileri, 1):
        if data.strip():
            raw_responses = data.replace(';', '\n').split('\n')
            for resp in raw_responses:
                clean_resp = resp.strip()
                if not clean_resp or clean_resp.lower() == "reddetme": continue
                total_r += 1
                if i in [8, 9, 10]: r_8910 += 1
                for k in clean_resp.replace(",", " ").split():
                    if k: all_codes.append(k)

    if total_r > 0:
        counts = Counter(all_codes)
        
        # Hesaplamalar
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

        # Sonuç Paneli
        st.subheader(f"Analiz Sonuçları (R: {total_r})")
        col_1, col_2, col_3, col_4 = st.columns(4)
        with col_1: st.markdown(f'<div class="metric-container bg-sari"><div class="metric-label">%G / %D</div><div class="metric-value">%{calc["%G"]:.0f} / %{calc["%D"]:.0f}</div></div>', unsafe_allow_html=True)
        with col_2: st.markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">%F</div><div class="metric-value">%{calc["%F"]:.0f}</div></div>', unsafe_allow_html=True)
        with col_3: st.markdown(f'<div class="metric-container bg-mor"><div class="metric-label">%A / %H</div><div class="metric-value">%{calc["%A"]:.0f} / %{calc["%H"]:.0f}</div></div>', unsafe_allow_html=True)
        with col_4: st.markdown(f'<div class="metric-container bg-kirmizi"><div class="metric-label">TRI / RC</div><div class="metric-value">%{calc["TRI"]:.0f} / %{calc["RC"]:.0f}</div></div>', unsafe_allow_html=True)

        # Word Raporu Oluşturma
        try:
            doc = Document()
            doc.add_heading('Rorschach Test Raporu', 0)
            
            # Hasta Bilgileri
            p = doc.add_paragraph()
            p.add_run('Hasta Adı: ').bold = True
            p.add_run(f'{h_isim}\n')
            p.add_run('Yaş: ').bold = True
            p.add_run(f'{h_yas}\n')
            
            doc.add_heading('Klinik Gözlem ve Yorumlar', level=1)
            doc.add_paragraph(h_yorum)
            
            doc.add_heading('Kart Tercihleri', level=1)
            doc.add_paragraph(f"En Beğenilen Kartlar: {', '.join(beğenilen_kartlar)}")
            doc.add_paragraph(f"Neden: {beğenilen_neden}")
            doc.add_paragraph(f"En Beğenilmeyen Kartlar: {', '.join(beğenilmeyen_kartlar)}")
            doc.add_paragraph(f"Neden: {beğenilmeyen_neden}")
            
            doc.add_heading('Psikogram Verileri', level=1)
            doc.add_paragraph(f'Toplam Yanıt (R): {total_r}')
            table = doc.add_table(rows=1, cols=2)
            for k, v in calc.items():
                row = table.add_row().cells
                row[0].text = k
                row[1].text = f"%{v:.0f}"
            
            doc.add_paragraph('\n\nİmza:\nKerem Birgül')
            
            bio = BytesIO()
            doc.save(bio)
            st.download_button(label="📄 Klinik Raporu Word Olarak İndir", data=bio.getvalue(), file_name=f"{h_isim}_Rorschach_Raporu.docx")
        except:
            st.info("Rapor hazırlanıyor...")

    else:
        st.warning("Veri girişi yapılmadı.")

st.markdown('<div class="footer">Kerem Birgül</div>', unsafe_allow_html=True)
