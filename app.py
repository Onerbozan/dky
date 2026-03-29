import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="DKY Araştırma Portalı", layout="wide")

# --- GİRİŞ KONTROLÜ ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 DKY Çalışma Girişi")
    with st.form("login"):
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.form_submit_button("Giriş"):
            if "passwords" in st.secrets and u in st.secrets["passwords"] and st.secrets["passwords"][u] == p:
                st.session_state.logged_in = True
                st.rerun()
            else: 
                st.error("Hatalı giriş! Şifreyi veya kullanıcı adını kontrol edin.")
    st.stop()

# --- VERİ BAĞLANTISI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(ttl=0) 
        if df.empty:
            return pd.DataFrame(columns=[
                "Kayit_Tarihi", "Hasta_TC", "Ad_Soyad", "Yas", "SBP", "Nabiz", "SaO2",
                "Ambulans", "Kanser", "Diuretik", "KOAH", "BUN", "Kreatinin", "Sodyum", 
                "Potasyum", "Troponin", "mEHMRG_Skoru", "ADHERE_Grubu", "GWTG_Skoru",
                "AS_Sonlanim", "Servis_Gunu", "YBU_Gunu", "Mortalite_7G", "Mortalite_30G"
            ])
        df['Hasta_TC'] = df['Hasta_TC'].astype(str)
        return df
    except Exception as e:
        st.error(f"⚠️ Bağlantı hatası: {e}\nLütfen Google API anahtarlarının (Service Account) Secrets bölümünde eksiksiz olduğundan emin olun.")
        st.stop()
        return pd.DataFrame()

df = load_data()

# --- SEKMELER ---
tab1, tab2, tab3, tab4 = st.tabs(["➕ Yeni Hasta Kaydı", "🧪 Lab Veri Girişi", "🏥 Takip & Sonlanım", "📋 İzlem Paneli"])

