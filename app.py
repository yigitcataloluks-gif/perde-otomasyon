import streamlit as st
import pandas as pd
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

# Google Formunun orijinal gömme linki
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/viewform?embedded=true"

# Okunacak Sayfaların CSV Linkleri
STOK_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=stok"
SATIS_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=satis"
VERESIYE_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=veresiye"

def veri_yukle(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
            return df
        else:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- ŞİFRE KORUMASI ---
if "login" not in st.session_state: 
    st.session_state["login"] = False

if not st.session_state["login"]:
    st.subheader("🔑 Dükkan Girişi")
    sifre = st.text_input("Giriş Şifresi:", type="password")
    if st.button("Giriş Yap", use_container_width=True):
        if sifre == "perde123":
            st.session_state["login"] = True
            st.rerun()
        else: 
            st.error("Hatalı şifre!")
    st.stop()

# --- VERİLERİ ÇEK ---
stok_df = veri_yukle(STOK_CSV_URL)
satis_df = veri_yukle(SATIS_CSV_URL)
veresiye_df = veri_yukle(VERESIYE_CSV_URL)

# --- SEKMELER BAŞLIYOR ---
sekme1, sekme2, sekme3, sekme4 = st.tabs(["🛒 Satış & Sipariş Kaydı", "📦 Stoğa Ürün Ekle", "👥 Müşteri Cariler", "📊 Müşteri Arama & Geçmiş"])

# 1. SEKME: SATIŞ FORMU GÖMME (HATALI TIRNAK BURADA TAMAMEN DÜZELTİLDİ!)
with sekme1:
    st.header("🛒 Satış & Sipariş Kayıt Ekranı")
    st.write("Abicim, satışı ve siparişi Excel'e kaydetmek için aşağıdaki formu doldurup en alttaki Gönder butonuna basman yeterlidir.")
    st.components.v1.iframe(FORM_URL, height=600, scrolling=True)

# 2. SEKME: ÜRÜN EKLEME FORMU GÖMME
with sekme2:
    st.header("📦 Stoğa Yeni Mal Ekleme")
    st.write("Yeni gelen kumaş veya tülleri Excel'e işlemek için formu doldurup Gönder deyin.")
    st.components.v1.iframe(FORM_URL, height=600, scrolling=True)
    
    st.write("---")
    st.subheader("📋 Güncel Stok Listesi")
    if not stok_df.empty:
        st.dataframe(stok_df, use_container_width=True)
    else:
        st.info("Kayıtlı stok verisi yükleniyor, yeni eklediyseniz sayfayı yenileyin kanka.")

# 3. SEKME: MÜŞTERİ CARİLERİ
with sekme3:
    st.header("👥 Kayıtlı Müşteriler & Borç Durumları")
    if not veresiye_df.empty:
        st.dataframe(veresiye_df, use_container_width=True)
    elif not satis_df.empty:
        try:
            st.dataframe(satis_df.groupby("Müşteri / Dükkan").sum(numeric_only=True), use_container_width=True)
        except:
            st.dataframe(satis_df, use_container_width=True)
    else:
        st.info("Kayıtlı cari bulunamadı veya veriler henüz işlenmedi kanka.")

# 4. SEKME: DETAYLI MÜŞTERİ GEÇMİŞİ ARAMA
with sekme4:
    st.header("🔍 Detaylı Müşteri Sorgulama")
    arama_kelimesi = st.text_input("Müşteri adı veya dükkan adı yazın:")
    
    if arama_kelimesi:
