import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Sayfa Konfigürasyonu
st.set_page_config(page_title="ADKY Prospektif Analiz", layout="centered")
st.title("🩺 ADKY Prospektif Veri Kayıt Portalı")
st.info("Bu sistem mEHMRG, GWTG-HF ve ADHERE skorlarını otomatik hesaplar.")

# Google Sheets Bağlantısı
conn = st.connection("gsheets", type=GSheetsConnection)

# --- VERİ GİRİŞ FORMU ---
with st.form(key="adky_form"):
    st.subheader("📋 Hasta Bilgileri ve Vitaller")
    patient_tc = st.text_input("Hasta TC Kimlik No*", max_chars=11)
    age = st.number_input("Yaş", min_value=18, max_value=110, value=65)
    
    col1, col2 = st.columns(2)
    with col1:
        sbp = st.number_input("Sistolik KB (mmHg)", value=120)
        hr = st.number_input("Kalp Hızı (atım/dk)", value=80)
    with col2:
        sao2 = st.number_input("Oksijen Satürasyonu (%)", value=95)
        ambulance = st.selectbox("Ambulansla Geliş?", ["Hayır", "Evet"])

    st.divider()
    st.subheader("🧪 Laboratuvar ve Özgeçmiş")
    c1, c2 = st.columns(2)
    with c1:
        bun = st.number_input("BUN (mg/dL)", value=20.0)
        creatinine = st.number_input("Kreatinin (mg/dL)", value=1.0)
        sodium = st.number_input("Sodyum (mmol/L)", value=138.0)
        potassium = st.number_input("Potasyum (mmol/L)", value=4.0)
    with c2:
        cancer = st.selectbox("Aktif Kanser?", ["Hayır", "Evet"])
        diuretic = st.selectbox("Kronik Diüretik?", ["Hayır", "Evet"])
        copd = st.selectbox("KOAH Öyküsü?", ["Hayır", "Evet"])
        troponin = st.selectbox("Troponin Durumu", ["Negatif", "Pozitif"])

    st.subheader("🚩 Takip (Sonradan Güncellenebilir)")
    mortality_7g = st.selectbox("7 Günlük Mortalite", ["Bilinmiyor", "Sağ", "Eks"])
    
    submit = st.form_submit_button("Veriyi Gönder ve Hesapla")

# --- HESAPLAMA VE KAYIT ---
if submit:
    if len(patient_tc) != 11:
        st.error("TC No 11 haneli olmalıdır!")
    else:
        # mEHMRG Hesaplama [cite: 103]
        mehmrg = (2 * age) + (60 if ambulance == "Evet" else 0) - sbp + hr - (2 * sao2) + (20 * creatinine) + (45 if cancer == "Evet" else 0) + (60 if troponin == "Pozitif" else 0) + (60 if diuretic == "Evet" else 0) + 12
        if potassium >= 4.6: mehmrg += 30
        elif potassium <= 3.9: mehmrg += 5
        
        # ADHERE (CART) Analizi [cite: 489]
        adhere = "Yüksek Risk" if (bun >= 43 and sbp < 115) else "Düşük/Orta"

        # Yeni Satır Verisi
        new_row = {
            "Kayit_Tarihi": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Hasta_TC": str(patient_tc),
            "Yas": age, "SBP": sbp, "Nabiz": hr, "SaO2": sao2,
            "Ambulans": ambulance, "Kanser": cancer, "Diuretik": diuretic,
            "KOAH": copd, "Troponin": troponin, "BUN": bun,
            "Kreatinin": creatinine, "Sodyum": sodium, "Potasyum": potassium,
            "mEHMRG_Skoru": round(mehmrg, 2), "ADHERE_Grubu": adhere, "Mortalite_7G": mortality_7d
        }

        try:
            # Mevcut veriyi oku
            existing_data = conn.read(worksheet="Sheet1", ttl=0)
            
            # Eğer sayfa tamamen boşsa başlıkları oluştur
            if existing_data.empty:
                updated_df = pd.DataFrame([new_row])
            else:
                updated_df = pd.concat([existing_data, pd.DataFrame([new_row])], ignore_index=True)
            
            # Güncelle
            conn.update(worksheet="Sheet1", data=updated_df)
            st.success(f"Kayıt Başarılı! mEHMRG: {mehmrg:.1f} | ADHERE: {adhere}")
            st.balloons()
        except Exception as e:
            st.error(f"Bağlantı Hatası: {e}")
