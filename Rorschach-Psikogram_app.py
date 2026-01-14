import streamlit as st
from collections import Counter

st.set_page_config(page_title="Kod Analiz Sistemi", layout="centered")

st.title("📊 Kart Kod Analiz Paneli")

# --- TANIMLI LİSTELER (Sıralama için) ---
KOD_LISTESI = [
    # Grup 1 Kodları
    "G", "D", "Dd", "Gbl", "Dbl",
    # Grup 2 Kodları
    "F", "F+", "F-", "F+-", "FC", "FC'", "Fclob", "C", "C'", "Clob", 
    "CF", "C'F", "ClobF", "K", "Kan", "Kob", "Kp", "E", "EF", "FE",
    # Grup 3 Kodları
    "H", "Hd", "(H)", "A", "Ad", "(A)", "Nesne", "Bitki", "Anatomi", "Coğrafya", "Doğa"
]
YAN_DAL_LISTESI = ["Ban", "Reddetme", "Şok"]

# --- GİRİŞ ALANLARI ---
st.subheader("Kart Yanıtlarını Girin")
kart_verileri = []

for i in range(1, 11):
    kod_girisi = st.text_area(f"Kart {i}:", key=f"kart_{i}", height=90)
    kart_verileri.append(kod_girisi)

if st.button("🚀 Kodları Analiz Et"):
    toplam_r_sayisi = 0
    tum_kodlar = []
    
    for ham_veri in kart_verileri:
        if ham_veri.strip():
            satirlar = ham_veri.strip().split('\n')
            for satir in satirlar:
                temiz_satir = satir.strip()
                # Sadece "Reddetme" yazan yanıtı R olarak kabul etme
                if temiz_satir == "" or temiz_satir.lower() == "reddetme":
                    continue
                
                toplam_r_sayisi += 1
                kelimeler = temiz_satir.replace(",", " ").split()
                for k in kelimeler:
                    if k != "":
                        tum_kodlar.append(k)

    if toplam_r_sayisi > 0:
        st.subheader(f"Toplam Yanıt: {toplam_r_sayisi} (R)")
        st.divider()

        kod_sayilari = Counter(tum_kodlar)
        hepsi_tanimli = set(KOD_LISTESI + YAN_DAL_LISTESI)
        
        # --- 1. KISIM: İSTİSNALAR (Renkli Kutu) ---
        istisnalar = [k for k in kod_sayilari if k not in hepsi_tanimli]
        if istisnalar:
            istisna_metni = "\n"
            for k in istisnalar:
                istisna_metni += f"{k}: {kod_sayilari[k]}  \n"
            st.info(istisna_metni)

        # --- 2. KISIM: ANA KODLAR VE YAN DALLAR ---
        # Kodları dikeyde güzel göstermek için sütun kullanalım ama başlık yazmayalım
        col1, col2 = st.columns(2)
        
        with col1:
            # Ana listedeki kodları sırayla yazdır
            for k in KOD_LISTESI:
                if kod_sayilari[k] > 0:
                    st.write(f"**{k}:** {kod_sayilari[k]}")
        
        with col2:
            # Yan dal kodlarını listenin en altına gelecek şekilde yazdır
            for k in YAN_DAL_LISTESI:
                if kod_sayilari[k] > 0:
                    st.write(f"**{k}:** {kod_sayilari[k]}")
                    
    else:
        st.error("Lütfen analiz için geçerli bir yanıt girin.")
        
