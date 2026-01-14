import streamlit as st
from collections import Counter

st.set_page_config(page_title="Rorschach Psikogram", layout="wide")

# Başlık
st.title("📊 Rorschach Psikogram")

# --- GRUP TANIMLAMALARI ---
GRUP_1 = ["G", "D", "Dd", "Gbl", "Dbl"]
GRUP_2 = [
    "F", "F+", "F-", "F+-", "FC", "FC'", "Fclob", "C", "C'", "Clob", 
    "CF", "C'F", "ClobF", "K", "Kan", "Kob", "Kp", "E", "EF", "FE"
]
GRUP_3 = ["H", "Hd", "(H)", "A", "Ad", "(A)", "Nesne", "Bitki", "Anatomi", "Coğrafya", "Doğa"]
YAN_DAL = ["Ban", "Reddetme", "Şok"]

HEPSI_TANIMLI = set(GRUP_1 + GRUP_2 + GRUP_3 + YAN_DAL)

# --- GİRİŞ ALANLARI ---
st.subheader("Kartlar")
kart_verileri = []

for i in range(1, 11):
    kod_girisi = st.text_area(f"Kart {i}", key=f"kart_{i}", height=80)
    kart_verileri.append(kod_girisi)

if st.button("🚀 Analiz"):
    toplam_r_sayisi = 0
    tum_kodlar = []
    
    for ham_veri in kart_verileri:
        if ham_veri.strip():
            satirlar = ham_veri.strip().split('\n')
            for satir in satirlar:
                temiz_satir = satir.strip()
                if temiz_satir == "" or temiz_satir.lower() == "reddetme":
                    continue
                
                toplam_r_sayisi += 1
                kelimeler = temiz_satir.replace(",", " ").split()
                for k in kelimeler:
                    if k != "":
                        tum_kodlar.append(k)

    if toplam_r_sayisi > 0:
        # Kodları say
        kod_sayilari = Counter(tum_kodlar)
        
        # --- HESAPLAMALAR (%G ve %D) ---
        g_sayisi = kod_sayilari["G"]
        d_sayisi = kod_sayilari["D"]
        
        g_orani = (g_sayisi / toplam_r_sayisi) * 100
        d_orani = (d_sayisi / toplam_r_sayisi) * 100

        # Üst Bilgi Satırı
        st.subheader(f"R:{toplam_r_sayisi}")
        
        # Oranları Yan Yana Göster
        col_g, col_d = st.columns(2)
        col_g.metric("%G", f"%{g_orani:.0f}")
        col_d.metric("%D", f"%{d_orani:.0f}")
        
        st.divider()

        # --- KODLARI YATAY GRUPLAR HALİNDE GÖSTER ---
        def grubu_yazdir(liste):
            bulunanlar = [k for k in liste if kod_sayilari[k] > 0]
            if bulunanlar:
                render_cols = st.columns(len(bulunanlar) if len(bulunanlar) > 0 else 1)
                for idx, k in enumerate(bulunanlar):
                    render_cols[idx].write(f"**{k}:** {kod_sayilari[k]}")
                st.write("") 

        grubu_yazdir(GRUP_1)
        grubu_yazdir(GRUP_2)
        grubu_yazdir(GRUP_3)
        grubu_yazdir(YAN_DAL)

        st.divider()

        # --- İSTİSNALAR (Tek Bir Kutu İçinde) ---
        istisnalar = [k for k in kod_sayilari if k not in HEPSI_TANIMLI]
        if istisnalar:
            istisna_metni = ""
            for k in istisnalar:
                istisna_metni += f"**{k}:** {kod_sayilari[k]} &nbsp;&nbsp;&nbsp; "
            st.info(istisna_metni)
                    
    else:
        st.error("Giriş yapılmadı.")
