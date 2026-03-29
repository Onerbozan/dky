import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Sayfa Yapılandırması
st.set_page_config(page_title="ADKY Prospektif Takip", layout="centered")
st.title("🩺 ADKY Prospektif Veri Kayıt Sistemi")

# Google Sheets Bağlantısı
conn = st.connection("gsheets", type=GSheetsConnection)

# --- VERİ GİRİŞ FORMU ---
with st.form(key="hf_form"):
    st.header("1. Hasta Kimlik ve Vital Bulgular")
    # Protokol No yerine TC Kimlik No eklendi
    patient_tc = st.text_input("Hasta TC Kimlik No*", max_chars=11, help="11 haneli TC numarasını giriniz.")
    age = st.number_input("Yaş", min_value=18, max_value=110, value=65)
    sbp = st.number_input("Sistolik Kan Basıncı (mmHg)", min_value=40, max_value=250)
    hr = st.number_input("Kalp Hızı (atım/dk)", min_value=30, max_value=220)
    sao2 = st.number_input("Oksijen Satürasyonu (%)", min_value=40, max_value=100)
    
    st.header("2. Özgeçmiş ve Klinik Durum")
    col1, col2 = st.columns(2)
    with col1:
        ambulance = st.selectbox("Ambulansla Geliş?", ["Hayır", "Evet"])
        cancer = st.selectbox("Aktif Kanser?", ["Hayır", "Evet"])
        # Metolazone yerine "Herhangi bir diüretik" kullanımı (mEHMRG) [cite: 389, 403]
        diuretic = st.selectbox("Kronik Diüretik Kullanımı?", ["Hayır", "Evet"])
    with col2:
        copd = st.selectbox("KOAH Öyküsü?", ["Hayır", "Evet"])
        troponin = st.selectbox("Troponin Durumu", ["Negatif", "Pozitif"])
    
    st.header("3. Laboratuvar Parametreleri")
    bun = st.number_input("BUN (mg/dL)", min_value=1.0)
    creatinine = st.number_input("Kreatinin (mg/dL)", min_value=0.1)
    sodium = st.number_input("Sodyum (mmol/L)", min_value=110.0)
    potassium = st.number_input("Potasyum (mmol/L)", min_value=1.0)

    st.header("4. Takip Verileri")
    disposition = st.selectbox("Acil Servis Sonlanımı", ["Seçiniz", "Taburcu", "Servis", "Yoğun Bakım"])
    mortality_7d = st.selectbox("7 Günlük Mortalite", ["Bilinmiyor", "Sağ", "Eks"])

    submit_button = st.form_submit_button(label="Verileri Google Sheets'e Kaydet")

# --- HESAPLAMA VE VERİ TABANI İŞLEMLERİ ---
if submit_button:
    if len(patient_tc) != 11:
        st.error("Hata: Geçerli bir 11 haneli TC Kimlik Numarası girilmelidir!")
    else:
        # mEHMRG Formülü [cite: 103, 378, 403]
        # Formül: (2 x yaş) + (Ambulans: 60) - SBP + HR - (2 x SaO2) + (20 x Kreatinin) + ...
        mehmrg = (2 * age) + (60 if ambulance == "Evet" else 0) - sbp + hr - (2 * sao2) + (20 * creatinine) + (45 if cancer == "Evet" else 0) + (60 if troponin == "Pozitif" else 0) + (60 if diuretic == "Evet" else 0) + 12
        if potassium >= 4.6: mehmrg += 30
        elif potassium <= 3.9: mehmrg += 5
        
        # ADHERE (CART) Algoritması [cite: 282, 360]
        adhere = "Yüksek Risk" if (bun >= 43 and sbp < 115) else "Düşük/Orta"

        # Veri Satırı Hazırlama
        new_row = pd.DataFrame([{
            "Kayit_Tarihi": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Hasta_TC": patient_tc,
            "Yas": age,
            "SBP": sbp,
            "Nabiz": hr,
            "SaO2": sao2,
            "Ambulans": ambulance,
            "Kanser": cancer,
            "Diuretik": diuretic,
            "KOAH": copd,
            "Troponin": troponin,
            "BUN": bun,
            "Kreatinin": creatinine,
            "Sodyum": sodium,
            "Potasyum": potassium,
            "mEHMRG_Skoru": round(mehmrg, 2),
            "ADHERE_Grubu": adhere,
            "AS_Sonlanim": disposition,
            "Mortalite_7G": mortality_7d
        }])

        # Google Sheets Güncelleme
        try:
            existing_data = conn.read(worksheet="Sheet1", ttl=0)
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.success(f"Başarılı! Hasta (TC: {patient_tc}) kaydedildi. mEHMRG: {mehmrg:.1f}")
        except Exception as e:
            st.error(f"Bağlantı Hatası: {e}")
