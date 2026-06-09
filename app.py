import streamlit as st
import pandas as pd
import requests
from io import StringIO
import urllib.parse

# --- SADE VE GÖZ YORMAYAN KOYU TEMA ---
st.set_page_config(page_title="Perde Otomasyon Sistemi", page_icon="🧵", layout="wide")

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
    .fatura-kutusu { 
        background-color: #ffffff; color: #000000; padding: 25px; 
        border-radius: 8px; font-family: 'Courier New', Courier, monospace;
        border: 2px dashed #000000; margin-top: 15px;
    }
    .sepet-kart {
        background-color: #27272a; padding: 12px; 
        border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #2563eb;
    }
    </style>
""", unsafe_allow_html=True)

# --- GOOGLE EXCEL BAĞLANTILARI ---
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"
DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]

# Google Formunun orijinal gömme linki (Ürün eklemek için buna dokunmuyoruz kanka)
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/viewform?embedded=true"

# Okunacak Sayfaların CSV Linkleri
STOK_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=stok"
SATIS_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=satis"
VERESIYE_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=veresiye"

def veri_yukle(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return pd.read_csv(StringIO(response.text))
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

# --- UYGULAMA HAFIZASI (SEPETİMİZ) ---
if "sepet" not in st.session_state:
    st.session_state["sepet"] = []
if "fatura_hazir" not in st.session_state:
    st.session_state["fatura_hazir"] = False
if "son_satis_bilgileri" not in st.session_state:
    st.session_state["son_satis_bilgileri"] = {}

# --- VERİLERİ CANLI ÇEK ---
stok_df = veri_yukle(STOK_CSV_URL)
satis_df = veri_yukle(SATIS_CSV_URL)
veresiye_df = veri_yukle(VERESIYE_CSV_URL)

# --- SEKMELER ---
sekme1, sekme2, sekme3, sekme4 = st.tabs(["🛒 Çoklu Satış & Sepet Paneli", "📦 Stoğa Ürün Ekle", "👥 Müşteri Cariler", "📊 Müşteri Arama & Geçmiş"])

# 1. SEKME: GELİŞMİŞ ÇOKLU SATIŞ VE WHATSAPP FATURA EKRANI
with sekme1:
    st.header("🛒 Gelişmiş Sipariş & Çoklu Satış")
    
    # Müşteri Bilgileri Üst Kısım
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        musteri_adi = st.text_input("👤 Müşteri / Dükkan Adı Soyadı:")
    with col_m2:
        musteri_telefon = st.text_input("📱 Müşteri Telefon Numarası (Örn: 905xxxxxxxxx):", help="Başında kodla birleşik yazın.")

    st.write("---")

    # Ürün ekleme kısmından gelen verileri buraya canlı çekiyoruz kanka:
    if stok_df.empty or "Ürün Adı" not in stok_df.columns:
        st.warning("⚠️ Stokta hiç ürün bulunamadı kanka. Lütfen yan sekmeden önce ürün ekleyin!")
    else:
        # Sol Taraf: Ürün Seçme ve Sepete Ekleme | Sağ Taraf: Aktif Sepet Görünümü
        col_sol, col_sag = st.columns([1.2, 1])
        
        with col_
