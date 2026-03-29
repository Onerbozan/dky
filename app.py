import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="DKY Klinik Karar Destek", layout="wide")

# --- GİRİŞ (LOGIN) EKRANI ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 DKY Prospektif Araştırma Portalı")
    st.info("Lütfen yetkili kullanıcı adı ve şifrenizle giriş yapın.")
    
    with st.form("login_form"):
        username = st.text_input("Kullanıcı Adı")
        password = st.text_input("Şifre", type="password")
        submit_login = st.form_submit_button("Giriş Yap")
        
        if submit_login:
            if username in st.secrets["passwords"] and st.secrets["passwords"][username] == password:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Hatalı kullanıcı adı veya şifre!")
    st.stop() # Giriş yapılmadıysa kodun geri kalanını çalıştırma

# --- ANA UYGULAMA ---
st.title("🩺 DKY Prospektif Veri Yönetim Sistemi")
conn = st.connection("gsheets", type=GSheetsConnection)

# Veriyi önbelleğe almadan doğrudan çekme (Güncellik için)
@st.cache_data(ttl=0)
def load_data():
    try:
        df = conn.read(worksheet="Sheet1")
        if df.empty:
            df = pd.DataFrame(columns=[
                "Kayit_Tarihi", "Hasta_TC", "Ad_Soyad", "Yas", "SBP", "Nabiz", "SaO2",
                "Ambulans", "Kanser", "Diuretik", "KOAH", "BUN", "Kreatinin", "Sodyum", 
                "Potasyum", "Troponin", "mEHMRG_Skoru", "ADHERE_Grubu", "GWTG_Skoru",
                "AS_Sonlanim", "Servis_Gunu", "YBU_Gunu", "Mortalite_7G", "Mortalite_30G"
            ])
        # TC Numarasını her zaman string olarak tut
        df['Hasta_TC'] = df['Hasta_TC'].astype(str)
        return df
    except Exception as e:
        st.error(f"Veri çekme hatası: {e}")
        return pd.DataFrame()

df = load_data()

# Sekmeler
tab1, tab2, tab3 = st.tabs(["➕ Yeni Hasta Kaydı", "🔍 Ara ve Düzenle", "📊 Hasta Listesi ve Durum"])

