import streamlit as st
import pandas as pd
import requests
from io import StringIO
import urllib.parse

# --- SADE VE GÖZ YORMAYAN KOYU TEMA ---
st.set_page_config(page_title="Dükkan Satış & Stok Otomasyonu", page_icon="🧵", layout="wide")

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
    .sepet-kart {
        background-color: #27272a; padding: 12px; 
        border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #2563eb;
    }
    </style>
""", unsafe_allow_html=True)

# --- BAĞLANTILAR ---
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"
DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]
STOK_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=Form+Yanıtları+1"

# KANKA: BURAYA KENDİ SATIŞ SEKMENDEN ALDIĞIN CSV LİNKİNİ YAPIŞTIR
SATIS_EXCEL_CSV_URL = "BURAYA_CSV_LINKINI_YAPISTIR" 

def satis_kaydet_form(tarih, musteri, urunler, toplam, kaparo, kalan, notlar):
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/formResponse"
    payload = {
        "entry.1855648839": tarih, "entry.823126487": musteri, "entry.1481546114": urunler,
        "entry.1691060935": str(toplam), "entry.1099182379": str(kaparo),
        "entry.1843076127": str(kalan), "entry.2096359577": notlar
    }
    try: requests.post(form_url, data=payload)
    except: pass

def veri_yukle(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200: return pd.read_csv(StringIO(response.text))
        return pd.DataFrame()
    except: return pd.DataFrame()

# --- ŞİFRE KORUMASI ---
if "login" not in st.session_state: st.session_state["login"] = False
if not st.session_state["login"]:
    st.subheader("🔑 Dükkan Girişi")
    sifre = st.text_input("Giriş Şifresi:", type="password")
    if st.button("Giriş Yap", use_container_width=True):
        if sifre == "perde123":
            st.session_state["login"] = True
            st.rerun()
    st.stop()

# --- KALICI BELLEK ---
if "sepet" not in st.session_state: st.session_state["sepet"] = []

stok_df = veri_yukle(STOK_CSV_URL)
if not stok_df.empty:
    stok_df.columns = [stok_df.columns[0], "Ürün Adı", "Birim Fiyat"] if len(stok_df.columns) >= 3 else ["Zaman", "Ürün Adı", "Birim Fiyat"][:len(stok_df.columns)]

sekme1, sekme2, sekme3, sekme4 = st.tabs(["🛒 Çoklu Satış & Sepet Paneli", "📦 Stoğa Ürün Ekle", "👥 Müşteri Cariler", "📊 Müşteri Arama & Geçmiş"])

with sekme1:
    st.header("🛒 Gelişmiş Sipariş & Çoklu Satış")
    musteri_adi = st.text_input("👤 Müşteri / Dükkan Adı Soyadı:")
    if not stok_df.empty:
        c1, c2 = st.columns(2)
        with c1: cam_eni = st.number_input("📐 Cam Eni (Metre):", min_value=0.0, step=0.5, value=1.0)
        with c2: pile_turu = st.selectbox("🧵 Pile Oranı:", ["1'e 3 (Sık)", "1'e 2.5 (Normal)", "1'e 2 (Seyrek)", "Pilesiz"])
        gidecek_kumas = cam_eni * (3.0 if "3" in pile_turu else (2.5 if "2.5" in pile_turu else (2.0 if "2" in pile_turu else 1.0)))
        secilen_urun = st.selectbox("📦 Satılacak Kumaşı Seçin:", stok_df["Ürün Adı"].dropna().unique().tolist())
        birim_fiyat = float(stok_df[stok_df["Ürün Adı"] == secilen_urun].iloc[0]['Birim Fiyat'])
        miktar = st.number_input("📏 Satış Miktarı (Metre):", value=float(gidecek_kumas))
        
        if st.button("➕ Ürünü Sepete Ekle", use_container_width=True):
            st.session_state["sepet"].append({"urun": secilen_urun, "miktar": miktar, "fiyat": birim_fiyat, "toplam": miktar * birim_fiyat})
            st.rerun()

        if st.session_state["sepet"]:
            toplam_sepet = sum(i['toplam'] for i in st.session_state["sepet"])
            st.write(f"### Toplam Tutar: {toplam_sepet} TL")
            if st.button("💾 Satışı Tamamla & Kaydet", use_container_width=True):
                satis_kaydet_form(pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"), musteri_adi, "Detaylı Ürün", toplam_sepet, toplam_sepet, 0, "Otomatik")
                st.session_state["sepet"] = []
                st.success("Satış Excel'e kaydedildi!")
                st.rerun()

with sekme2:
    st.components.v1.iframe("https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/viewform?embedded=true", height=600)

with sekme3:
    st.header("👥 Müşteri Cariler (Excel'den Gelenler)")
    df_cariler = veri_yukle(SATIS_EXCEL_CSV_URL)
    st.dataframe(df_cariler, use_container_width=True)

with sekme4:
    st.header("🔍 Müşteri Sorgulama")
    arama = st.text_input("Müşteri adı:")
    df_cariler = veri_yukle(SATIS_EXCEL_CSV_URL)
    if arama and not df_cariler.empty:
        st.dataframe(df_cariler[df_cariler.astype(str).apply(lambda x: x.str.contains(arama, case=False)).any(axis=1)])
