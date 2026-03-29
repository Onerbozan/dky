import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bozan DKY Araştırma Portalı", layout="wide")

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
        df['Hasta_TC'] = df['Hasta_TC'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        return df
    except Exception as e:
        st.error(f"⚠️ Bağlantı hatası: {e}")
        st.stop()
        return pd.DataFrame()

df = load_data()

# --- SEKMELER ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "➕ Yeni Hasta", 
    "🧪 Lab Girişi", 
    "🏥 Takip & Sonlanım", 
    "📋 İzlem (Düzenle)", 
    "📈 Raporlar & Yedek"
])

# ==========================================
# SEKME 1: YENİ HASTA KAYDI (Kırmızı Uyarı ve Çerçeve)
# ==========================================
with tab1:
    st.subheader("Yeni Hasta Girişi (Vitaller ve Anamnez)")
    
    # Uyarının aşağıda değil, formun hemen üstünde çıkması için özel alan
    uyari_alani = st.empty()
    
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
            temiz_tc = str(tc).strip()
            temiz_isim = isim.strip()
            sistemdeki_tcler = [str(x).split('.')[0].strip() for x in df['Hasta_TC'].tolist()]

            if len(temiz_tc) != 11 or not temiz_isim:
                uyari_alani.error("Lütfen 11 haneli TC ve Ad Soyad giriniz.")
            elif temiz_tc in sistemdeki_tcler:
                # 1. Mesajı yukarıdaki alana yazdır
                uyari_alani.error(f"❌ HATA: '{temiz_tc}' numaralı TC önceki kayıtlarda var! Lütfen TC'yi değiştirin.")
                
                # 2. TC Kutusunun çevresini kırmızı yapacak CSS kodunu sayfaya enjekte et
                st.markdown("""
                    <style>
                    div[data-testid="stTextInput"] input[aria-label="Hasta TC*"] {
                        border: 2px solid red !important;
                        background-color: #fff0f0 !important;
                        border-radius: 5px !important;
                    }
                    </style>
                """, unsafe_allow_html=True)
            else:
                new_row = pd.DataFrame([{
                    "Kayit_Tarihi": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Hasta_TC": temiz_tc, "Ad_Soyad": temiz_isim.upper(), "Yas": yas, "SBP": sbp, "Nabiz": hr, "SaO2": sao2,
                    "Ambulans": amb, "Kanser": kan, "Diuretik": diu, "KOAH": koah,
                    "BUN": 0.0, "Kreatinin": 0.0, "Sodyum": 0.0, "Potasyum": 0.0, "Troponin": "Bilinmiyor",
                    "mEHMRG_Skoru": 0.0, "ADHERE_Grubu": "Bekleniyor", "GWTG_Skoru": 0.0,
                    "AS_Sonlanim": "Bilinmiyor", "Servis_Gunu": 0, "YBU_Gunu": 0, "Mortalite_7G": "Bilinmiyor", "Mortalite_30G": "Bilinmiyor"
                }])
                updated = pd.concat([df, new_row], ignore_index=True)
                
                conn.update(data=updated)
                st.cache_data.clear()
                
                uyari_alani.success("✅ Hasta başarıyla kaydedildi! Form temizlendi.")
                time.sleep(1.5)
                st.rerun()

# ==========================================
# SEKME 2: LAB VERİ GİRİŞİ
# ==========================================
with tab2:
    st.subheader("Laboratuvar Sonuçlarını İşle")
    if not df.empty:
        search_list = (df['Hasta_TC'] + " - " + df['Ad_Soyad']).tolist()
        choice = st.selectbox("Hasta Seçin (TC veya İsim):", ["Seçiniz..."] + search_list)
        
        if choice != "Seçiniz...":
            t_id = choice.split(" - ")[0]
            row = df[df['Hasta_TC'] == t_id].iloc[0]
            idx = df.index[df['Hasta_TC'] == t_id][0]
            
            with st.form("lab_form"):
                l1, l2, l3, l4, l5 = st.columns(5)
                f_bun = l1.number_input("BUN", value=float(row['BUN']))
                f_cre = l2.number_input("Kreatinin", value=float(row['Kreatinin']))
                f_sod = l3.number_input("Sodyum", value=float(row['Sodyum']))
                f_pot = l4.number_input("Potasyum", value=float(row['Potasyum']))
                f_tro = l5.selectbox("Troponin", ["Negatif", "Pozitif"], index=0 if row['Troponin'] != "Pozitif" else 1)
                
                if st.form_submit_button("Lab Verilerini Güncelle"):
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
                    st.success("✅ Veriler ve skorlar güncellendi!")
                    st.rerun()

