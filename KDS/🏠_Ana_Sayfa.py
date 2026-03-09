import streamlit as st
from datetime import date, timedelta
import datetime
import time
import utils
from database.connection import get_db_connection
from database.dynamic_income import get_latest_fatura_metrics


st.set_page_config(
    page_title="Kurum Analiz Paneli", 
    layout="wide", 
    page_icon="🏥"
)


def check_password():
    if st.session_state.get("password_correct", False):
        return True

    st.title("🔐 Kurum Analiz Paneli Girişi")
    with st.form("login_form"):
        u_input = st.text_input("Kullanıcı Adı").strip()
        p_input = st.text_input("Şifre", type="password").strip()
        submitted = st.form_submit_button("Giriş Yap")

        if submitted:
            creds = st.secrets.get("credentials", {})
            if u_input in creds and str(creds[u_input]) == p_input:
                st.session_state["password_correct"] = True
                st.session_state["logged_in_user"] = u_input
                st.rerun()
            else:
                st.error("😕 Kullanıcı adı veya şifre hatalı")
    return False


if check_password():
   
    st.sidebar.header("📅 Global Filtreler")
    
    today = date.today()
    quick_choice = st.sidebar.selectbox(
        "Zaman Aralığı Seçin",
        ["Bugün", "Dün", "Son 7 Gün", "Son 30 Gün", "Bu Ay", "Geçen Ay", "Bu Yıl", "Geçen Yıl", "Özel"],
        index=4 
    )

   
    if quick_choice == "Bugün": start_date, end_date = today, today
    elif quick_choice == "Dün": start_date, end_date = today - timedelta(days=1), today - timedelta(days=1)
    elif quick_choice == "Son 7 Gün": start_date, end_date = today - timedelta(days=7), today
    elif quick_choice == "Son 30 Gün": start_date, end_date = today - timedelta(days=30), today
    elif quick_choice == "Bu Ay": start_date, end_date = today.replace(day=1), today
    elif quick_choice == "Geçen Ay":
        first_current = today.replace(day=1)
        end_date = first_current - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif quick_choice == "Bu Yıl": start_date, end_date = date(today.year, 1, 1), today
    elif quick_choice == "Geçen Yıl":
        last_year = today.year - 1
        start_date = date(last_year, 1, 1)
        end_date = date(last_year, 12, 31)
    else:
        start_date = st.sidebar.date_input("Başlangıç", today - timedelta(days=30))
        end_date = st.sidebar.date_input("Bitiş", today)

    st.session_state['start_date'] = start_date
    st.session_state['end_date'] = end_date

   
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.toast("Tüm veriler ve sunucu bağlantıları tazelendi!", icon="✅")
        time.sleep(0.6) # Toast'un görünmesi için kısa bekleme
        st.rerun()

    if st.sidebar.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.clear()
        st.rerun()

   
    current_hour = datetime.datetime.now().hour
    greeting = "İyi Günler" if 9 <= current_hour < 18 else "İyi Çalışmalar"
    
    st.title("🏥 Kurum Performans Yönetim Sistemi")
    st.caption(f"👋 {greeting}, **{st.session_state.get('logged_in_user')}**. Analiz periyodu: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}")
    
   
    st.markdown("### 🚀 Finansal Performans Özeti")
    
    start_perf = time.time()
    try:
        df_latest = get_latest_fatura_metrics()
        query_time = round(time.time() - start_perf, 3) 
        
        if not df_latest.empty:
            m = df_latest.iloc[0]
            avg_val = m['ToplamTutar'] / m['ToplamHasta'] if m['ToplamHasta'] > 0 else 0
            
            with st.container(border=True):
                met1, met2, met3 = st.columns(3)
                met1.metric("👥 Toplam Hasta", f"{int(m['ToplamHasta'])} Kişi", delta="Güncel Kayıt")
                met2.metric("💰 Toplam Gelir", f"₺{utils.format_turkish_number(m['ToplamTutar'])}", delta="Tahakkuk Eden")
                met3.metric("📊 Hasta Başı Ort.", f"₺{utils.format_turkish_number(avg_val)}", delta="Verimlilik")
            
            st.info(f"📄 **Sistem Notu:** En son `{m['FATURA_NO']}` nolu fatura grubu işlendi. Veriler bu grup üzerinden konsolide edilmiştir.")
        else:
            query_time = 0
            st.warning("⚠️ Seçilen aralıkta fatura verisi bulunamadı.")
    except Exception as e:
        query_time = 0
        st.error(f"⚠️ Veri yükleme hatası: {e}")

    st.divider()

   
    st.markdown("### 🛠️ Sistem Sağlık Durumu")
    c_sys1, c_sys2, c_sys3 = st.columns(3)
    
    with c_sys1:
        st.markdown("**📡 Sunucu Bağlantısı**")
        try:
            conn = get_db_connection()
            if conn:
                st.success("Çalışıyor: Bağlantı Sağlıklı")
                conn.close()
        except:
            st.error("Bağlantı Yok: SQL Server'a Erişilemiyor")

    with c_sys2:
        st.markdown("**⚡ Sorgu Performansı**")
        if query_time > 0:
            if query_time < 1.0:
                st.success(f"Çok Hızlı: {query_time} sn")
            else:
                st.warning(f"Normal: {query_time} sn")
        else:
            st.info("Ölçülmedi")

    with c_sys3:
        st.markdown("**🕒 Son Güncelleme**")
        st.info(datetime.datetime.now().strftime("%H:%M:%S"))

 
    utils.footer_ekle()
    ## st.markdown("<br><br><div style='text-align:center; color:gray; font-size: 0.8em; border-top: 1px solid #eee; padding-top: 10px;'>Kurum Karar Destek Sistemi v2.0 | © 2026 | Seyrani Demirel</div>", unsafe_allow_html=True)