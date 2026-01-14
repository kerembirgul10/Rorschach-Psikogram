import streamlit as st
from collections import Counter

st.set_page_config(page_title="Rorschach Psikogram", layout="wide")

# Başlık
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

for i in range(1, 11):
    kod_girisi = st.text_area(f"Kart {i}", key=f"kart_{i}", height=80)
    kart_verileri.append(kod_girisi)

if st.button("🚀 Analiz"):
    toplam_r_sayisi = 0
    kart_8910_r_sayisi = 0
    tum_kodlar = []
    
    for i, ham_veri in enumerate(kart_verileri, 1):
        if ham_veri.strip():
            satirlar = ham_veri.strip().split('\n')
            for satir in satirlar:
                temiz_satir = satir.strip()
                if temiz_satir == "" or temiz_satir.lower() == "reddetme":
                    continue
                
                toplam_r_sayisi += 1
                
                if i in [8, 9, 10]:
                    kart_8910_r_sayisi += 1
                
                kelimeler = temiz_satir.replace(",", " ").split()
                for k in kelimeler:
                    if k != "":
                        tum_kodlar.append(k)

    if toplam_r_sayisi > 0:
        # 1. BÖLÜM: R SAYISI
        st.subheader(f"R:{toplam_r_sayisi}")
        st.divider()

        # 2. BÖLÜM: KOD DAĞILIMI
        kod_sayilari = Counter(tum_kodlar)
        
        def grubu_yazdir(liste):
            bulunanlar = [k for k in liste if kod_sayilari[k] > 0]
            if bulunanlar:
                render_cols = st.columns(len(bulunanlar))
                for idx, k in enumerate(bulunanlar):
                    render_cols[idx].write(f"**{k}:** {kod_sayilari[k]}")
                st.write("") 

        grubu_yazdir(GRUP_1)
        grubu_yazdir(GRUP_2)
        grubu_yazdir(GRUP_3)
        grubu_yazdir(YAN_DAL)

        istisnalar = [k for k in kod_sayilari if k not in HEPSI_TANIMLI]
        if istisnalar:
            istisna_metni = ""
            for k in istisnalar:
                istisna_metni += f"**{k}:** {kod_sayilari[k]} &nbsp;&nbsp;&nbsp; "
            st.info(istisna_metni)

        st.divider()

        # 3. BÖLÜM: PSİKOGRAM HESAPLAMALARI
        st.subheader("🔍 Psikogram Hesaplamaları")
        
        # Değerleri hazırla
        g_say = kod_sayilari["G"]
        d_say = kod_sayilari["D"]
        a_toplam = kod_sayilari["A"] + kod_sayilari["Ad"]
        h_toplam = kod_sayilari["H"] + kod_sayilari["Hd"]
        f_toplam = kod_sayilari["F"] + kod_sayilari["F+"] + kod_sayilari["F-"] + kod_sayilari["F+-"]
        
        # T.R.I. Puanlama Mantığı
        puan_05 = (kod_sayilari["FC"] + kod_sayilari["FC'"] + kod_sayilari["Fclob"]) * 0.5
        puan_10 = (kod_sayilari["CF"] + kod_sayilari["C'F"] + kod_sayilari["ClobF"]) * 1.0
        puan_15 = (kod_sayilari["C"] + kod_sayilari["C'"] + kod_sayilari["Clob"]) * 1.5
        toplam_tri_puani = puan_05 + puan_10 + puan_15
        
        k_sayisi = kod_sayilari["K"]
        
        # Yüzde Hesaplamaları
        g_yuzde = (g_say / toplam_r_sayisi) * 100
        d_yuzde = (d_say / toplam_r_sayisi) * 100
        rc_yuzde = (kart_8910_r_sayisi / toplam_r_sayisi) * 100
        a_yuzde = (a_toplam / toplam_r_sayisi) * 100
        h_yuzde = (h_toplam / toplam_r_sayisi) * 100
        f_yuzde = (f_toplam / toplam_r_sayisi) * 100
        
        # T.R.I. Hesaplama (Bölme hatasını önlemek için kontrol ekledik)
        tri_sonuc = (k_sayisi / toplam_tri_puani) * 100 if toplam_tri_puani > 0 else 0

        # Metrikleri Göster
        calc_cols = st.columns(7)
        calc_cols[0].metric("%G", f"%{g_yuzde:.0f}")
        calc_cols[1].metric("%D", f"%{d_yuzde:.0f}")
        calc_cols[2].metric("R.C.", f"%{rc_yuzde:.0f}")
        calc_cols[3].metric("%A", f"%{a_yuzde:.0f}")
        calc_cols[4].metric("%H", f"%{h_yuzde:.0f}")
        calc_cols[5].metric("%F", f"%{f_yuzde:.0f}")
        calc_cols[6].metric("T.R.I.", f"%{tri_sonuc:.0f}")
                    
    else:
        st.error("Giriş yapılmadı.")