# ==========================================
# SEKME 1: YENİ HASTA KAYDI (Vitaller & Anamnez)
# ==========================================
with tab1:
    st.subheader("Yeni Hasta Girişi (Vitaller ve Anamnez)")
    # clear_on_submit=True ile butona basıldığında form içindeki her şey sıfırlanır
    with st.form("new_reg", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        tc = c1.text_input("Hasta TC*", max_chars=11)
        isim = c2.text_input("Ad Soyad*")
        yas = c3.number_input("Yaş", 18, 110, 65)

        st.markdown("**Vitaller**")
        v1, v2, v3 = st.columns(3)
        sbp = v1.number_input("Sistolik KB (mmHg)", value=120)
        hr = v2.number_input("Kalp Hızı (dk)", value=80)
        sao2 = v3.number_input("SaO2 (%)", value=95)

        st.markdown("**Anamnez**")
        a1, a2, a3, a4 = st.columns(4)
        amb = a1.selectbox("Ambulansla mı geldi?", ["Hayır", "Evet"])
        koah = a2.selectbox("KOAH Öyküsü?", ["Hayır", "Evet"])
        kan = a3.selectbox("Aktif Kanser?", ["Hayır", "Evet"])
        diu = a4.selectbox("Kronik Diüretik?", ["Hayır", "Evet"])

        if st.form_submit_button("Hastayı Kaydet"):
            if len(tc) == 11 and isim:
                new_row = pd.DataFrame([{
                    "Kayit_Tarihi": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Hasta_TC": tc, "Ad_Soyad": isim.upper(), "Yas": yas, "SBP": sbp, "Nabiz": hr, "SaO2": sao2,
                    "Ambulans": amb, "Kanser": kan, "Diuretik": diu, "KOAH": koah,
                    "BUN": 0.0, "Kreatinin": 0.0, "Sodyum": 0.0, "Potasyum": 0.0, "Troponin": "Bilinmiyor",
                    "mEHMRG_Skoru": 0.0, "ADHERE_Grubu": "Bekleniyor", "GWTG_Skoru": 0.0,
                    "AS_Sonlanim": "Bilinmiyor", "Servis_Gunu": 0, "YBU_Gunu": 0, "Mortalite_7G": "Bilinmiyor", "Mortalite_30G": "Bilinmiyor"
                }])
                updated = pd.concat([df, new_row], ignore_index=True)
                
                conn.update(data=updated)
                st.cache_data.clear()
                
                st.success("✅ Hasta başarıyla kaydedildi! Form temizlendi, yeni hasta girebilir veya düzenleme sekmelerine geçebilirsiniz.")
                time.sleep(1.5) # Mesajın ekranda 1.5 saniye kalmasını sağlar
                st.rerun() # Sayfayı yeniler
            else: 
                st.error("Lütfen 11 haneli TC ve Ad Soyad giriniz.")

# ==========================================
# SEKME 2: LAB VERİ GİRİŞİ (Arama + Lab)
# ==========================================
with tab2:
    st.subheader("Laboratuvar Sonuçlarını İşle")
    if not df.empty:
        search_list = (df['Hasta_TC'] + " - " + df['Ad_Soyad']).tolist()
        choice = st.selectbox("Hasta Seçin (TC veya İsim yazarak arayın):", ["Seçiniz..."] + search_list)
        
        if choice != "Seçiniz...":
            t_id = choice.split(" - ")[0]
            row = df[df['Hasta_TC'] == t_id].iloc[0]
            idx = df.index[df['Hasta_TC'] == t_id][0]
            
            with st.form("lab_form", clear_on_submit=True):
                l1, l2, l3, l4, l5 = st.columns(5)
                f_bun = l1.number_input("BUN", value=float(row['BUN']))
                f_cre = l2.number_input("Kreatinin", value=float(row['Kreatinin']))
                f_sod = l3.number_input("Sodyum", value=float(row['Sodyum']))
                f_pot = l4.number_input("Potasyum", value=float(row['Potasyum']))
                f_tro = l5.selectbox("Troponin", ["Negatif", "Pozitif"], index=0 if row['Troponin'] != "Pozitif" else 1)
                
                if st.form_submit_button("Laboratuvar Verilerini Kaydet ve Skorları Hesapla"):
                    mehmrg = (2 * row['Yas']) + (60 if row['Ambulans'] == "Evet" else 0) - row['SBP'] + row['Nabiz'] - (2 * row['SaO2']) + (20 * f_cre) + (45 if row['Kanser'] == "Evet" else 0) + (60 if f_tro == "Pozitif" else 0) + (60 if row['Diuretik'] == "Evet" else 0) + 12
                    if f_pot >= 4.6: mehmrg += 30
                    elif f_pot <= 3.9: mehmrg += 5
                    
                    adhere = "Yüksek Risk" if (f_bun >= 43 and row['SBP'] < 115) else "Düşük/Orta"
                    
                    gwtg = (row['Yas'] // 10) * 3 + (2 if row['KOAH'] == "Evet" else 0)
                    if f_bun >= 40: gwtg += 8
                    if row['SBP'] < 100: gwtg += 15
                    if f_sod < 135: gwtg += 4

                    df.at[idx, 'BUN'] = f_bun
                    df.at[idx, 'Kreatinin'] = f_cre
                    df.at[idx, 'Sodyum'] = f_sod
                    df.at[idx, 'Potasyum'] = f_pot
                    df.at[idx, 'Troponin'] = f_tro
                    df.at[idx, 'mEHMRG_Skoru'] = round(mehmrg, 2)
                    df.at[idx, 'ADHERE_Grubu'] = adhere
                    df.at[idx, 'GWTG_Skoru'] = gwtg
                    
                    conn.update(data=df)
                    st.cache_data.clear()
                    st.success("✅ Laboratuvar verileri kaydedildi ve tüm skorlar güncellendi!")
                    time.sleep(1.5)
                    st.rerun()

# ==========================================
# SEKME 3: TAKİP & SONLANIM (Arama + Yatış)
# ==========================================
with tab3:
    st.subheader("Yatış Bilgileri ve Mortalite Takibi")
    if not df.empty:
        search_list_2 = (df['Hasta_TC'] + " - " + df['Ad_Soyad']).tolist()
        choice_2 = st.selectbox("Takip Girişi İçin Hasta Seçin:", ["Seçiniz..."] + search_list_2, key="search2")
        
        if choice_2 != "Seçiniz...":
            t_id2 = choice_2.split(" - ")[0]
            row2 = df[df['Hasta_TC'] == t_id2].iloc[0]
            idx2 = df.index[df['Hasta_TC'] == t_id2][0]
            
            with st.form("follow_form", clear_on_submit=True):
                f1, f2, f3 = st.columns(3)
                son_ops = ["Bilinmiyor", "Taburcu", "Servis Yatış", "Yoğun Bakım"]
                s_idx = son_ops.index(row2['AS_Sonlanim']) if row2['AS_Sonlanim'] in son_ops else 0
                son = f1.selectbox("Sonlanım", son_ops, index=s_idx)
                
                s_gun = f2.number_input("Servis Gün", 0, 100, int(row2['Servis_Gunu']))
                y_gun = f3.number_input("YBÜ Gün", 0, 100, int(row2['YBU_Gunu']))
                
                m1, m2 = st.columns(2)
                mort_ops = ["Bilinmiyor", "Sağ", "Eks"]
                m7_idx = mort_ops.index(row2['Mortalite_7G']) if row2['Mortalite_7G'] in mort_ops else 0
                m30_idx = mort_ops.index(row2['Mortalite_30G']) if row2['Mortalite_30G'] in mort_ops else 0
                
                m7 = m1.selectbox("7 Günlük Mortalite", mort_ops, index=m7_idx)
                m30 = m2.selectbox("30 Günlük Mortalite", mort_ops, index=m30_idx)
                
                if st.form_submit_button("Takip Verilerini Güncelle"):
                    df.at[idx2, 'AS_Sonlanim'] = son
                    df.at[idx2, 'Servis_Gunu'] = s_gun
                    df.at[idx2, 'YBU_Gunu'] = y_gun
                    df.at[idx2, 'Mortalite_7G'] = m7
                    df.at[idx2, 'Mortalite_30G'] = m30
                    
                    conn.update(data=df)
                    st.cache_data.clear()
                    st.success("✅ Takip verileri başarıyla güncellendi.")
                    time.sleep(1.5)
                    st.rerun()

# ==========================================
# SEKME 4: İZLEM PANELI (Liste)
# ==========================================
with tab4:
    st.subheader("Vaka Kontrol Paneli")
    if not df.empty:
        def get_status(r):
            if r['BUN'] == 0.0 or r['Mortalite_30G'] == "Bilinmiyor": return "🔴 Eksik"
            return "🟢 Tamam"
        
        df_view = df.copy()
        df_view['Durum'] = df_view.apply(get_status, axis=1)
        disp_cols = ['Durum', 'Hasta_TC', 'Ad_Soyad', 'mEHMRG_Skoru', 'ADHERE_Grubu', 'AS_Sonlanim', 'Mortalite_30G']
        st.dataframe(df_view[disp_cols], use_container_width=True, hide_index=True)
    else: 
        st.info("Henüz kayıtlı hasta yok.")
