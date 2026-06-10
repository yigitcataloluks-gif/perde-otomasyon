import streamlit as st
import pandas as pd
import requests
from io import StringIO

# Arayüz Ayarları (Bozulmayacak)
st.set_page_config(page_title="Dükkan Yönetim", layout="wide")

# LİNKLER
# Stoklar
STOK_CSV = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/gviz/tq?tqx=out:csv&sheet=Form+Yanıtları+1"
# Satışların olduğu yer (Bunu oku ve asla değiştirme)
CARILER_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTzXUNpze1FKf3kpYTHGBZ-cqCrR8uOUqrHtbFahqr3D0qZ1_ZT_LXVb4auwSjUO1V2pp-3-ZF_6y47/pub?gid=1188156871&single=true&output=csv"

# Form Linki (Veriyi yazdıran)
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/formResponse"

def veri_getir(url):
    try: return pd.read_csv(StringIO(requests.get(url, timeout=5).text))
    except: return pd.DataFrame()

# GİRİŞ KONTROLÜ
if "login" not in st.session_state: st.session_state["login"] = False
if not st.session_state["login"]:
    if st.text_input("Giriş:", type="password") == "perde123":
        st.session_state["login"] = True; st.rerun()
    st.stop()

# SEKMELER
t1, t2, t3, t4 = st.tabs(["🛒 Satış", "📦 Stok Ekle", "👥 Cariler", "🔍 Arama"])

with t1:
    st.header("🛒 Yeni Satış Yap")
    musteri = st.text_input("Müşteri Adı:")
    stok_df = veri_getir(STOK_CSV)
    
    if not stok_df.empty:
        urun = st.selectbox("Ürün:", stok_df.iloc[:,1].unique())
        adet = st.number_input("Miktar:", value=1.0)
        
        if st.button("💾 Satışı Kaydet"):
            # Google Form'a gönderiyoruz, form bunu Excel'e "çakılı" yazar
            payload = {"entry.823126487": musteri, "entry.1481546114": f"{urun} - {adet} adet"}
            requests.post(FORM_URL, data=payload)
            st.success("✅ Kayıt Google Sheets'e gönderildi!")
            st.rerun()

with t2:
    st.header("📦 Stoğa Ürün Ekle")
    st.components.v1.iframe("https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/viewform?embedded=true", height=600)

with t3:
    st.header("👥 Müşteri Cariler")
    st.dataframe(veri_getir(CARILER_CSV), use_container_width=True)

with t4:
    st.header("🔍 Ara")
    ara = st.text_input("Müşteri ismi:")
    df = veri_getir(CARILER_CSV)
    if ara and not df.empty:
        st.dataframe(df[df.astype(str).apply(lambda x: x.str.contains(ara, case=False)).any(axis=1)])
