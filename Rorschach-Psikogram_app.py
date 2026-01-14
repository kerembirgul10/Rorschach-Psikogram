import streamlit as st
from collections import Counter

st.set_page_config(page_title="Kod Analizi", page_icon="📈", layout="centered")

st.title("📊 Kart Kod Analiz Sistemi")

# --- TANIMLAMALAR ---
# Yan dal kodları (Sayıma girmeyecek olanlar)
YAN_DAL = ["Ban", "Reddetme", "Şok"]

# --- GİRİŞ ALANLARI ---
st.subheader("Kart Verilerini Girin")
kart_verileri = []
# 10 Kart girişi
for i in range(1, 11):
    kod_girisi = st.text_input(f"Kart {i}:", key=f"kart_{i}", placeholder="Örn: G FC' A")
    kart_verileri.append(kod_girisi)

st.divider()
l14_degeri = st.number_input("🎯 L14 Değeri:", value=7.0)

if st.button("🚀 Analiz Et"):
    tum_kodlar = []
    
    # Tüm kartlardaki kelimeleri topla ve filtrele
    for ham_veri in kart_verileri:
        if ham_veri:
            # Boşluklara göre böl ve temizle
            kelimeler = ham_veri.replace(",", " ").split()
            for k in kelimeler:
                # Sadece Yan Dal listesinde OLMAYANLARI listeye ekle
                if k not in YAN_DAL and k.strip() != "":
                    tum_kodlar.append(k)

    if tum_kodlar:
        # --- HESAPLAMA MANTIĞI ---
        p05 = sum(1 for k in tum_kodlar if k in ["FC", "Fc'", "Fclob"]) * 0.5
        p10 = sum(1 for k in tum_kodlar if k in
