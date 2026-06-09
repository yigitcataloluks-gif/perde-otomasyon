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
    .stButton>button { background-color: #2563eb !important; color: white !important; border-radius: 6px !important; font-weight: bold !important; }
    div[data-testid="stMetricValue"] { color: #10b981 !important; }
    .sepet-kart { background-color: #27272a; padding: 12px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #2563eb; }
    </style>
""", unsafe_allow_html=True)

# --- LİNKLER ---
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"
DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]
STOK_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=Form+Yanıtları+1"
# KANKA: BURAYA FORM YANITLARININ DÜŞTÜĞÜ SEKMENİN YAYINLANMIŞ CSV LİNKİNİ YAPIŞTIR
SATIS_EXCEL_URL = "BURAYA_SATIŞ_SEKMESİNİN_CSV_LİNKİNİ_YAPISTIR"

def veri_yukle(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200: return pd.read_csv(StringIO(response.text))
        return pd.DataFrame()
    except: return pd.DataFrame()

def satis_kaydet_form(tarih, musteri, urunler, toplam, kaparo, kalan, notlar):
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/formResponse"
    payload = {
        "entry.1855648839": tarih, "entry.823126487": musteri, "entry.1481546114": urunler,
        "entry.1691060935": str(toplam), "entry.1099182379": str(kaparo),
        "entry.1843076127": str(kalan), "entry.2096359577": notlar
    }
    requests.post(form_url, data=payload)

# --- ŞİFRE ---
if "login" not in st.session_state: st.session_state["login"] = False
if not st.session_state["login"]:
    if st.text_input("Giriş Şifresi:", type="password") == "perde123":
        st.session_state["login"] = True
        st.rerun()
    st.stop()

if "sepet" not in st.session_state: st.session_state["sepet"] = []

stok_df = veri_yukle(STOK_CSV_URL)
sekme1, sekme2, sekme3, sekme4 = st.tabs(["🛒 Çoklu Satış", "📦 Ürün Ekle", "👥 Müşteri Cariler", "📊 Müşteri Arama"])

with sekme1:
    musteri_adi = st.text_input("👤 Müşteri Adı:")
    if not stok_df.empty:
        secilen_urun = st.selectbox("📦 Kumaş:", stok_df.iloc[:,1].unique())
        miktar = st.number_input("📏 Metre:", value=1.0)
        if st.button("➕ Sepete Ekle"):
            st.session_state["sepet"].append({"urun": secilen_urun, "miktar": miktar, "toplam": miktar*100})
            st.rerun()
        if st.session_state["sepet"]:
            if st.button("💾 Satışı Tamamla"):
                satis_kaydet_form(pd.Timestamp.now().strftime("%d/%m/%Y"), musteri_adi, "Detay", 100, 0, 100, "Not")
                st.session_state["sepet"] = []
                st.success("Kayıt Excel'e gönderildi!")
                st.rerun()

with sekme3:
    st.header("👥 Müşteri Cariler (Excel'den Anlık)")
    # Burada artık RAM'e değil, direkt Excel'e bakıyoruz
    df_satislar = veri_yukle(SATIS_EXCEL_URL)
    st.dataframe(df_satislar)

with sekme4:
    arama = st.text_input("Müşteri Ara:")
    df_satislar = veri_yukle(SATIS_EXCEL_URL)
    if arama and not df_satislar.empty:
        st.dataframe(df_satislar[df_satislar.astype(str).apply(lambda x: x.str.contains(arama, case=False)).any(axis=1)])
