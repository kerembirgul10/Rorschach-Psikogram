import streamlit as st
from collections import Counter

# Sayfa yapılandırması
st.set_page_config(page_title="Rorschach Psikogram", layout="wide")

# Kutuların boyutunu sabitleyen CSS
st.markdown("""
    <style>
    textarea {
        resize: none !important;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    /* Pastel Renk Grupları */
    .sari-kutu { background-color: #fff9c4; padding: 20px; border-radius: 10px; border: 1px solid #fbc02d; margin-bottom: 10px; }
    .kirmizi-kutu { background-color: #ffecb3; padding: 20px; border-radius: 10px; border: 1px solid #ffa000; margin-bottom: 10px; }
    .mor-kutu { background-color: #f3e5f5; padding: 20px; border-radius: 10px; border: 1px solid #9c27b0; margin-bottom: 10px; }
    .footer { position: fixed; left: 0; bottom: 10px; width: 100%; text-align: center; color: #bdc3c7; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

st.title("Rorschach Psikogram")

# --- GRUP TANIMLAMALARI ---
GRUP_1 = ["G", "D", "Dd", "Gbl", "Dbl"]
GRUP_2 = ["F", "F+", "F-", "F+-", "FC", "FC'", "Fclob", "C", "C'", "Clob", "CF", "C'F", "ClobF", "K", "Kan", "Kob", "Kp", "E", "EF", "FE"]
GRUP_3 = ["H", "Hd", "(H)", "A", "Ad", "(A)", "Nesne", "Bitki", "Anatomi", "Coğrafya", "Doğa"]
YAN_DAL = ["Ban", "Reddetme", "Şok"]
HEPSI_TANIMLI = set(GRUP_1 + GRUP_2 + GRUP_3 + YAN_DAL)

st.info("Yanıtları birbirinden ayırmak için her yanıtın sonuna noktalı virgül (;) koyun. Örn: G F+ H; D F- A")

kart_verileri = []
for i in range(1, 11):
    kod_girisi = st.text_area(f"Kart {i}", key=f"kart_{i}", height=100)
    kart_verileri.append(kod_girisi)

if st.button("Analiz"):
    toplam_r_sayisi = 0
    kart_8910_r_sayisi = 0
    tum_kodlar = []
    
    for i, ham_veri in enumerate(kart_verileri, 1):
        if ham_veri.strip():
            # Yanıtları noktalı virgül veya yeni satıra göre ayır
            satirlar = ham_veri.replace(';', '\n').split('\n')
            for satir in satirlar:
                temiz_satir = satir.strip()
                if temiz_satir == "" or temiz_satir.lower() == "reddetme":
                    continue
                
                toplam_r_sayisi += 1
                if i in [8, 9, 10]:
                    kart_8910_r_sayisi += 1
                
                kelimeler = temiz_satir.replace(",", " ").split()
                for k in kelimeler:
                    if k != "":
                        tum_kodlar.append(k)

    if toplam_r_sayisi > 0:
        st.subheader(f"R:{toplam_r_sayisi}")
        st.divider()

        kod_sayilari = Counter(tum_kodlar)
        
        # Kod Dağılımı Gösterimi
        def grubu_yazdir(liste):
            bulunanlar = [k for k in liste if kod_sayilari[k] > 0]
            if bulunanlar:
                render_cols = st.columns(max(len(bulunanlar), 1))
                for idx, k in enumerate(bulunanlar):
                    render_cols[idx].write(f"**{k}:** {kod_sayilari[k]}")

        grubu_yazdir(GRUP_1)
        grubu_yazdir(GRUP_2)
        grubu_yazdir(GRUP_3)
        grubu_yazdir(YAN_DAL)

        istisnalar = [k for k in kod_sayilari if k not in HEPSI_TANIMLI]
        if istisnalar:
            istisna_metni = " ".join([f"**{k}:** {kod_sayilari[k]} | " for k in istisnalar])
            st.info(istisna_metni)

        st.divider()

        # --- HESAPLAMALAR VE RENKLİ KUTULAR ---
        # Veri Hazırlama
        g_yuzde = (kod_sayilari["G"] / toplam_r_sayisi) * 100
        d_yuzde = (kod_sayilari["D"] / toplam_r_sayisi) * 100
        f_yuzde = (sum(kod_sayilari[k] for k in ["F", "F+", "F-", "F+-"]) / toplam_r_sayisi) * 100
        a_yuzde = ((kod_sayilari["A"] + kod_sayilari["Ad"]) / toplam_r_sayisi) * 100
        h_yuzde = ((kod_sayilari["H"] + kod_sayilari["Hd"]) / toplam_r_sayisi) * 100
        rc_yuzde = (kart_8910_r_sayisi / toplam_r_sayisi) * 100
        
        puan_tri = (kod_sayilari["FC"]+kod_sayilari["FC'"]+kod_sayilari["Fclob"])*0.5 + \
                   (kod_sayilari["CF"]+kod_sayilari["C'F"]+kod_sayilari["ClobF"])*1.0 + \
                   (kod_sayilari["C"]+kod_sayilari["C'"]+kod_sayilari["Clob"])*1.5
        tri_sonuc = (kod_sayilari["K"] / puan_tri) * 100 if puan_tri > 0 else 0

        # Renkli Kutuların Oluşturulması
        c1, c2, c3, c4 = st.columns(4)

        with c1: # SARI KUTU
            st.markdown(f'<div class="sari-kutu"><b>%G:</b> %{g_yuzde:.0f}<br><b>%D:</b> %{d_yuzde:.0f}</div>', unsafe_allow_html=True)

        with c2: # KIRMIZI KUTU (F)
            st.markdown(f'<div class="kirmizi-kutu"><b>%F:</b> %{f_yuzde:.0f}</div>', unsafe_allow_html=True)

        with c3: # MOR KUTU
            st.markdown(f'<div class="mor-kutu"><b>%A:</b> %{a_yuzde:.0f}<br><b>%H:</b> %{h_yuzde:.0f}</div>', unsafe_allow_html=True)

        with c4: # KIRMIZI KUTU (TRI ve RC)
            st.markdown(f'<div class="kirmizi-kutu"><b>TRI:</b> %{tri_sonuc:.0f}<br><b>RC:</b> %{rc_yuzde:.0f}</div>', unsafe_allow_html=True)

    else:
        st.error("Giriş yapılmadı.")

# Footer İmza
st.markdown('<div class="footer">Kerem Birgül</div>', unsafe_allow_html=True)
