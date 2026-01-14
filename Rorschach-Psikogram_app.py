import streamlit as st
from collections import Counter

st.set_page_config(page_title="Rorschach Psikogram", layout="wide")

# Başlık Güncellemesi
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

# Kartları tam genişlikte alt alta sıralıyoruz
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
                # "Reddetme" tek başına bir yanıt ise R sayma
                if temiz_satir == "" or temiz_satir.lower() == "reddetme":
                    continue
                
                toplam_r_sayisi += 1
                kelimeler = temiz_satir.replace(",", " ").split()
                for k in kelimeler:
                    if k != "":
                        tum_kodlar.append(k)

    if toplam_r_sayisi > 0:
        st.subheader(f"R:{toplam_r_sayisi}")
        st.divider()

        kod_sayilari = Counter(tum_kodlar)
        
        # --- KODLARI YAN YANA GÖSTERME (GRUP GRUP) ---
        
        # Fonksiyon: Grubu yatayda yazdırır
        def grubu_yazdir(liste):
            cols = st.columns(len(liste))
            bulunanlar = [k for k in liste if kod_sayilari[k] > 0]
            if bulunanlar:
                render_cols = st.columns(len(bulunanlar))
                for idx, k in enumerate(bulunanlar):
                    render_cols[idx].write(f"**{k}:** {kod_sayilari[k]}")
                st.write("") # Alt gruba geçmeden önce boşluk

        # 1. Grup (G, D...)
        grubu_yazdir(GRUP_1)
        # 2. Grup (F, FC...)
        grubu_yazdir(GRUP_2)
        # 3. Grup (H, A...)
        grubu_yazdir(GRUP_3)
        # Yan Dal (Ban, Şok...)
        grubu_yazdir(YAN_DAL)

        st.divider()

        # --- İSTİSNALAR (Tek Bir Kutu İçinde) ---
        istisnalar = [k for k in kod_sayilari if k not in HEPSI_TANIMLI]
        if istisnalar:
            istisna_metni = ""
            for k in istisnalar:
                istisna_metni += f"**{k}:** {kod_sayilari[k]} &nbsp;&nbsp;&nbsp; " # Yan yana boşluklu
            
            st.info(istisna_metni)
                    
    else:
        st.error("Giriş yapılmadı.")
    
