import streamlit as st
import pandas as pd
import requests
from io import StringIO

# --- AYARLAR ---
st.set_page_config(page_title="Dükkan Satış & Stok Otomasyonu", page_icon="🧵", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #1a1a1e; color: #f4f4f5; }
    h1, h2, h3, h4 { color: #e4e4e7 !important; }
    .stButton>button { background-color: #2563eb !important; color: white !important; border-radius: 6px !important; font-weight: bold !important; }
    .sepet-kart { background-color: #27272a; padding: 12px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #2563eb; }
    </style>
""", unsafe_allow_html=True)

# --- BAĞLANTILAR ---
STOK_CSV_URL = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/gviz/tq?tqx=out:csv&sheet=Form+Yanıtları+1"
SATIŞLAR_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTzXUNpze1FKf3kpYTHGBZ-cqCrR8uOUqrHtbFahqr3D0qZ1_ZT_LXVb4auwSjUO1V2pp-3-ZF_6y47/pub?gid=1188156871&single=true&output=csv"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/formResponse"

# --- FONKSİYONLAR ---
def veri_yukle(url):
    try:
        r = requests.get(url, timeout=5)
        return pd.read_csv(StringIO(r.text)) if r.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

def satis_kaydet(tarih, musteri, urunler, toplam, kaparo, kalan):
    payload = {
        "entry.1855648839": tarih, "entry.823126487": musteri, "entry.1481546114": urunler,
        "entry.1691060935": str(toplam), "entry.1099182379": str(kaparo), "entry.1843076127": str(kalan)
    }
    requests.post(FORM_URL, data=payload)

# --- ŞİFRE KORUMASI ---
if "login" not in st.session_state: st.session_state["login"] = False
if not st.session_state["login"]:
    st.subheader("🔑 Dükkan Girişi")
    if st.text_input("Giriş Şifresi:", type="password") == "perde123":
        st.session_state["login"] = True
        st.rerun()
    st.stop()

# --- ANA UYGULAMA ---
if "sepet" not in st.session_state: st.session_state["sepet"] = []

stok_df = veri_yukle(STOK_CSV_URL)
sekme1, sekme2, sekme3, sekme4 = st.tabs(["🛒 Çoklu Satış & Sepet Paneli", "📦 Stoğa Ürün Ekle", "👥 Müşteri Cariler", "📊 Müşteri Arama & Geçmiş"])

with sekme1:
    st.header("🛒 Gelişmiş Sipariş & Çoklu Satış")
    col_m1, col_m2 = st.columns(2)
    with col_m1: musteri_adi = st.text_input("👤 Müşteri / Dükkan Adı:")
    with col_m2: st.text_input("📱 Telefon:")

    if not stok_df.empty:
        c1, c2 = st.columns(2)
        with c1: cam_eni = st.number_input("📐 Cam Eni (Metre):", min_value=0.0, step=0.5, value=1.0)
        with c2: pile = st.selectbox("🧵 Pile Oranı:", ["1'e 3 (Sık)", "1'e 2.5 (Normal)", "1'e 2 (Seyrek)", "Pilesiz"])
        
        urun_listesi = stok_df.iloc[:,1].dropna().unique().tolist()
        secilen_urun = st.selectbox("📦 Kumaş:", urun_listesi)
        miktar = st.number_input("📏 Miktar (Mt):", value=float(cam_eni * 2.5))
        
        if st.button("➕ Ürünü Sepete Ekle"):
            st.session_state["sepet"].append({"urun": secilen_urun, "miktar": miktar})
            st.rerun()

        if st.session_state["sepet"]:
            st.markdown("---")
            st.write("### 🛒 Sepetiniz:")
            for s in st.session_state["sepet"]: st.write(f"- {s['urun']}: {s['miktar']} metre")
            
            kaparo = st.number_input("💵 Alınan Kaparo (TL):")
            if st.button("💾 Satışı Tamamla & Kaydet"):
                satis_kaydet(pd.Timestamp.now().strftime("%d/%m/%Y"), musteri_adi, str(st.session_state["sepet"]), 0, kaparo, 0)
                st.session_state["sepet"] = []
                st.success("✅ Satış başarıyla forma işlendi!")
                st.rerun()

with sekme2:
    st.header("📦 Stoğa Ürün Ekle")
    st.components.v1.iframe("https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/viewform?embedded=true", height=600)

with sekme3:
    st.header("👥 Müşteri Cariler")
    st.dataframe(veri_yukle(SATIŞLAR_CSV_URL), use_container_width=True)

with sekme4:
    st.header("🔍 Müşteri Arama")
    arama = st.text_input("Müşteri adı:")
    df = veri_yukle(SATIŞLAR_CSV_URL)
    if arama and not df.empty:
        st.dataframe(df[df.astype(str).apply(lambda x: x.str.contains(arama, case=False)).any(axis=1)], use_container_width=True)
