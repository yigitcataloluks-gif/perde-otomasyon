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

# Formların linkleri hazır gömülü kanka:
FORM_URUN_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/viewform?embedded=true"
SATIS_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/viewform?embedded=true"

# Okunacak Sayfaların CSV Linkleri
STOK_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=stok"
SATIS_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=satis"
VERESIYE_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=veresiye"

# Formların yedek okuma linkleri:
FORM_YANIT_1_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=Form Yanıtları 1"
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

# --- VERI YÜKLEME ---
stok_df = veri_yukle(STOK_CSV_URL)
satis_df = veri_yukle(SATIS_CSV_URL)
veresiye_df = veri_yukle(VERESIYE_CSV_URL)
form_urun_df = veri_yukle(FORM_YANIT_1_URL)
form_satis_df = veri_yukle(FORM_SATIS_URL)

# KANKA BÜTÜN YARIM KALAN YERLER JİLET GİBİ TAMAMLANDI:
if satis_df.empty and not form_satis_df.empty:
    satis_df = form_satis_df
if stok_df.empty and not form_urun_df.empty:
    stok_df = form_urun_df

# --- SEKMELER TANIMLANIYOR ---
sekme1, sekme2, sekme3, sekme4 = st.tabs(["🛒 Sipariş & Satış Formu", "📦 Ürün Giriş Formu", "👥 Müşteri Cariler", "📊 Müşteri Arama & Geçmiş"])

# 1. SEKME: SATIŞ FORMU (GÖMÜLÜ)
with sekme1:
    st.header("🛒 Satış & Sipariş Kayıt Ekranı")
    st.write("Abicim, satışı ve siparişi kaydetmek için aşağıdaki formu doldurup 'Gönder' demen yeterlidir. Veriler anında hafızaya işlenir.")
    st.components.v1.iframe(SATIS_FORM_URL, height=550, scrolling=True)

# 2. SEKME: ÜRÜN GİRİŞ FORMU (GÖMÜLÜ)
with sekme2:
    st.header("📦 Stoğa Yeni Mal Ekleme")
    st.write("Yeni gelen kumaş veya tülleri buradan ekleyebilirsiniz. Eklenen mallar aşağıdaki listede anında güncellenir.")
    st.components.v1.iframe(FORM_URUN_URL, height=450, scrolling=True)
    
    st.write("---")
    st.subheader("📋 Güncel Stok Listesi")
    if not stok_df.empty:
        st.dataframe(stok_df, use_container_width=True)
    else:
        st.info("Kayıtlı stok bulunamadı veya henüz yüklenmedi kanka.")

# 3. SEKME: CARİLER VE BORÇLAR
with sekme3:
    st.header("👥 Kayıtlı Müşteriler & Borç Durumları")
    if not veresiye_df.empty:
        st.dataframe(veresiye_df, use_container_width=True)
    elif not satis_df.empty:
        st.caption("*(Satış verilerinden canlı hesaplanan borç listesi)*")
        try:
            cari_ozet = satis_df.groupby("Müşteri / Dükkan").sum(numeric_only=True)
            st.dataframe(cari_ozet, use_container_width=True)
        except:
            st.dataframe(satis_df, use_container_width=True)
    else:
        st.info("Henüz kayıtlı cari veya borç verisi bulunamadı kanka.")

# 4. SEKME: MÜŞTERİ SORGULAMA VE ARAMA MOTORU
with sekme4:
    st.header("🔍 Detaylı Müşteri Sorgulama Paneli")
    st.write("Müşterinin adını yazarak hangi gün ne aldığını, ne kadar ödediğini ve geçmiş tüm sipariş detaylarını anında listeleyebilirsiniz.")
    
    arama_kelimesi = st.text_input("Müşteri veya Dükkan Adı Yazın (Örn: Ahmet, Akdeniz Mobilya):")
    
    if arama_kelimesi:
        if not satis_df.empty:
            mask = satis_df.astype(str).apply(lambda x: x.str.contains(arama_kelimesi, case=False, na=False)).any(axis=1)
            sonuclar = satis_df[mask]
            
            if sonuclar.empty:
                st.warning(f"'{arama_kelimesi}' ismine ait geçmiş bir satış kaydı bulunamadı kanka.")
            else:
                st.subheader(f"📋 {arama_kelimesi} İsimli Müşterinin Tüm Alışveriş Dosyası")
                st.dataframe(sonuclar, use_container_width=True)
        else:
            st.error("Excel'deki satış geçmişi sayfası okunamadı veya bomboş kanka.")