# ==========================================
# SEKME 1: YENİ HASTA KAYDI
# ==========================================
with tab1:
    st.subheader("Yeni Vaka Girişi")
    with st.form(key="new_patient_form"):
        col_id1, col_id2, col_id3 = st.columns([1, 2, 1])
        with col_id1:
            patient_tc = st.text_input("Hasta TC Kimlik No*", max_chars=11)
        with col_id2:
            patient_name = st.text_input("Ad Soyad*")
        with col_id3:
            age = st.number_input("Yaş", min_value=18, max_value=110, value=65)

        st.markdown("**Vitaller ve Özgeçmiş**")
        c1, c2, c3, c4 = st.columns(4)
        sbp = c1.number_input("Sistolik KB", value=120)
        hr = c2.number_input("Kalp Hızı", value=80)
        sao2 = c3.number_input("SaO2 (%)", value=95)
        ambulance = c4.selectbox("Ambulans?", ["Hayır", "Evet"])

        c5, c6, c7, c8 = st.columns(4)
        cancer = c5.selectbox("Aktif Kanser?", ["Hayır", "Evet"])
        diuretic = c6.selectbox("Kronik Diüretik?", ["Hayır", "Evet"])
        copd = c7.selectbox("KOAH?", ["Hayır", "Evet"])
        troponin = c8.selectbox("Troponin", ["Negatif", "Pozitif"])

        st.markdown("**Laboratuvar**")
        l1, l2, l3, l4 = st.columns(4)
        bun = l1.number_input("BUN (mg/dL)", value=20.0)
        creatinine = l2.number_input("Kreatinin", value=1.0)
        sodium = l3.number_input("Sodyum", value=138.0)
        potassium = l4.number_input("Potasyum", value=4.0)

        submit_new = st.form_submit_button("Kaydet ve Skorları Hesapla")

        if submit_new:
            if len(patient_tc) != 11 or not patient_name:
                st.error("Lütfen 11 haneli TC No ve Ad Soyad giriniz!")
            elif patient_tc in df['Hasta_TC'].values:
                st.error("Bu TC Kimlik Numarası ile daha önce kayıt yapılmış! Lütfen 'Ara ve Düzenle' sekmesini kullanın.")
            else:
                # Hesaplamalar
                mehmrg = (2 * age) + (60 if ambulance == "Evet" else 0) - sbp + hr - (2 * sao2) + (20 * creatinine) + (45 if cancer == "Evet" else 0) + (60 if troponin == "Pozitif" else 0) + (60 if diuretic == "Evet" else 0) + 12
                if potassium >= 4.6: mehmrg += 30
                elif potassium <= 3.9: mehmrg += 5
                
                adhere = "Yüksek Risk" if (bun >= 43 and sbp < 115) else "Düşük/Orta"
                
                gwtg_score = (age // 10) * 3 + (2 if copd == "Evet" else 0)
                if bun >= 40: gwtg_score += 8
                if sbp < 100: gwtg_score += 15
                if sodium < 135: gwtg_score += 4

                new_row = pd.DataFrame([{
                    "Kayit_Tarihi": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Hasta_TC": patient_tc, "Ad_Soyad": patient_name.upper(), "Yas": age, 
                    "SBP": sbp, "Nabiz": hr, "SaO2": sao2, "Ambulans": ambulance, 
                    "Kanser": cancer, "Diuretik": diuretic, "KOAH": copd,
                    "BUN": bun, "Kreatinin": creatinine, "Sodyum": sodium, "Potasyum": potassium, "Troponin": troponin,
                    "mEHMRG_Skoru": round(mehmrg, 2), "ADHERE_Grubu": adhere, "GWTG_Skoru": gwtg_score,
                    "AS_Sonlanim": "Bilinmiyor", "Servis_Gunu": 0, "YBU_Gunu": 0, 
                    "Mortalite_7G": "Bilinmiyor", "Mortalite_30G": "Bilinmiyor"
                }])

                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                st.success(f"{patient_name} başarıyla eklendi! mEHMRG: {mehmrg:.1f}")
                st.cache_data.clear()
                st.rerun()

# ==========================================
# SEKME 2: ARA VE DÜZENLE (Takip Verileri İçin)
# ==========================================
with tab2:
    st.subheader("Hasta Güncelleme ve Takip Girişi")
    if not df.empty:
        # Arama kutusu için TC ve İsim birleştirme
        df['Arama_Metni'] = df['Hasta_TC'] + " - " + df['Ad_Soyad']
        hasta_listesi = df['Arama_Metni'].tolist()
        secilen_hasta = st.selectbox("Düzenlemek istediğiniz hastayı arayın (TC veya İsim):", ["Seçiniz..."] + hasta_listesi)

        if secilen_hasta != "Seçiniz...":
            # Seçilen hastanın verilerini filtrele
            hedef_tc = secilen_hasta.split(" - ")[0]
            hasta_verisi = df[df['Hasta_TC'] == hedef_tc].iloc[0]
            idx = df.index[df['Hasta_TC'] == hedef_tc].tolist()[0]

            st.info(f"Seçilen Hasta: **{hasta_verisi['Ad_Soyad']}** | Kayıt Tarihi: {hasta_verisi['Kayit_Tarihi']}")

            with st.form(key="edit_form"):
                st.markdown("**1. Hastane Yatış Bilgileri**")
                col_e1, col_e2, col_e3 = st.columns(3)
                
                # Mevcut değerlerin indexlerini bulma (Hata önleme)
                sonlanim_options = ["Bilinmiyor", "Taburcu", "Servis Yatış", "Yoğun Bakım"]
                s_idx = sonlanim_options.index(hasta_verisi['AS_Sonlanim']) if hasta_verisi['AS_Sonlanim'] in sonlanim_options else 0
                
                edit_disposition = col_e1.selectbox("AS Sonlanımı", sonlanim_options, index=s_idx)
                edit_ward = col_e2.number_input("Serviste Kalış Süresi (Gün)", min_value=0, value=int(hasta_verisi.get('Servis_Gunu', 0)))
                edit_icu = col_e3.number_input("YBÜ Kalış Süresi (Gün)", min_value=0, value=int(hasta_verisi.get('YBU_Gunu', 0)))

                st.markdown("**2. Mortalite Takibi**")
                col_m1, col_m2 = st.columns(2)
                
                mort_options = ["Bilinmiyor", "Sağ", "Eks"]
                m7_idx = mort_options.index(hasta_verisi['Mortalite_7G']) if hasta_verisi['Mortalite_7G'] in mort_options else 0
                m30_idx = mort_options.index(hasta_verisi['Mortalite_30G']) if hasta_verisi['Mortalite_30G'] in mort_options else 0
                
                edit_mort7 = col_m1.selectbox("7 Günlük Mortalite", mort_options, index=m7_idx)
                edit_mort30 = col_m2.selectbox("30 Günlük Mortalite", mort_options, index=m30_idx)

                update_btn = st.form_submit_button("Güncellemeleri Kaydet")

                if update_btn:
                    # Sadece ilgili satırı güncelle
                    df.at[idx, 'AS_Sonlanim'] = edit_disposition
                    df.at[idx, 'Servis_Gunu'] = edit_ward
                    df.at[idx, 'YBU_Gunu'] = edit_icu
                    df.at[idx, 'Mortalite_7G'] = edit_mort7
                    df.at[idx, 'Mortalite_30G'] = edit_mort30
                    
                    # 'Arama_Metni' sütununu kaydetmeden önce sil
                    df_to_save = df.drop(columns=['Arama_Metni'])
                    
                    conn.update(worksheet="Sheet1", data=df_to_save)
                    st.success("Veriler başarıyla güncellendi!")
                    st.cache_data.clear()
                    st.rerun()
    else:
        st.warning("Henüz sisteme kayıtlı hasta bulunmamaktadır.")

# ==========================================
# SEKME 3: HASTA LİSTESİ VE EKSİK VERİ KONTROLÜ
# ==========================================
with tab3:
    st.subheader("Genel Durum Panosu")
    if not df.empty:
        # Eksik veri kontrolü (Sonlanım veya Mortalite bilinmiyorsa uyarı ver)
        def durum_belirle(row):
            if row['AS_Sonlanim'] == "Bilinmiyor" or row['Mortalite_30G'] == "Bilinmiyor":
                return "🔴 Eksik Veri"
            else:
                return "🟢 Tamamlandı"
                
        df_display = df.copy()
        df_display['Durum'] = df_display.apply(durum_belirle, axis=1)
        
        # Sadece göze hitap eden önemli sütunları listele
        df_display = df_display[['Durum', 'Kayit_Tarihi', 'Hasta_TC', 'Ad_Soyad', 'mEHMRG_Skoru', 'ADHERE_Grubu', 'AS_Sonlanim', 'Mortalite_30G']]
        
        # Filtreleme metrikleri
        tamamlanan = len(df_display[df_display['Durum'] == '🟢 Tamamlandı'])
        eksik = len(df_display[df_display['Durum'] == '🔴 Eksik Veri'])
        
        st.write(f"**Toplam Kayıt:** {len(df_display)} | **Tamamlanan:** {tamamlanan} | **Eksik Takip:** {eksik}")
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Kayıtlı veri bulunmamaktadır.")
