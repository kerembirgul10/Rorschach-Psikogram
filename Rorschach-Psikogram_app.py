import streamlit as st
from collections import Counter

st.set_page_config(page_title="R Analiz Sistemi", page_icon="📈", layout="centered")

st.title("📊 Kart Yanıt (R) ve Kod Analizi")

# --- TANIMLAMALAR ---
# Sayılmayacak ve elenecek yan dal kodları
YAN_DAL = ["Ban", "Reddetme", "Şok"]

# --- GİRİŞ ALANLARI ---
st.subheader("Kart Yanıtlarını Girin")
st.info("Her bir yanıtı (R) yeni bir satıra yazın. Örn: \n\nG F+ H Ban\nG F+ Nesne Ban")

kart_verileri = []
for i in range(1, 11):
    # Çoklu yanıt girilebilmesi için text_area kullandık
    kod_girisi = st.text_area(f"Kart {i}:", key=f"kart_{i}", height=100)
    kart_verileri.append(kod_girisi)

st.divider()
l14_degeri = st.number_input("🎯 L14 Değeri:", value=7.0)

if st.button("🚀 Analiz Et"):
    toplam_r_sayisi = 0
    tum_gecerli_kodlar = []
    
    for ham_veri in kart_verileri:
        if ham_veri.strip():
            # Satırları ayır (Her satır bir Yanıttır/R)
            satirlar = ham_veri.strip().split('\n')
            
            for satir in satirlar:
                if satir.strip():
                    toplam_r_sayisi += 1  # Her dolu satır bir R artırır
                    
                    # Satır içindeki kodları işle
                    kelimeler = satir.replace(",", " ").split()
                    for k in kelimeler:
                        # Yan dalları ele ve listeye ekle
                        if k not in YAN_DAL and k.strip() != "":
                            tum_gecerli_kodlar.append(k)

    if toplam_r_sayisi > 0:
        # --- HESAPLAMA MANTIĞI ---
        p05 = sum(1 for k in tum_gecerli_kodlar if k in ["FC", "Fc'", "Fclob"]) * 0.5
        p10 = sum
