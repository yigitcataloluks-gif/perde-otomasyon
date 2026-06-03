import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import StringIO

# --- SADE VE GÖZ YORMAYAN KOYU TEMA ---
st.set_page_config(page_title="Perde Otomasyon Sistemi", page_icon="🧵", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #1a1a1e; color: #f4f4f5; }
    h1, h2, h3, h4 { color: #e4e4e7 !important; }
    .stButton>button {
        background-color: #2563eb !important; color: white !important;
        border-radius: 6px !important; font-weight: bold !important;
    }
    div[data-testid="stMetricValue"] { color: #10b981 !important; }
    .stTabs [data-baseweb="tab"] { color: #a1a1aa !important; }
    .stTabs [aria-selected="true"] { color: #3b82f6 !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

# --- GOOGLE EXCEL BAĞLANTILARI ---
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"
DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]

# Google Formların Canlı Linkleri (Uygulamanın içine gömmek için)
FORM_URUN_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/viewform?embedded=true"

# Okunacak Sayfaların CSV Linkleri
# Kanka formlardan gelen ham verileri "Form Yanıtları 1" ve satış formunun sayfasından çekeceğiz.
STOK_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=stok"
SATIS_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=satis"
CARI_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=cariler"
VERESIYE_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=veresiye"

# Formların kendi orijinal sayfalarından veriyi garantiye almak için yedek okuma linkleri:
FORM_YANIT_1_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=Form Yanıtları 1"
# Kanka eğer satış formunun Excel'deki sayfa adı farklıysa buradaki "Form Yanıtları 2" kısmını o sayfa adı yapabilirsin:
FORM_SATIS_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=Form Yanıtları 2"

def veri_yukle(url):
    try:
        response = requests.get(url)
        df = pd.read_csv(StringIO(response.text))
        return df
    except:
        return pd.DataFrame()

# --- ŞİFRE KORUMASI ---
if "login" not in st.session_state: st.session_state["login"] = False
if not st.session_state["login"]:
    st.subheader("🔑 Dükkan Girişi")
    sifre = st.text_input("Giriş Şifresi:", type="password")
    if st.button("Giriş Yap", use_container_width=True):
        if sifre == "perde123":
            st.session_state["login"] = True
            st.rerun()
        else: st.error("Hatalı şifre!")
    st.stop()

# --- VERİLERİ ÇEK ---
stok_df = veri_yukle(STOK_CSV_URL)
# 1. SEKME: SATIŞ FORMU (GÖMÜLÜ)
with sekme1:
    st.header("🛒 Satış & Sipariş Kayıt Ekranı")
    st.write("Abicim, satışı ve siparişi kaydetmek için aşağıdaki formu doldurup 'Gönder' demen yeterlidir. Veriler anında hafızaya işlenir.")
    
    # ⚠️ KANKA BURADAKİ TIRNAKLARIN İÇİNE FORM LİNKİNİ YAPIŞTIR:
    SATIS_FORM_URL = "BURAYA_SATIS_FORMUNUN_LINKINI_YAZ"
    
    if SATIS_FORM_URL == "BURAYA_SATIS_FORMUNUN_LINKINI_YAZ":
        st.warning("Kanka satış formunun linkini yapıştırmayı unutma!")
    else:
        st.components.v1.iframe(SATIS_FORM_URL, height=550, scrolling=True)
