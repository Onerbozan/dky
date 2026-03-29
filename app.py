import streamlit as st
import pandas as pd

# Sayfa Yapılandırması
st.set_page_config(page_title="DKY Risk Skorlama", layout="centered")
st.title("🩺 DKY Prospektif Risk Analiz Formu")

# Bölüm 1: Hasta Tanıtım ve Vital Bulgular
st.header("1. Hasta Tanıtım ve Vital Bulgular")
patient_id = st.text_input("Hasta TC / ID", help="Benzersiz bir numara giriniz.")
age = st.number_input("Yaş", min_value=18, max_value=120, value=65)
sbp = st.number_input("Sistolik Kan Basıncı (mmHg)", min_value=40, max_value=300, value=120)
hr = st.number_input("Kalp Hızı (atım/dk)", min_value=30, max_value=250, value=80)
sao2 = st.number_input("Oksijen Satürasyonu (%)", min_value=40, max_value=100, value=95)

# Bölüm 2: Özgeçmiş ve Geliş
st.header("2. Özgeçmiş ve Geliş Şekli")
col1, col2 = st.columns(2)
with col1:
    ambulance = st.selectbox("Ambulans ile mi geldi?", ["Hayır", "Evet"])
    cancer = st.selectbox("Aktif Kanser Öyküsü?", ["Hayır", "Evet"])
with col2:
    diuretic = st.selectbox("Kronik Diüretik Kullanımı?", ["Hayır", "Evet"]) # mEHMRG modifikasyonu
    copd = st.selectbox("KOAH Öyküsü?", ["Hayır", "Evet"])

# Bölüm 3: Laboratuvar Bulguları
st.header("3. Laboratuvar Bulguları")
bun = st.number_input("BUN (mg/dL)", min_value=1.0, value=20.0)
creatinine = st.number_input("Serum Kreatinin (mg/dL)", min_value=0.1, value=1.0)
sodium = st.number_input("Serum Sodyum (mmol/L)", min_value=100.0, value=138.0)
potassium = st.number_input("Serum Potasyum (mmol/L)", min_value=1.0, value=4.0)
troponin = st.selectbox("Troponin Durumu", ["Negatif", "Pozitif (>ULN)"])

# --- OTOMATİK SKOR HESAPLAMALARI ---
st.divider()
st.header("📊 Anlık Risk Analiz Sonuçları")

# 1. ADHERE (CART) Hesaplama [cite: 282, 360]
adhere_risk = "Düşük/Orta"
if bun >= 43 and sbp < 115:
    adhere_risk = "YÜKSEK RİSK"
elif bun >= 43 and sbp >= 115 and creatinine >= 2.75:
    adhere_risk = "ORTA-YÜKSEK RİSK"

# 2. mEHMRG Puan Hesaplama [cite: 103, 389, 403]
mehmrg_score = (2 * age) + (60 if ambulance == "Evet" else 0) - sbp + hr - (2 * sao2) + (20 * creatinine) + (45 if cancer == "Evet" else 0) + (60 if troponin == "Pozitif (>ULN)" else 0) + (60 if diuretic == "Evet" else 0) + 12
if potassium >= 4.6: mehmrg_score += 30
elif potassium <= 3.9: mehmrg_score += 5

st.info(f"**ADHERE Risk Grubu:** {adhere_risk}")
st.success(f"**mEHMRG Puanı:** {mehmrg_score:.1f}")

# Bölüm 4: Takip (Mortalite / Yatış)
st.header("4. Takip ve Sonlanım (Sonradan Doldurulabilir)")
disposition = st.selectbox("AS Sonlanımı", ["Seçiniz...", "Taburcu", "Servis Yatış", "Yoğun Bakım"])
mortality_7d = st.selectbox("7 Günlük Mortalite", ["Bilinmiyor", "Sağ", "Eks"])

if st.button("Verileri Kaydet"):
    # Burada Google Sheets API veya CSV kayıt kodu çalışacak
    st.write("Veri kaydedildi! (Bu kısım backend bağlantısı gerektirir)")