import streamlit as st
from collections import Counter

st.set_page_config(page_title="R Analiz Sistemi", layout="wide")

st.title("📊 Gelişmiş Kart Yanıt (R) Analizi")

# --- GRUP TANIMLAMALARI ---
GRUP_1 = ["G", "D", "Dd", "Gbl", "Dbl"]
GRUP_2 = [
    "F", "F+", "F-", "F+-", "FC", "FC'", "Fclob", "C", "C'", "Clob", 
    "CF", "C'F", "ClobF", "K", "Kan", "Kob", "Kp", "E", "EF", "FE"
]
GRUP_3 = ["H", "Hd", "(H)", "A", "Ad", "(A)", "Nesne", "Bitki", "Anatomi", "Coğrafya", "Doğa"]
ELENECEK_KODLAR = ["Ban", "Reddetme", "Şok"]

# --- GİRİŞ ALANLARI ---
st.subheader("Kart Yanıtlarını Girin")
kart_verileri = []
cols = st.columns(2)
for i in range(1, 11):
    with cols[0] if i <= 5 else cols[1]:
        kod_girisi = st.text_area(f"Kart {i}:", key=f"kart_{i}", height=100)
        kart_verileri.append(kod_girisi)

st.divider()
l14_degeri = st.number_input("🎯 L14 Değeri:", value=7.0)

if st.button("🚀 Analizi Başlat"):
    toplam_r_sayisi = 0
    tum_gecerli_kodlar = []
    
    for ham_veri in kart_verileri:
        if ham_veri.strip():
            satirlar = ham_veri.strip().split('\n')
            for satir in satirlar:
                temiz_satir = satir.strip()
                # 1. KURAL: Sadece "Reddetme" yazan yanıtı R olarak kabul etme
                if temiz_satir == "" or temiz_satir.lower() == "reddetme":
                    continue
                
                toplam_r_sayisi += 1
                kelimeler = temiz_satir.replace(",", " ").split()
                for k in kelimeler:
                    if k not in ELENECEK_KODLAR and k != "":
                        tum_gecerli_kod