# ==========================================
# SEKME 3: TAKİP & SONLANIM
# ==========================================
with tab3:
    st.subheader("Yatış Bilgileri ve Mortalite Takibi")
    if not df.empty:
        search_list_2 = (df['Hasta_TC'] + " - " + df['Ad_Soyad']).tolist()
        choice_2 = st.selectbox("Takip Girişi İçin Seçin:", ["Seçiniz..."] + search_list_2, key="search2")
        
        if choice_2 != "Seçiniz...":
            t_id2 = choice_2.split(" - ")[0]
            row2 = df[df['Hasta_TC'] == t_id2].iloc[0]
            idx2 = df.index[df['Hasta_TC'] == t_id2][0]
            
            with st.form("follow_form"):
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
                    st.success("✅ Takip verileri güncellendi.")
                    st.rerun()

# ==========================================
# SEKME 4: İZLEM PANELI (Düzenlenebilir Tablo)
# ==========================================
with tab4:
    st.subheader("Vaka Kontrol ve Hızlı Düzenleme Paneli")
    st.info("💡 Tablodaki hücrelere çift tıklayarak tüm verileri değiştirebilirsiniz. Sağa doğru kaydırarak tüm sütunları görebilirsiniz.")
    
    if not df.empty:
        df_view = df.copy()
        
        def get_status(r):
            if r['BUN'] == 0.0 or r['Mortalite_30G'] == "Bilinmiyor": return "🔴 Eksik"
            return "🟢 Tamam"
        
        df_view.insert(0, 'Durum', df_view.apply(get_status, axis=1))
        
        all_cols = ['Durum', 'Kayit_Tarihi', 'Hasta_TC', 'Ad_Soyad', 'Yas', 'SBP', 'Nabiz', 'SaO2', 
                    'Ambulans', 'Kanser', 'Diuretik', 'KOAH', 'BUN', 'Kreatinin', 'Sodyum', 'Potasyum', 
                    'Troponin', 'mEHMRG_Skoru', 'ADHERE_Grubu', 'GWTG_Skoru', 'AS_Sonlanim', 
                    'Servis_Gunu', 'YBU_Gunu', 'Mortalite_7G', 'Mortalite_30G']
        
        edited_df = st.data_editor(
            df_view[all_cols],
            use_container_width=True,
            hide_index=True,
            disabled=["Durum", "Kayit_Tarihi", "Hasta_TC", "mEHMRG_Skoru", "ADHERE_Grubu", "GWTG_Skoru"]
        )
        
        if st.button("💾 Tablodaki Değişiklikleri Kaydet ve Skorları Güncelle"):
            for idx, row in edited_df.iterrows():
                df.at[idx, 'Ad_Soyad'] = str(row['Ad_Soyad'])
                df.at[idx, 'Yas'] = int(row['Yas'])
                df.at[idx, 'SBP'] = float(row['SBP'])
                df.at[idx, 'Nabiz'] = float(row['Nabiz'])
                df.at[idx, 'SaO2'] = float(row['SaO2'])
                df.at[idx, 'Ambulans'] = str(row['Ambulans'])
                df.at[idx, 'Kanser'] = str(row['Kanser'])
                df.at[idx, 'Diuretik'] = str(row['Diuretik'])
                df.at[idx, 'KOAH'] = str(row['KOAH'])
                df.at[idx, 'BUN'] = float(row['BUN'])
                df.at[idx, 'Kreatinin'] = float(row['Kreatinin'])
                df.at[idx, 'Sodyum'] = float(row['Sodyum'])
                df.at[idx, 'Potasyum'] = float(row['Potasyum'])
                df.at[idx, 'Troponin'] = str(row['Troponin'])
                df.at[idx, 'AS_Sonlanim'] = str(row['AS_Sonlanim'])
                df.at[idx, 'Servis_Gunu'] = int(row['Servis_Gunu'])
                df.at[idx, 'YBU_Gunu'] = int(row['YBU_Gunu'])
                df.at[idx, 'Mortalite_7G'] = str(row['Mortalite_7G'])
                df.at[idx, 'Mortalite_30G'] = str(row['Mortalite_30G'])
                
                r = df.iloc[idx]
                try:
                    mehmrg = (2 * r['Yas']) + (60 if r['Ambulans'] == "Evet" else 0) - r['SBP'] + r['Nabiz'] - (2 * r['SaO2']) + (20 * r['Kreatinin']) + (45 if r['Kanser'] == "Evet" else 0) + (60 if r['Troponin'] == "Pozitif" else 0) + (60 if r['Diuretik'] == "Evet" else 0) + 12
                    if r['Potasyum'] >= 4.6: mehmrg += 30
                    elif r['Potasyum'] <= 3.9: mehmrg += 5
                    
                    adhere = "Yüksek Risk" if (r['BUN'] >= 43 and r['SBP'] < 115) else "Düşük/Orta"
                    
                    gwtg = (r['Yas'] // 10) * 3 + (2 if r['KOAH'] == "Evet" else 0)
                    if r['BUN'] >= 40: gwtg += 8
                    if r['SBP'] < 100: gwtg += 15
                    if r['Sodyum'] < 135: gwtg += 4
                    
                    df.at[idx, 'mEHMRG_Skoru'] = round(mehmrg, 2)
                    df.at[idx, 'ADHERE_Grubu'] = adhere
                    df.at[idx, 'GWTG_Skoru'] = gwtg
                except:
                    pass
            
            conn.update(data=df)
            st.cache_data.clear()
            st.success("✅ Tüm veriler kaydedildi!")
            st.rerun()

# ==========================================
# SEKME 5: RAPORLAR VE YEDEKLEME
# ==========================================
with tab5:
    st.subheader("📊 Araştırma İstatistikleri ve Yedekleme")
    if not df.empty:
        df['Tarih_Obj'] = pd.to_datetime(df['Kayit_Tarihi'], format="%d/%m/%Y %H:%M", errors='coerce')
        
        bugun = datetime.now()
        bir_hafta_once = bugun - timedelta(days=7)
        
        toplam_hasta = len(df)
        haftalik_hasta = len(df[df['Tarih_Obj'] >= bir_hafta_once])
        eksik_veri = len(df[(df['BUN'] == 0.0) | (df['Mortalite_30G'] == "Bilinmiyor")])
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Toplam Kaydedilen Hasta", f"{toplam_hasta} Kişi")
        col_m2.metric("Bu Hafta Eklenen Hasta", f"+{haftalik_hasta} Kişi")
        col_m3.metric("Eksik Verisi Olan Hasta", f"{eksik_veri} Kişi", delta="-İncelenmeli", delta_color="inverse")
        
        st.divider()
        st.markdown("### 💾 Veritabanını Bilgisayara İndir (Yedek Al)")
        st.info("Aylık veya haftalık olarak tüm verilerinizi bir Excel/CSV dosyası şeklinde bilgisayarınıza indirmek için aşağıdaki butonu kullanabilirsiniz.")
        
        df_indir = df.drop(columns=['Tarih_Obj'], errors='ignore')
        csv_data = df_indir.to_csv(index=False).encode('utf-8-sig')
        
        dosya_adi = f"DKY_Yedek_{bugun.strftime('%d_%m_%Y')}.csv"
        
        st.download_button(
            label="📥 Tüm Verileri İndir (Excel/CSV Formatında)",
            data=csv_data,
            file_name=dosya_adi,
            mime="text/csv"
        )
    else:
        st.info("Henüz sistemde raporlanacak hasta bulunmamaktadır.")
