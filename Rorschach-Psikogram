import streamlit as st

# Sayfa Başlığı ve Tasarımı
st.set_page_config(page_title="Kod Analiz Sistemi", layout="centered")
st.title("📊 Kart ve Kod Analiz Paneli")

# 1. KISIM: Veri Girişi
st.subheader("Giriş Bilgileri")
kart_no = st.text_input("Kart Numarası")
kodlar = st.text_area("Kodları buraya yapıştırın (Aralarına boşluk bırakarak)")
l14_degeri = st.number_input("L14 Değeri (Toplam Puan Bölünecek Sayı)", min_value=0.0, value=7.0)

# 2. KISIM: Hesaplama Mantığı
if st.button("Analiz Et ve Hesapla"):
    if kodlar:
        # Kodları listeye çevir ve "Reddetme" olanları ele
        kelime_listesi = [k.strip() for k in kodlar.split() if "Reddetme" not in k]
        toplam_kod_sayisi = len(kelime_listesi)
        
        # Puanlama Grupları (Senin mantığına göre)
        # Örnek: L5, L6, L7 grubu kodları burada tanımlanabilir
        grup_05 = ["FC", "FC'", "Fclob"]
        grup_10 = ["CF", "C'F", "ClobF"]
        grup_15 = ["C", "C'", "Clob"]
        
        puan_05 = sum(1 for k in kelime_listesi if k in grup_05) * 0.5
        puan_10 = sum(1 for k in kelime_listesi if k in grup_10) * 1.0
        puan_15 = sum(1 for k in kelime_listesi if k in grup_15) * 1.5
        
        toplam_puan = puan_05 + puan_10 + puan_15
        
        # Sonuç Hesaplama (L14 / Toplam Puan)
        try:
            oran = (l14_degeri / toplam_puan) * 100 if toplam_puan > 0 else 0
        except ZeroDivisionError:
            oran = 0

        # 3. KISIM: Sonuçları Göster
        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.metric("Geçerli Kod Sayısı", toplam_kod_sayisi)
        col2.metric("Hesaplanan Puan", toplam_puan)
        col3.metric("Sonuç Oranı", f"%{oran:.0f}")
        
        if oran > 100:
            st.warning("⚠️ Oran %100'ün üzerinde çıktı!")
    else:
        st.error("Lütfen kodları giriniz!")
