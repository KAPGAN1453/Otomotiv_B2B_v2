import streamlit as st
import database as db
import pandas as pd

st.set_page_config(page_title="Otomotiv B2B Yönetim Paneli", page_icon="🏎️", layout="wide")

# Veritabanı Tablolarını Oluştur
db.init_db()

# Session State Kontrolleri
if "user" not in st.session_state:
    st.session_state.user = None

# --- GİRİŞ & KAYIT EKRANI ---
if st.session_state.user is None:
    st.title("🚗 Otomotiv B2B Saha & Müşteri Takip Sistemi")
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])

    with tab1:
        st.subheader("Kullanıcı Girişi")
        login_email = st.text_input("E-Posta Adresi", key="login_email")
        login_password = st.text_input("Şifre", type="password", key="login_pw")
        if st.button("Giriş Yap", type="primary"):
            user = db.login_user(login_email, login_password)
            if user:
                st.session_state.user = user
                st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                st.rerun()
            else:
                st.error("E-posta veya şifre hatalı!")

    with tab2:
        st.subheader("Yeni İşletme Kaydı")
        reg_name = st.text_input("Ad Soyad / Firma Yetkilisi")
        reg_phone = st.text_input("Telefon Numarası")
        reg_email = st.text_input("E-Posta Adresi")
        reg_address = st.text_area("İşletme Adresi")
        reg_password = st.text_input("Şifre Belirleyin", type="password")

        if st.button("Kayıt Ol"):
            if reg_name and reg_email and reg_password:
                success, msg = db.register_user(reg_name, reg_phone, reg_email, reg_address, reg_password)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.warning("Lütfen zorunlu alanları doldurun.")

else:
    # --- YÖNETİM PANELİ (ANA UYGULAMA) ---
    st.sidebar.title(f"👤 {st.session_state.user['full_name']}")
    st.sidebar.caption(st.session_state.user['address'])

    if st.sidebar.button("Çıkış Yap"):
        st.session_state.user = None
        st.rerun()

    st.sidebar.divider()
    menu = st.sidebar.radio("Modül Seçin", ["Ana Sayfa & Raporlar", "Müşteri Yönetimi", "Stok Yönetimi", "Saha Ziyaretleri"])

    st.title("🚗 Otomotiv B2B Yönetim Paneli")

    # 1. ANA SAYFA & RAPORLAR
    if menu == "Ana Sayfa & Raporlar":
        st.header("📊 Genel Durum & Raporlama")
        m_list = db.musterileri_getir()
        v_list = db.saha_ziyaretleri_getir()
        s_list = db.stoklari_getir()

        col1, col2, col3 = st.columns(3)
        col1.metric("Toplam Müşteri", len(m_list))
        col2.metric("Toplam Saha Ziyareti", len(v_list))
        col3.metric("Stoktaki Ürün Çeşidi", len(s_list))

    # 2. MÜŞTERİ YÖNETİMİ
    elif menu == "Müşteri Yönetimi":
        st.header("👥 Müşteri & Bayi Yönetimi")
        tab_m1, tab_m2 = st.tabs(["Müşteri Listesi", "Yeni Müşteri Ekle"])

        with tab_m1:
            m_list = db.musterileri_getir()
            if m_list:
                df = pd.DataFrame(m_list, columns=["ID", "Firma Adı", "Yetkili", "Telefon", "Şehir", "Adres", "Bakiye"])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Kayıtlı müşteri bulunmamaktadır.")

        with tab_m2:
            st.subheader("Yeni Müşteri Kaydı")
            f_adi = st.text_input("Firma Adı")
            yetkili = st.text_input("Yetkili Kişi")
            tel = st.text_input("Telefon")
            sehir = st.text_input("Şehir")
            adres = st.text_area("Açık Adres")
            bakiye = st.number_input("Başlangıç Bakiyesi / Risk Limiti (TL)", value=0.0)

            if st.button("Müşteriyi Kaydet"):
                if f_adi:
                    db.musteri_ekle(f_adi, yetkili, tel, sehir, bakiye, st.session_state.user['email'], adres)
                    st.success("Müşteri başarıyla eklendi!")
                    st.rerun()
                else:
                    st.warning("Firma adı zorunludur.")

    # 3. STOK YÖNETİMİ
    elif menu == "Stok Yönetimi":
        st.header("📦 Stok Yönetimi")
        tab_s1, tab_s2 = st.tabs(["Stok Listesi", "Yeni Ürün Ekle"])

        with tab_s1:
            s_list = db.stoklari_getir()
            if s_list:
                df_s = pd.DataFrame(s_list, columns=["ID", "Ürün Kodu", "Ürün Adı", "Kategori", "Adet", "Fiyat"])
                st.dataframe(df_s, use_container_width=True)
            else:
                st.info("Stokta ürün bulunmuyor.")

        with tab_s2:
            st.subheader("Yeni Ürün Kaydı")
            p_code = st.text_input("Ürün Kodu")
            p_name = st.text_input("Ürün Adı")
            p_cat = st.text_input("Kategori")
            p_qty = st.number_input("Stok Adedi", min_value=0, value=10)
            p_price = st.number_input("Birim Fiyat (TL)", min_value=0.0, value=100.0)

            if st.button("Ürünü Kaydet"):
                if p_code and p_name:
                    db.stok_ekle(p_code, p_name, p_cat, p_qty, p_price, st.session_state.user['email'])
                    st.success("Ürün stoğa eklendi!")
                    st.rerun()
                else:
                    st.warning("Ürün kodu ve adı zorunludur.")

    # 4. SAHA ZİYARETLERİ
    elif menu == "Saha Ziyaretleri":
        st.header("📍 Saha Ziyaret Kaydı")
        m_list = db.musterileri_getir()

        if not m_list:
            st.warning("Önce 'Müşteri Yönetimi' modülünden en az bir müşteri eklemelisiniz.")
        else:
            m_dict = {m[1]: m[1] for m in m_list}
            selected_m = st.selectbox("Müşteri Seçin", list(m_dict.keys()))
            z_tarih = st.date_input("Ziyaret Tarihi")
            z_not = st.text_area("Ziyaret Notları / Görüşme Detayı")

            if st.button("Ziyareti Kaydet"):
                db.saha_ziyareti_ekle(selected_m, str(z_tarih), z_not, "Tamamlandı", st.session_state.user['email'])
                st.success("Ziyaret kaydı oluşturuldu!")
                st.rerun()

            st.divider()
            st.subheader("Seçili Müşterinin Geçmiş Ziyaretleri")
            v_list = db.saha_ziyaretleri_getir(selected_m)
            if v_list:
                df_v = pd.DataFrame(v_list, columns=["ID", "Müşteri Adı", "Tarih", "Notlar", "Durum"])
                st.dataframe(df_v, use_container_width=True)
            else:
                st.info("Bu müşteriye ait geçmiş ziyaret kaydı yok.")