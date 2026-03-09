import streamlit as st
import locale


def format_turkish_number(value, decimals=2):
    """Sayıyı Türkçe formatta biçimlendirir (nokta=binlik, virgül=ondalık)."""
    try:
        value = float(value)
        if decimals == 0:
            formatted = f"{value:,.0f}"
        else:
            formatted = f"{value:,.{int(decimals)}f}"
        # İngilizce formatı Türkçe'ye çevir: 1,234.56 -> 1.234,56
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted
    except (ValueError, TypeError):
        return str(value)


def footer_ekle():
    """Sayfanın altına standart footer ekler."""
    st.markdown(
        "<br><br><div style='text-align:center; color:gray; font-size: 0.8em; "
        "border-top: 1px solid #eee; padding-top: 10px;'>"
        "Kurum Karar Destek Sistemi v2.0 | © 2026 | Seyrani Demirel"
        "</div>",
        unsafe_allow_html=True,
    )


def aktif_donem_goster():
    """Seçili tarih aralığını sayfa üstünde bilgi kutusu olarak gösterir."""
    start_date = st.session_state.get("start_date")
    end_date = st.session_state.get("end_date")
    if start_date and end_date:
        st.info(
            f"📅 Aktif Dönem: **{start_date.strftime('%d.%m.%Y')}** – "
            f"**{end_date.strftime('%d.%m.%Y')}**"
        )


def generate_smart_insights(df, group_col, revenue_col, count_col, top_n=3):
    """DataFrame'den akıllı içgörüler üretir. Dönen liste string satırlarından oluşur."""
    insights = []
    if df.empty:
        return insights

    try:
        sorted_rev = df.sort_values(revenue_col, ascending=False)
        top = sorted_rev.head(top_n)
        for _, row in top.iterrows():
            insights.append(
                f"🏆 **{row[group_col]}**: {format_turkish_number(row[revenue_col])} ₺ gelir, "
                f"{format_turkish_number(row[count_col], 0)} işlem"
            )

        if len(df) > 1:
            total_rev = df[revenue_col].sum()
            top_rev = top[revenue_col].sum()
            if total_rev > 0:
                pct = (top_rev / total_rev) * 100
                insights.append(
                    f"📊 İlk {top_n} grup, toplam gelirin **%{pct:.1f}**'ini oluşturuyor."
                )
    except Exception:
        pass

    return insights


def get_dynamic_insights(df, name_col, sort_col, top_n=3):
    """Performans sıralamasına göre dinamik içgörüler üretir."""
    insights = []
    if df.empty:
        return insights

    try:
        sorted_df = df.sort_values(sort_col, ascending=False)
        top = sorted_df.head(top_n)
        for _, row in top.iterrows():
            insights.append(
                f"⭐ **{row[name_col]}**: {format_turkish_number(row[sort_col], 0)} "
                f"({sort_col})"
            )

        if len(df) > top_n:
            bottom = sorted_df.tail(1).iloc[0]
            insights.append(
                f"📉 En düşük: **{bottom[name_col]}** – "
                f"{format_turkish_number(bottom[sort_col], 0)}"
            )
    except Exception:
        pass

    return insights
