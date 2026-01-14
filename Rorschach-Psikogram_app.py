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
                        tum_gecerli_kodlar.append(k)

    if toplam_r_sayisi > 0:
        # --- PUAN HESAPLAMA ---
        p05 = sum(1 for k in tum_gecerli_kodlar if k in ["FC", "FC'", "Fclob"]) * 0.5
        p10 = sum(1 for k in tum_gecerli_kodlar if k in ["CF", "C'F", "ClobF"]) * 1.0
        p15 = sum(1 for k in tum_gecerli_kodlar if k in ["C", "C'", "Clob"]) * 1.5
        toplam_puan = p05 + p10 + p15
        
        # --- ÖZET METRİKLER ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Toplam Yanıt", f"{toplam_r_sayisi} (R)")
        m2.metric("Toplam Puan", toplam_puan)
        if toplam_puan > 0:
            oran = (l14_degeri / toplam_puan) * 100
            m3.metric("Sonuç Oranı", f"%{oran:.0f}")

        st.divider()

        # --- KOD DAĞILIMI (GRUPLARA GÖRE ALT ALTA) ---
        st.subheader("🔍 Kod Dağılım Analizi")
        kod_sayilari = Counter(tum_gecerli_kodlar)
        
        c1, c2, c3, c4 = st.columns(4)
        
        # Grup 1
        with c1:
            for k in GRUP_1:
                if kod_sayilari[k] > 0:
                    st.write(f"**{k}:** {kod_sayilari[k]}")
        
        # Grup 2
        with c2:
            for k in GRUP_2:
                if kod_sayilari[k] > 0:
                    st.write(f"**{k}:** {kod_sayilari[k]}")
        
        # Grup 3
        with c3:
            for k in GRUP_3:
                if kod_sayilari[k] > 0:
                    st.write(f"**{k}:** {kod_sayilari[k]}")
        
        # İstisna/Tanımsız Kodlar
        with c4:
            st.write("*Diğer:*")
            hepsi = set(GRUP_1 + GRUP_2 + GRUP_3)
            for k, adet in kod_sayilari.items():
                if k not in hepsi:
                    st.write(f"**{k}:** {adet}")
                    
    else:
        st.error("Hesaplanacak geçerli bir (R) yanıtı bulunamadı.")
