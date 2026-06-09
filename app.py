import streamlit as st
import pandas as pd
import requests
from io import StringIO

st.set_page_config(page_title="Dükkan Satış & Stok", layout="wide")

# --- LİNKLER ---
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"
DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]
STOK_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=Form+Yanıtları+1"

# KANKA: BURAYA "FORM YANITLARI 2" SEKMESİNİN CSV LİNKİNİ YAPIŞTIR
SATIS_EXCEL_CSV_URL = "BURAYA_CSV_LINKINI_YAPISTIR" 

def veri_yukle(url):
    try:
        r = requests.get(url, timeout=5)
        return pd.read_csv(StringIO(r.text)) if r.status_code == 200 else pd.DataFrame()
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

sekme1, sekme2, sekme3, sekme4 = st.tabs(["🛒 Satış", "📦 Stok Ekle", "👥 Cariler", "🔍 Arama"])

with sekme1:
    musteri_adi = st.text_input("👤 Müşteri Adı:")
    if not stok_df.empty:
        secilen_urun = st.selectbox("📦 Ürün:", stok_df.iloc[:,1].unique())
        miktar = st.number_input("📏 Miktar:", value=1.0)
        if st.button("➕ Sepete Ekle"):
            st.session_state["sepet"].append({"urun": secilen_urun, "miktar": miktar, "tutar": miktar*100})
            st.rerun()
        
        if st.session_state["sepet"]:
            toplam = sum(i['tutar'] for i in st.session_state["sepet"])
            if st.button("💾 Satışı Tamamla & Kaydet"):
                satis_kaydet_form(pd.Timestamp.now().strftime("%d/%m/%Y"), musteri_adi, "Detay", toplam, 0, toplam, "Not")
                st.session_state["sepet"] = []
                st.success("✅ Kayıt Excel'e gönderildi!")
                # Fatura mesajı
                fatura_link = f"https://wa.me/905XXXXXXXX?text=Sayın {musteri_adi}, toplam borcunuz: {toplam} TL."
                st.markdown(f"[🧾 Müşteriye WhatsApp'tan Fatura Gönder]({fatura_link})")
                st.rerun()

with sekme3:
    st.header("👥 Müşteri Cariler (Excel'den)")
    df = veri_yukle(SATIS_EXCEL_CSV_URL)
    st.dataframe(df)

with sekme4:
    arama = st.text_input("Müşteri Ara:")
    df = veri_yukle(SATIS_EXCEL_CSV_URL)
    if arama and not df.empty:
        st.dataframe(df[df.astype(str).apply(lambda x: x.str.contains(arama, case=False)).any(axis=1)])
