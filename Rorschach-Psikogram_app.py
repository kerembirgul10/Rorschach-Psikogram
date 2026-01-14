import streamlit as st
from collections import Counter

st.set_page_config(page_title="Kod Analiz Sistemi", layout="centered")

st.title("📊 Kart Kod Analiz Paneli")

# --- TANIMLI LİSTELER ---
ANA_VE_YAN_LISTE = [
    # Grup 1
    "G", "D", "Dd", "Gbl", "Dbl",
    # Grup 2
    "F", "F+", "F-", "F+-", "FC", "FC'", "Fclob", "C", "C'", "Clob", 
    "CF", "C'F", "ClobF", "K", "Kan", "Kob", "Kp", "E", "EF", "FE",
    # Grup 3
    "H", "Hd", "(H)", "A", "Ad", "(A)", "Nesne", "Bitki", "Anatomi", "Coğrafya", "Doğa",
    # Yan Dallar
    "Ban", "Reddetme", "Şok"
]

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
                # "Reddetme" yanıtını R olarak sayma
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
        
        # --- SIRALI LİSTELEME ---
        # Önce listede olanları senin sıranla yazdır
        for k in ANA_VE_YAN_LISTE:
            if kod_sayilari[k] > 0:
                st.write(f"**{k}:** {kod_sayilari[k]}")
        
        # --- İSTİSNALARI RENKLİ KUTUDA SIRALA ---
        # Listede olmayan ama girişi yapılan kodları bul
        tanimsizlar = [k for k in kod_sayilari if k not in ANA_VE_YAN_LISTE]
        
        for k in tanimsizlar:
            # Grup ismi yazmadan sadece pastel renkli kutu içinde kod ve sayısı
            st.info(f"**{k}:** {kod_sayilari[k]}")
                    
    else:
        st.error("Lütfen analiz için geçerli bir yanıt girin.")
