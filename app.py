import streamlit as st
import pandas as pd
import requests
from io import StringIO
import urllib.parse

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Dükkan Satış & Stok Otomasyonu", page_icon="🧵", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #1a1a1e; color: #f4f4f5; }
    h1, h2, h3, h4 { color: #e4e4e7 !important; }
    .stButton>button { background-color: #2563eb !important; color: white !important; }
    .sepet-kart { background-color: #27272a; padding: 12px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #2563eb; }
    </style>
""", unsafe_allow_html=True)

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

# --- GEÇİCİ BELLEK ---
if "sepet" not in st.session_state: st.session_state["sepet"] = []

# --- SEKMELER ---
sekme1, sekme2, sekme3, sekme4 = st.tabs(["🛒 Çoklu Satış & Sepet Paneli", "📦 Stoğa Ürün Ekle", "👥 Müşteri Cariler", "📊 Müşteri Arama & Geçmiş"])

with sekme1:
    st.header("🛒 Gelişmiş Sipariş & Çoklu Satış")
    col_m1, col_m2 = st.columns(2)
    with col_m1: musteri_adi = st.text_input("👤 Müşteri / Dükkan Adı Soyadı:")
    with col_m2: musteri_telefon = st.text_input("📱 Müşteri Telefon Numarası:")
    
    st.info("Sepetiniz ve satışlarınız için şu an yerel bellek aktif.")

with sekme2:
    st.header("📦 Stoğa Yeni Mal Ekleme")
    st.components.v1.iframe(f"https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/viewform?embedded=true", height=600, scrolling=True)

with sekme3:
    st.header("👥 Kayıtlı Müşteriler & Borç Durumları")
    st.write("Cari bilgileriniz burada listelenecek.")

with sekme4:
    st.header("🔍 Detaylı Müşteri Sorgulama")
    st.text_input("Müşteri adı veya dükkan adı yazın kanka:")
