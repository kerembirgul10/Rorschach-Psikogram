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
        p10 = sum(1 for k in tum_kodlar if k in ["CF", "C'F", "ClobF"]) * 1.0
        p15 = sum(1 for k in tum_kodlar if k in ["C", "C'", "Clob"]) * 1.5
        
        toplam_puan = p05 + p10 + p15
        
        # --- ÖZET SONUÇLAR ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Toplam Kod", len(tum_kodlar))
        col2.metric("Toplam Puan", toplam_puan)
        if toplam_puan > 0:
            oran = (l14_degeri / toplam_puan) * 100
            col3.metric("Sonuç Oranı", f"%{oran:.0f}")

        st.divider()

        # --- TEKİL KOD LİSTESİ (SADECE ADETLER) ---
        st.subheader("🔍 Kod Sayıları")
        
        # Kodları say ve sırala (en çoktan en aza)
        kod_sayilari = Counter(tum_kodlar)
        
        # Sonuçları yan yana sütunlarda göster (daha az yer kaplaması için)
        detay_cols = st.columns(4)
        for idx, (kod, adet) in enumerate(kod_sayilari.items()):
            with detay_cols[idx % 4]:
                st.write(f"**{kod}:** {adet} adet")
                
    else:
        st.error("Lütfen en az bir geçerli kod girişi yapın.")
