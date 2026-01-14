import streamlit as st

st.set_page_config(page_title="Kart Analiz Sistemi", layout="wide")

st.title("📋 10 Kartlı Kod Analiz Sistemi")
st.write("Her kart için kodları ilgili kutucuğa yapıştırın. 'Reddetme' içeren kodlar otomatik elenecektir.")

# Puanlama Katsayıları (Daha sonra değiştirmek istersen buradan kolayca yapabilirsin)
GRUP_05 = ["FC", "FC'", "Fclob"]
GRUP_10 = ["CF", "C'F", "ClobF"]
GRUP_15 = ["C", "C'", "Clob"]

# Verileri depolamak için bir liste
kart_verileri = []

# 10 Adet Kart Girişi Oluşturma
cols = st.columns(2) # Sayfayı iki sütuna bölüyoruz ki çok uzun görünmesin
for i in range(1, 11):
    with cols[0] if i <= 5 else cols[1]:
        input_id = f"Kart {i}"
        kod_girisi = st.text_area(f"📍 {input_id} Kodlarını Girin:", key=f"kart_{i}", height=100)
        kart_verileri.append(kod_girisi)

st.divider()

# Global Ayarlar (L14 Değeri)
l14_degeri = st.number_input("🎯 Analiz için L14 Değerini Girin:", value=7.0)

if st.button("🚀 Tüm Kartları Analiz Et ve Hesapla"):
    toplam_genel_puan = 0
    toplam_gecerli_kod = 0
    
    # Her kartı tek tek dönerek hesapla
    for idx, ham_veri in enumerate(kart_verileri, 1):
        if ham_veri:
            # Kodları ayır ve Reddetme içerenleri ele
            kodlar = [k.strip() for k in ham_veri.split() if "Reddetme" not in k]
            
            # Bu kartın puanını hesapla
            p05 = sum(1 for k in kodlar if k in GRUP_05) * 0.5
            p10 = sum(1 for k in kodlar if k in GRUP_10) * 1.0
            p15 = sum(1 for k in kodlar if k in GRUP_15) * 1.5
            
            kart_puani = p05 + p10 + p15
            toplam_genel_puan += kart_puani
            toplam_gecerli_kod += len(kodlar)
            
            # Kart bazlı küçük bilgi (isteğe bağlı)
            # st.write(f"Kart {idx}: {kart_puani} puan")

    # Genel Sonuç Hesaplama
    if toplam_genel_puan > 0:
        genel_oran = (l14_degeri / toplam_genel_puan) * 100
        
        # Sonuç Ekranı
        st.success("✅ Tüm kartlar başarıyla analiz edildi.")
        res_col1, res_col2, res_col3 = st.columns(3)
        res_col1.metric("Toplam Geçerli Kod", toplam_gecerli_kod)
        res_col2.metric("Toplam Hesaplanan Puan", f"{toplam_genel_puan}")
        res_col3.metric("GENEL SONUÇ ORANI", f"%{genel_oran:.0f}")
    else:
        st.warning("Hesaplanacak veri bulunamadı. Lütfen kartlara kod girişi yapın.")
