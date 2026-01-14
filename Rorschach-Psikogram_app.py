import streamlit as st
from collections import Counter

st.set_page_config(page_title="R Analiz Sistemi", layout="centered")

st.title("📊 Kart Yanıt (R) Analiz Sistemi")

# --- GRUP TANIMLAMALARI ---
GRUP_1 = ["G", "D", "Dd", "Gbl", "Dbl"]
GRUP_2 = [
    "F", "F+", "F-", "F+-", "FC", "FC'", "Fclob", "C", "C'", "Clob", 
    "CF", "C'F", "ClobF", "K", "Kan", "Kob", "Kp", "E", "EF", "FE"
]
GRUP_3 = ["H", "Hd", "(H)", "A", "Ad", "(A)", "Nesne", "Bitki", "Anatomi", "Coğrafya", "Doğa"]
OZEL_GRUP = ["Ban", "Reddetme", "Şok"]

# --- GİRİŞ ALANLARI ---
st.subheader("Kart Yanıtlarını Girin")
kart_verileri = []

for i in range(1, 11):
    kod_girisi = st.text_area(f"Kart {i}:", key=f"kart_{i}", height=100)
    kart_verileri.append(kod_girisi)

st.divider()
l14_degeri = st.number_input("🎯 L14 Değeri:", value=7.0)

if st.button("🚀 Analizi Başlat"):
    toplam_r_sayisi = 0
    tum_gecerli_kodlar = []
    ozel_kodlar_listesi = []
    
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
                    if k in OZEL_GRUP:
                        ozel_kodlar_listesi.append(k)
                    elif k != "":
                        tum_gecerli_kodlar.append(k)

    if toplam_r_sayisi > 0:
        # --- PUAN HESAPLAMA ---
        p05 = sum(1 for k in tum_gecerli_kodlar if k in ["FC", "FC'", "Fclob"]) * 0.5
        p10 = sum(1 for k in tum_gecerli_kodlar if k in ["CF", "C'F", "ClobF"]) * 1.0
        p15 = sum(1 for k in tum_gecerli_kodlar if k in ["C", "C'", "Clob"]) * 1.5
        toplam_puan = p05 + p10 + p15
        
        # --- ÖZET SONUÇLAR ---
        st.subheader("📌 Genel Sonuçlar")
        m1, m2, m3 = st.columns(3)
        m1.metric("Toplam Yanıt", f"{toplam_r_sayisi} (R)")
        m2.metric("Toplam Puan", toplam_puan)
        if toplam_puan > 0:
            oran = (l14_degeri / toplam_puan) * 100
            m3.metric("Sonuç Oranı", f"%{oran:.0f}")

        st.divider()

        # --- KOD DAĞILIMI ---
        st.subheader("🔍 Kod Dağılım Analizi")
        kod_sayilari = Counter(tum_gecerli_kodlar)
        ozel_sayilari = Counter(ozel_kodlar_listesi)
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown("**1. Grup**")
            for k in GRUP_1:
                if kod_sayilari[k] > 0:
                    st.write(f"**{k}:** {kod_sayilari[k]}")
        
        with c2:
            st.markdown("**2. Grup**")
            for k in GRUP_2:
                if kod_sayilari[k] > 0:
                    st.write(f"**{k}:** {kod_sayilari[k]}")
        
        with c3:
            st.markdown("**3. Grup**")
            for k in GRUP_3:
                if kod_sayilari[k] > 0:
                    st.write(f"**{k}:** {kod_sayilari[k]}")

        st.divider()
        
        # --- ALT KISIM: ÖZEL GRUP VE İSTİSNALAR ---
        alt_c1, alt_c2 = st.columns(2)
        
        with alt_c1:
            st.markdown("**🛡️ Yan Dal (Ban/Şok/Red)**")
            for k in OZEL_GRUP:
                if ozel_sayilari[k] > 0:
                    st.write(f"**{k}:** {ozel_sayilari[k]}")

        with alt_c2:
            st.markdown("**⚠️ İstisnalar (Tanımsız)**")
            hepsi = set(GRUP_1 + GRUP_2 + GRUP_3 + OZEL_GRUP)
            # İstisnaları bir kutu (info) içinde gösterelim
            istisna_metni = ""
            for k, adet in kod_sayilari.items():
                if k not in hepsi:
                    istisna_metni += f"**{k}:** {adet}  \n"
            
            if istisna_metni:
                st.info(istisna_metni)
            else:
                st.write("İstisna kod bulunamadı.")
                    
    else:
        st.error("Hesaplanacak geçerli bir (R) yanıtı bulunamadı.")
