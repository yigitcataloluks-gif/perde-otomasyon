import streamlit as st
import pandas as pd
import requests
from io import StringIO
import urllib.parse
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

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

# --- GOOGLE EXCEL CANLI BAĞLANTISI ---
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"
DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]
STOK_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=Form+Yanıtları+1"

def excel_baglan():
    try:
        # GitHub Secrets'tan senin o kaydettiğin anahtarı çekiyoruz kanka
        creds_json = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
        client = gspread.authorize(creds)
        
        # Excel dosyasının içindeki "satis" isimli sayfaya bağlanıyoruz
        sheet = client.open_by_key(DOC_ID).worksheet("satis")
        return sheet
    except Exception as e:
        return None

def stok_yukle(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return pd.read_csv(StringIO(response.text))
        return pd.DataFrame()
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

# --- GEÇİCİ BELLEK (Sadece Canlı Sepet İçin) ---
if "sepet" not in st.session_state: st.session_state["sepet"] = []
if "fatura_hazir" not in st.session_state: st.session_state["fatura_hazir"] = False
if "son_satis_bilgileri" not in st.session_state: st.session_state["son_satis_bilgileri"] = {}

# --- VERİLERİ CANLI ÇEK ---
stok_df = stok_yukle(STOK_CSV_URL)
if not stok_df.empty:
    stok_df.columns = [stok_df.columns[0], "Ürün Adı", "Birim Fiyat"] if len(stok_df.columns) >= 3 else ["Zaman", "Ürün Adı", "Birim Fiyat"][:len(stok_df.columns)]

satis_sheet = excel_baglan()

# --- SEKMELER ---
sekme1, sekme2, sekme3, sekme4 = st.tabs(["🛒 Çoklu Satış & Sepet Paneli", "📦 Stoğa Ürün Ekle", "👥 Müşteri Cariler", "📊 Müşteri Arama & Geçmiş"])

# 1. SEKME: ÇOKLU SATIŞ PANELİ
with sekme1:
    st.header("🛒 Gelişmiş Sipariş & Çoklu Satış")
    col_m1, col_m2 = st.columns(2)
    with col_m1: musteri_adi = st.text_input("👤 Müşteri / Dükkan Adı Soyadı:")
    with col_m2: musteri_telefon = st.text_input("📱 Müşteri Telefon Numarası (İsteğe Bağlı):")

    st.write("---")

    if stok_df.empty or "Ürün Adı" not in stok_df.columns:
        st.warning("⚠️ Stokta hiç ürün yok kanka. Önce ürün ekleyin.")
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

            urun_listesi = stok_df["Ürün Adı"].dropna().unique().tolist()
            secilen_urun = st.selectbox("📦 Satılacak Kumaşı Seçin:", urun_listesi)
            urun_row = stok_df[stok_df["Ürün Adı"] == secilen_urun].iloc[0]
            try: birim_fiyat = float(urun_row['Birim Fiyat'])
            except: birim_fiyat = 0.0
            
            st.info(f"💰 Seçilen Ürünün Metre Fiyatı: {birim_fiyat} TL")
            miktar = st.number_input("📏 Satış Miktarı (Metre):", min_value=0.1, value=float(gidecek_kumas) if gidecek_kumas > 0 else 1.0)
            urun_notu = st.text_input("📝 Terzi / Dikim Notu:", value=f"{pile_turu} dikilecek.")
            toplam_urun_fiyati = miktar * birim_fiyat
            
            if st.button("➕ Ürünü Sepete Ekle", use_container_width=True):
                st.session_state["sepet"].append({"urun": secilen_urun, "miktar": miktar, "fiyat": birim_fiyat, "toplam": toplam_urun_fiyati, "not": urun_notu})
                st.success(f"'{secilen_urun}' sepete eklendi!")
                st.rerun()

        with col_sag:
            st.subheader("📋 Güncel Sepetiniz")
            if not st.session_state["sepet"]:
                st.info("Sepetiniz şu an boş kanka.")
            else:
                toplam_sepet_tutari = 0.0
                sepet_ozeti_yazi = ""
                for eleman in st.session_state["sepet"]:
                    st.markdown(f'<div class="sepet-kart"><strong>{eleman["urun"]}</strong><br>📐 Miktar: {eleman["miktar"]} Mt | Tutar: {eleman["toplam"]} TL<br><small>📝 Not: {eleman["not"]}</small></div>', unsafe_allow_html=True)
                    toplam_sepet_tutari += eleman['toplam']
                    sepet_ozeti_yazi += f"{eleman['urun']} ({eleman['miktar']}Mt), "
                
                st.markdown(f"### 🧾 Toplam Tutar: {toplam_sepet_tutari} TL")
                alinan_para = st.number_input("💵 Alınan Kaparo (TL):", min_value=0.0, value=toplam_sepet_tutari)
                kalan_borc = toplam_sepet_tutari - alinan_para
                st.write(f"🔴 Kalan Borç (Veresiye): **{kalan_borc} TL**")
                
                c_b1, c_b2 = st.columns(2)
                with c_b1:
                    if st.button("💾 Satışı Tamamla & Kaydet", use_container_width=True):
                        if not musteri_adi:
                            st.error("Kanka önce Müşteri Adı yazmalısın!")
                        else:
                            su_an = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
                            st.session_state["son_satis_bilgileri"] = {"musteri": musteri_adi, "sepet": st.session_state["sepet"].copy(), "toplam": toplam_sepet_tutari, "alinan": alinan_para, "kalan": kalan_borc, "tarih": su_an}
                            
                            # KANKA BURASI ARTIK ÖMÜRLÜK: Doğrudan Excel'e satır fırlatıyoruz!
                            if satis_sheet is not None:
                                try:
                                    satis_sheet.append_row([su_an, musteri_adi, sepet_ozeti_yazi.strip(", "), float(toplam_sepet_tutari), float(alinan_para), float(kalan_borc)])
                                    st.toast("Satış Excel'e ömürlük kaydedildi! 📄", icon="💾")
                                except Exception as e:
                                    st.error(f"Excel'e yazılırken hata çıktı kanka: {e}")
                            else:
                                st.error("Google Excel bağlantısı kurulamadı! Lütfen secrets ayarını kontrol et kanka.")
                            
                            st.session_state["fatura_hazir"] = True
                            st.session_state["sepet"] = []
                            st.rerun()
                with c_b2:
                    if st.button("🗑️ Sepeti Boşalt", use_container_width=True):
                        st.session_state["sepet"] = []
                        st.session_state["fatura_hazir"] = False
                        st.rerun()

    # --- FATURA GÖSTERİMİ VE REHBER SEÇMELİ WHATSAPP ---
    if st.session_state["fatura_hazir"]:
        st.write("---")
        st.subheader("🧾 Müşteri Satış Faturası")
        info = st.session_state["son_satis_bilgileri"]
        fatura_metni = f"========================================\n             SATIŞ FİŞİ / ÖZET          \n Tarih: {info['tarih']}\n Müşteri: {info['musteri']}\n----------------------------------------\n"
        whatsapp_urunler = ""
        for s in info['sepet']:
            fatura_metni += f" * {s['urun']}\n   {s['miktar']} Mt x {s['fiyat']} TL = {s['toplam']} TL\n"
            whatsapp_urunler += f"- {s['urun']} ({s['miktar']} Mt): {s['toplam']} TL\n"
        fatura_metni += f"----------------------------------------\n TOPLAM TUTAR : {info['toplam']} TL\n ALINAN NAKİT : {info['alinan']} TL\n KALAN BORÇ   : {info['kalan']} TL\n========================================"
        st.code(fatura_metni)
        
        wp_mesaj = f"*Sipariş Özetiniz:*\n\n👤 *Müşteri:* {info['musteri']}\n📅 *Tarih:* {info['tarih']}\n\n📦 *Ürünler:*\n{whatsapp_urunler}\n💰 *Toplam:* {info['toplam']} TL\n💵 *Kaparo:* {info['alinan']} TL\n📉 *Kalan Borç:* {info['kalan']} TL"
        st.markdown(f'<a href="https://web.whatsapp.com/send?text={urllib.parse.quote(wp_mesaj)}" target="_blank"><button style="background-color: #25d366; color: white; border: none; padding: 12px 20px; border-radius: 6px; font-weight: bold; cursor: pointer; width: 100%;">💬 Faturayı WhatsApp ile Gönder</button></a>', unsafe_allow_html=True)

# 2. SEKME: ÜRÜN EKLEME FORMU
with sekme2:
    st.header("📦 Stoğa Yeni Mal Ekleme")
    st.components.v1.iframe(f"https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/viewform?embedded=true", height=600, scrolling=True)

# 3. SEKME: MÜŞTERİ CARİLERİ (HER REFRESH'TE CANLI EXCEL'DEN OKUR)
with sekme3:
    st.header("👥 Kayıtlı Müşteriler & Borç Durumları (Kalıcı Excel Hafızası)")
    if satis_sheet is not None:
        try:
            canli_veriler = satis_sheet.get_all_records()
            if canli_veriler:
                df_cariler = pd.DataFrame(canli_veriler)
                st.dataframe(df_cariler, use_container_width=True)
                
                st.write("---")
                t_ciro = pd.to_numeric(df_cariler.iloc[:, 3], errors='coerce').sum()
                t_alinan = pd.to_numeric(df_cariler.iloc[:, 4], errors='coerce').sum()
                t_kalan = pd.to_numeric(df_cariler.iloc[:, 5], errors='coerce').sum()
                
                col_t1, col_t2, col_t3 = st.columns(3)
                with col_t1: st.metric(label="📊 Toplam Yapılan Satış (Ciro)", value=f"{t_ciro:,.2f} TL")
                with col_t2: st.metric(label="💰 Kasaya Giren Toplam Nakit", value=f"{t_alinan:,.2f} TL")
                with col_t3: st.metric(label="🔴 Dışarıdaki Toplam Alacak (Veresiye)", value=f"{t_kalan:,.2f} TL")
            else: st.info("Excel'de henüz kayıtlı satış bulunmuyor kanka.")
        except Exception as e: st.error(f"Veriler Excel'den çekilirken hata oluştu: {e}")
    else:
        st.warning("Excel tablosuna şu an bağlanılamıyor, lütfen sayfayı yenileyin.")

# 4. SEKME: DETAYLI MÜŞTERİ GEÇMİŞİ ARAMA
with sekme4:
    st.header("🔍 Detaylı Müşteri Sorgulama")
    arama_kelimesi = st.text_input("Müşteri adı veya dükkan adı yazın kanka:")
    if arama_kelimesi and satis_sheet is not None:
        try:
            canli_veriler = satis_sheet.get_all_records()
            if canli_veriler:
                df_cariler = pd.DataFrame(canli_veriler)
                mask = df_cariler.astype(str).apply(lambda x: x.str.contains(arama_kelimesi, case=False, na=False)).any(axis=1)
                sonuclar = df_cariler[mask]
                if not sonuclar.empty: st.dataframe(sonuclar, use_container_width=True)
                else: st.warning("Bu isme ait geçmiş bir kayıt bulunamadı kanka.")
        except: pass
