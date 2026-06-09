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
    .sepet-kart {
        background-color: #27272a; padding: 12px; 
        border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #2563eb;
    }
    </style>
""", unsafe_allow_html=True)

# --- GOOGLE EXCEL BAĞLANTILARI ---
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"
DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]

# Google Formunun orijinal gömme linki (Ürün eklemek için buna dokunmuyoruz)
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
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        musteri_adi = st.text_input("👤 Müşteri / Dükkan Adı Soyadı:")
    with col_m2:
        musteri_telefon = st.text_input("📱 Müşteri Telefon Numarası (Örn: 905xxxxxxxxx):")

    st.write("---")

    if stok_df.empty or "Ürün Adı" not in stok_df.columns:
        st.warning("⚠️ Stokta hiç ürün bulunamadı kanka. Lütfen yan sekmeden önce ürün ekleyin!")
    else:
        col_sol, col_sag = st.columns([1.2, 1])
        
        with col_sol:
            st.subheader("🛍️ Sepete Ürün Ekle")
            
            c1, c2 = st.columns(2)
            with c1: cam_eni = st.number_input("📐 Cam Eni (Metre):", min_value=0.0, step=0.5, value=1.0)
            with c2: pile_turu = st.selectbox("🧵 Pile Oranı:", ["1'e 3 (Sık)", "1'e 2.5 (Normal)", "1'e 2 (Seyrek)", "Pilesiz"])
            
            carpan = 3.0 if "3" in pile_turu else (2.5 if "2.5" in pile_turu else (2.0 if "2" in pile_turu else 1.0))
            gidecek_kumas = cam_eni * carpan
            st.caption(f"🤖 Robot Hesaplaması: Gerekli Kumaş Miktarı **{gidecek_kumas} Metre**")

            urun_listesi = stok_df["Ürün Adı"].tolist()
            secilen_urun = st.selectbox("📦 Satılacak Kumaşı Seçin:", urun_listesi)
            
            urun_row = stok_df[stok_df["Ürün Adı"] == secilen_urun].iloc[0]
            try: birim_fiyat = float(urun_row['Birim Fiyat'])
            except: birim_fiyat = 0.0
            
            st.info(f"💰 Seçilen Ürünün Metre Fiyatı: {birim_fiyat} TL")
            
            miktar = st.number_input("📏 Satış Miktarı (Metre):", min_value=0.1, value=float(gidecek_kumas))
            urun_notu = st.text_input("📝 Terzi / Dikim Notu:", value=f"{pile_turu} dikilecek.")
            
            toplam_urun_fiyati = miktar * birim_fiyat
            
            if st.button("➕ Ürünü Sepete Ekle", use_container_width=True):
                st.session_state["sepet"].append({
                    "urun": secilen_urun,
                    "miktar": miktar,
                    "fiyat": birim_fiyat,
                    "toplam": toplam_urun_fiyati,
                    "not": urun_notu
                })
                st.success(f"{secilen_urun} sepete eklendi!")
                st.rerun()

        with col_sag:
            st.subheader("📋 Güncel Sepetiniz")
            if not st.session_state["sepet"]:
                st.info("Sepetiniz şu an boş kanka. Soldan ürün ekleyin.")
            else:
                toplam_sepet_tutari = 0.0
                for idx, eleman in enumerate(st.session_state["sepet"]):
                    st.markdown(f"""
                    <div class="sepet-kart">
                        <strong>{eleman['urun']}</strong><br>
                        📐 Miktar: {eleman['miktar']} Mt | Tutar: {eleman['toplam']} TL<br>
                        <small>📝 Not: {eleman['not']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    toplam_sepet_tutari += eleman['toplam']
                
                st.markdown(f"### 🧾 Toplam Tutar: {toplam_sepet_tutari} TL")
                
                alinan_para = st.number_input("💵 Alınan Kaparo / Ödeme (TL):", min_value=0.0, value=toplam_sepet_tutari)
                kalan_borc = toplam_sepet_tutari - alinan_para
                st.write(f"🔴 Kalan Borç (Veresiye): **{kalan_borc} TL**")
                
                c_b1, c_b2 = st.columns(2)
                with c_b1:
                    if st.button("💾 Satışı Tamamla & Fatura Kes", use_container_width=True):
                        if not musteri_adi:
                            st.error("Kanka fatura kesmek için önce Müşteri Adı yazmalısın!")
                        else:
                            st.session_state["son_satis_bilgileri"] = {
                                "musteri": musteri_adi,
                                "telefon": musteri_telefon if musteri_telefon else "Belirtilmedi",
                                "sepet": st.session_state["sepet"].copy(),
                                "toplam": toplam_sepet_tutari,
                                "alinan": alinan_para,
                                "kalan": kalan_borc,
                                "tarih": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
                            }
                            st.session_state["fatura_hazir"] = True
                            st.session_state["sepet"] = []
                            st.rerun()
                with c_b2:
                    if st.button("🗑️ Sepeti Boşalt", use_container_width=True):
                        st.session_state["sepet"] = []
                        st.session_state["fatura_hazir"] = False
                        st.rerun()

    # --- FATURA GÖSTERİMİ VE WHATSAPP GÖNDERME ALANI ---
    if st.session_state["fatura_hazir"]:
        st.write("---")
        st.subheader("🧾 Müşteri Satış Faturası")
        info = st.session_state["son_satis_bilgileri"]
        
        fatura_metni = f"========================================\n"
        fatura_metni += f"         PERDE OTOMASYON SİSTEMİ        \n"
        fatura_metni += f" Tarih: {info['tarih']}\n"
        fatura_metni += f" Müşteri: {info['musteri']}\n"
        fatura_metni += f" Tel: {info['telefon']}\n"
        fatura_metni += f"----------------------------------------\n"
        
        whatsapp_urunler = ""
        for s in info['sepet']:
            fatura_metni += f" * {s['urun']}\n"
            fatura_metni += f"   {s['miktar']} Mt x {s['fiyat']} TL = {s['toplam']} TL\n"
            fatura_metni += f"   Not: {s['not']}\n"
            whatsapp_urunler += f"- {s['urun']} ({s['miktar']} Mt): {s['toplam']} TL\n"
            
        fatura_metni += f"----------------------------------------\n"
        fatura_metni += f" TOPLAM TUTAR : {info['toplam']} TL\n"
        fatura_metni += f" ALINAN NAKİT : {info['alinan']} TL\n"
        fatura_metni += f" KALAN BORÇ   : {info['kalan']} TL\n"
        fatura_metni += f"========================================"
        
        st.code(fatura_metni)
        
        wp_mesaj = f"*Hayırlı İşler, Sipariş Özetiniz:*\n\n"
        wp_mesaj += f"👤 *Müşteri:* {info['musteri']}\n"
        wp_mesaj += f"📅 *Tarih:* {info['tarih']}\n\n"
        wp_mesaj += f"📦 *Alınan Ürünler:*\n{whatsapp_urunler}\n"
        wp_mesaj += f"💰 *Toplam Tutar:* {info['toplam']} TL\n"
        wp_mesaj += f"💵 *Ödenen Kaparo:* {info['alinan']} TL\n"
        wp_mesaj += f"📉 *Kalan Borç:* {info['kalan']} TL\n\n"
        wp_mesaj += f"Bizi tercih ettiğiniz için teşekkür ederiz!"
        
        encoded_wp = urllib.parse.quote(wp_mesaj)
        wp_link = f"https://api.whatsapp.com/send?phone={info['telefon']}&text={encoded_wp}"
        
        st.markdown(f'<a href="{wp_link}" target="_blank"><button style="background-color: #25d366; color: white; border: none; padding: 12px 20px; border-radius: 6px; font-weight: bold; cursor: pointer; width: 100%;">💬 Faturayı WhatsApp ile Müşteriye Gönder</button></a>', unsafe_allow_html=True)

# 2. SEKME: ÜRÜN EKLEME FORMU
with sekme2:
    st.header("📦 Stoğa Yeni Mal Ekleme")
    st.write("Yeni gelen kumaş veya tülleri Excel'e işlemek için formu doldurup en alttaki **'Gönder'** butonuna basman yeterlidir.")
    st.components.v1.iframe(FORM_URL, height=600, scrolling=True)
    
    st.write("---")
    st.subheader("📋 Sistemdeki Güncel Ürün Listesi")
    if not stok_df.empty:
        st.dataframe(stok_df, use_container_width=True)
    else:
        st.info("Kayıtlı ürün verisi yükleniyor kanka.")

# 3. SEKME: MÜŞTERİ CARİLERİ
with sekme3:
    st.header("👥 Kayıtlı Müşteriler & Borç Durumları")
    if not veresiye_df.empty:
        st.dataframe(veresiye_df, use_container_width=True)
    elif not satis_df.empty:
        try: st.dataframe(satis_df.groupby("Müşteri / Dükkan").sum(numeric_only=True), use_container_width=True)
        except: st.dataframe(satis_df, use_container_width=True)
    else:
        st.info("Kayıtlı cari bulunamadı kanka.")

# 4. SEKME: DETAYLI MÜŞTERİ GEÇMİŞİ ARAMA
with sekme4:
    st.header("🔍 Detaylı Müşteri Sorgulama")
    arama_kelimesi = st.text_input("Müşteri adı veya dükkan adı yazın kanka:")
    
    if arama_kelimesi:
        if not satis_df.empty:
            mask = satis_df.astype(str).apply(lambda x: x.str.contains(arama_kelimesi, case=False, na=False)).any(axis=1)
            sonuclar = satis_df[mask]
            if not sonuclar.empty:
                st.dataframe(sonuclar, use_container_width=True)
            else:
                st.warning("Bu isme ait geçmiş bir kayıt bulunamadı kanka.")
        else:
            st.error("Excel'deki satış geçmişi sayfası okunamadı.")
