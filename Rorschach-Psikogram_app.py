import streamlit as st
from collections import Counter

st.set_page_config(page_title="Detaylı Kod Analizi", layout="wide")

st.title("📊 10 Kartlı Detaylı Analiz Sistemi")

# --- KOD GRUPLARI TANIMLAMA ---
GRUP_1 = ["G", "D", "Dd", "Gbl", "Dbl"]
GRUP_2 = [
    "F", "F+", "F-", "F+-", "FC", "Fc'", "Fclob", "C", "C'", "Clob", 
    "CF", "C'F", "ClobF", "K", "Kan", "Kob", "Kp", "E", "EF", "FE"
]
GRUP_3 = ["H", "Hd", "(H)", "A", "Ad", "(A)", "Nesne", "Bitki", "Anatomi", "Coğrafya", "Doğa"]
YAN_DAL = ["Ban", "Reddetme", "Şok"]

# --- GİRİŞ ALANI ---
kart_verileri = []
cols = st.columns(2)
for i in range(1, 11):
    with cols[0] if i <= 5 else cols[1]:
        kod_girisi = st.text_area(f"📍 Kart {i} Kodları:", key=f"kart_{i}", height=80, placeholder="Örn: G FC' A")
        kart_verileri.append(kod_girisi)

st.divider()
l14_degeri = st.number_input("🎯 L14 Değerini Girin:", value=7.0)

if st.button("🚀 Detaylı Analiz Yap"):
    tum_kodlar_listesi = []
    
    # Verileri Topla ve Filtrele
    for ham_veri in kart_verileri:
        if ham_veri:
            # Kelimeleri ayır
            kelimeler = ham_veri.replace(",", " ").split()
            for k in kelimeler:
                # Yan dal kodlarını ve listede olmayan gereksiz boşlukları ele
                if k not in YAN_DAL and k != "":
                    tum_kodlar_listesi.append(k)

    if tum_kodlar_listesi:
        # --- HESAPLAMA MANTIĞI (Önceki Puanlama Sistemine Göre) ---
        # Not: Buradaki puan katsayılarını önceki konuşmamıza göre korudum.
        p05 = sum(1 for k in tum_kodlar_listesi if k in ["FC", "Fc'", "Fclob"]) * 0.5
        p10 = sum(1 for k in tum_kodlar_listesi if k in ["CF", "C'F", "ClobF"]) * 1.0
        p15 = sum(1 for k in tum_kodlar_listesi if k in ["C", "C'", "Clob"]) * 1.5
        # Diğer gruplar için puan istersen buraya ekleyebiliriz.
        
        toplam_puan = p05 + p10 + p15
        
        # --- SONUÇ EKRANI ---
        st.subheader("📌 Genel Sonuçlar")
        res_col1, res_col2, res_col3 = st.columns(3)
        
        with res_col1:
            st.metric("Toplam Geçerli Kod", len(tum_kodlar_listesi))
        with res_col2:
            st.metric("Hesaplanan Puan", toplam_puan)
        with res_col3:
            if toplam_puan > 0:
                oran = (l14_degeri / toplam_puan) * 100
                st.metric("Sonuç Oranı", f"%{oran:.0f}")

        st.divider()

        # --- DETAYLI İSTATİSTİK (ÇETELE) ---
        st.subheader("🔍 Kod Dağılım Analizi")
        
        # Kodları say
        kod_sayilari = Counter(tum_kodlar_listesi)
        
        # Gruplara göre dağılımı göster
        cat_col1, cat_col2, cat_col3 = st.columns(3)
        
        with cat_col1:
            st.info("**1. Grup (G, D, Dd...)**")
            for k in GRUP_1:
                if kod_sayilari[k] > 0:
                    st.write(f"**{k}:** {kod_sayilari[k]} adet")
        
        with cat_col2:
            st.success("**2. Grup (F, FC, C, K...)**")
            for k in GRUP_2:
                if kod_sayilari[k] > 0:
                    st.write(f"**{k}:** {kod_sayilari[k]} adet")
                    
        with cat_col3:
            st.warning("**3. Grup (H, A, Doğa...)**")
            for k in GRUP_3:
                if kod_sayilari[k] > 0:
                    st.write(f"**{k}:** {kod_sayilari[k]} adet")

        # Gruplar dışındaki bilinmeyen kodlar varsa göster
        bilinmeyenler = [k for k in kod_sayilari if k not in GRUP_1 + GRUP_2 + GRUP_3]
        if bilinmeyenler:
            st.error("**Tanımlanmamış Diğer Kodlar**")
            for k in bilinmeyenler:
                st.write(f"**{k}:** {kod_sayilari[k]} adet")
    else:
        st.error("Hesaplanacak geçerli bir kod bulunamadı!")
