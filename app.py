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

# --- GOOGLE EXCEL BAĞLANTILARI (Stok Okuma) ---
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"
DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]
STOK_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=Form+Yanıtları+1"

# --- KALICI KAYIT FONKSİYONU (Arka planda Form'a yollar) ---
def satis_kaydet_form(tarih, musteri, urunler, toplam, kaparo, kalan, notlar):
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/formResponse"
    payload = {
        "entry.1855648839": tarih,
        "entry.823126487": musteri,
        "entry.1481546114": urunler,
        "entry.1691060935": str(toplam),
        "entry.1099182379": str(kaparo),
        "entry.1843076127": str(kalan),
        "entry.2096359577": notlar
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
        else: st.error("Hatalı şifre!")
    st.stop()

# --- KALICI BELLEK ---
if "sepet" not in st.session_state: st.session_state["sepet"] = []
if "fatura_hazir" not in st.session_state: st.session_state["fatura_hazir"] = False
if "son_satis_bilgileri" not in st.session_state: st.session_state["son_satis_bilgileri"] = {}
if "gercek_satis_listesi" not in st.session_state: st.session_state["gercek_satis_listesi"] = []

stok_df = veri_yukle(STOK_CSV_URL)
if not stok_df.empty:
    stok_df.columns = [stok_df.columns[0], "Ürün Adı", "Birim Fiyat"] if len(stok_df.columns) >= 3 else ["Zaman", "Ürün Adı", "Birim Fiyat"][:len(stok_df.columns)]

sekme1, sekme2, sekme3, sekme4 = st.tabs(["🛒 Çoklu Satış & Sepet Paneli", "📦 Stoğa Ürün Ekle", "👥 Müşteri Cariler", "📊 Müşteri Arama & Geçmiş"])

with sekme1:
    st.header("🛒 Gelişmiş Sipariş & Çoklu Satış")
    col_m1, col_m2 = st.columns(2)
    with col_m1: musteri_adi = st.text_input("👤 Müşteri / Dükkan Adı Soyadı:")
    with col_m2: musteri_telefon = st.text_input("📱 Müşteri Telefon Numarası (İsteğe Bağlı):")

    if not stok_df.empty and "Ürün Adı" in stok_df.columns:
        col_sol, col_sag = st.columns([1.2, 1])
        with col_sol:
            c1, c2 = st.columns(2)
            with c1: cam_eni = st.number_input("📐 Cam Eni (Metre):", min_value=0.0, step=0.5, value=1.0)
            with c2: pile_turu = st.selectbox("🧵 Pile Oranı:", ["1'e 3 (Sık)", "1'e 2.5 (Normal)", "1'e 2 (Seyrek)", "Pilesiz"])
            gidecek_kumas = cam_eni * (3.0 if "3" in pile_turu else (2.5 if "2.5" in pile_turu else (2.0 if "2" in pile_turu else 1.0)))
            urun_listesi = stok_df["Ürün Adı"].dropna().unique().tolist()
            secilen_urun = st.selectbox("📦 Satılacak Kumaşı Seçin:", urun_listesi)
            birim_fiyat = float(stok_df[stok_df["Ürün Adı"] == secilen_urun].iloc[0]['Birim Fiyat'])
            miktar = st.number_input("📏 Satış Miktarı (Metre):", value=float(gidecek_kumas))
            urun_notu = st.text_input("📝 Terzi / Dikim Notu:", value=f"{pile_turu} dikilecek.")
            
            if st.button("➕ Ürünü Sepete Ekle", use_container_width=True):
                st.session_state["sepet"].append({"urun": secilen_urun, "miktar": miktar, "fiyat": birim_fiyat, "toplam": miktar * birim_fiyat, "not": urun_notu})
                st.rerun()

        with col_sag:
            if not st.session_state["sepet"]: st.info("Sepet boş.")
            else:
                toplam_sepet_tutari, sepet_ozeti_yazi = 0.0, ""
                for eleman in st.session_state["sepet"]:
                    st.markdown(f'<div class="sepet-kart"><strong>{eleman["urun"]}</strong><br>Miktar: {eleman["miktar"]} Mt | Tutar: {eleman["toplam"]} TL</div>', unsafe_allow_html=True)
                    toplam_sepet_tutari += eleman['toplam']
                    sepet_ozeti_yazi += f"{eleman['urun']} ({eleman['miktar']}Mt), "
                
                st.markdown(f"### 🧾 Toplam: {toplam_sepet_tutari} TL")
                alinan_para = st.number_input("💵 Alınan Kaparo (TL):", min_value=0.0, value=toplam_sepet_tutari)
                kalan_borc = toplam_sepet_tutari - alinan_para
                
                if st.button("💾 Satışı Tamamla & Kaydet", use_container_width=True):
                    if not musteri_adi: st.error("Müşteri Adı gir!")
                    else:
                        su_an = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
                        satis_kaydet_form(su_an, musteri_adi, sepet_ozeti_yazi.strip(", "), toplam_sepet_tutari, alinan_para, kalan_borc, "Otomatik")
                        st.session_state["gercek_satis_listesi"].append({"Tarih / Zaman": su_an, "Müşteri / Dükkan": musteri_adi, "Satılan Ürün Detayı": sepet_ozeti_yazi.strip(", "), "Toplam Tutar (TL)": float(toplam_sepet_tutari), "Alınan Kaparo (TL)": float(alinan_para), "Kalan Net Borç (TL)": float(kalan_borc)})
                        st.session_state["fatura_hazir"], st.session_state["sepet"] = True, []
                        st.rerun()

with sekme2:
    st.components.v1.iframe("https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/viewform?embedded=true", height=600)

with sekme3:
    if st.session_state["gercek_satis_listesi"]: st.dataframe(pd.DataFrame(st.session_state["gercek_satis_listesi"]))

with sekme4:
    arama = st.text_input("Müşteri adı:")
    if arama and st.session_state["gercek_satis_listesi"]:
        df = pd.DataFrame(st.session_state["gercek_satis_listesi"])
        st.dataframe(df[df.astype(str).apply(lambda x: x.str.contains(arama, case=False)).any(axis=1)])
