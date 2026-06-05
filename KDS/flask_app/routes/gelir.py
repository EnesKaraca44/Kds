from flask import Blueprint, render_template, request, Response
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from database.fatura_sorgular import fatura_gelir_verisi_yukle
from database.vezne_sorgular import (
    kasa_aylik_verisi_yukle,
    kasa_hareket_turu_verisi_yukle,
    kasa_ozet_verisi_yukle,
)
from routes.dashboard import get_date_range

gelir_bp = Blueprint('gelir', __name__)

PAGE_SQL_KODLARI = [
    "fatura.fatura_gelir_verisi_yukle",
    "vezne.kasa_ozet_verisi_yukle",
    "vezne.kasa_hareket_turu_verisi_yukle",
    "vezne.kasa_aylik_verisi_yukle",
]

FATURA_COLUMN_LABELS = {
    'FATURA_NO': 'Fatura No',
    'FATURA_TARIHI': 'Fatura Tarihi',
    'FATURA_ILGILI': 'Fatura İlgili',
    'KURUM_TURU': 'Kurum Türü',
    'FATURA_KDVLI_TOPLAM_TUTAR': 'KDV Dahil Tutar',
    'FATURA_KISI_SAYISI': 'Kişi Sayısı',
    'FATURA_ACIKLAMA': 'Açıklama',
    'FATURA_TOPLAM_KDV': 'Toplam KDV',
    'FATURA_TOPLAM_TUTAR': 'Net Tutar',
}

MONEY_TABLE_COLUMNS = frozenset({
    'FATURA_KDVLI_TOPLAM_TUTAR',
    'FATURA_TOPLAM_TUTAR',
    'FATURA_TOPLAM_KDV',
})

INT_TABLE_COLUMNS = frozenset({'FATURA_KISI_SAYISI'})

# Grafik ve KPI'larda kullanilan gelir tutari (KDV haric)
GELIR_TUTAR_KOLONU = 'FATURA_TOPLAM_TUTAR'

MONEY_DF_COLUMNS = (
    GELIR_TUTAR_KOLONU,
    'FATURA_KDVLI_TOPLAM_TUTAR',
    'FATURA_TOPLAM_KDV',
)


def _coerce_invoice_money_columns(df):
    """Tutar kolonlarini sayisal yap; grafik toplamlari dogru hesaplansin."""
    for col in MONEY_DF_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    return df


def _fatura_column_label(column_key):
    """FATURA_NO -> Fatura No; bilinmeyen kolonlar okunakli basliga cevrilir."""
    key = str(column_key or '').upper().strip()
    if key in FATURA_COLUMN_LABELS:
        return FATURA_COLUMN_LABELS[key]
    return ' '.join(part.capitalize() for part in key.split('_') if part)


def _table_columns_meta(column_keys):
    return [{'key': col, 'label': _fatura_column_label(col)} for col in column_keys]


def _format_table_cell(column_key, value):
    key = str(column_key or '').upper().strip()
    if pd.isna(value) or value == '':
        return ''
    if key == 'FATURA_TARIHI':
        try:
            return pd.to_datetime(value).strftime('%d.%m.%Y')
        except (TypeError, ValueError):
            return value
    if key in MONEY_TABLE_COLUMNS:
        try:
            return float(value)
        except (TypeError, ValueError):
            return value
    if key in INT_TABLE_COLUMNS:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return value
    return value


def _load_invoice_df():
    """Seçili tarih aralığına göre fatura verisini döndürür."""
    sd, ed = get_date_range()
    df = fatura_gelir_verisi_yukle(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))
    if df.empty:
        return sd, ed, df

    df = df.copy()
    df.columns = [c.upper().strip() for c in df.columns]
    df['FATURA_TARIHI'] = pd.to_datetime(df['FATURA_TARIHI'], errors='coerce')
    df = _coerce_invoice_money_columns(df)
    return sd, ed, df


def format_tr_money(val):
    try:
        if pd.isna(val): return "0 ₺"
        s = f"{float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if s.endswith(",00"): s = s[:-3]
        return f"{s} ₺"
    except:
        return "0 ₺"


@gelir_bp.route('/gelir')
@login_required
def gelir():
    sd, ed, df = _load_invoice_df()

    # Removed early exit for df.empty to allow vezne data to render

    # Vezne (Kasa) verileri
    vezne_kasa_df = kasa_ozet_verisi_yukle(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))
    vezne_kasa_rows = vezne_kasa_df.to_dict(orient='records') if not vezne_kasa_df.empty else []
    t_vezne_gelir = float(vezne_kasa_df['tahsilatToplam'].sum()) if (not vezne_kasa_df.empty and 'tahsilatToplam' in vezne_kasa_df.columns) else 0.0
    vezne_kasa_totals = {
        "tahsilatToplam": float(vezne_kasa_df["tahsilatToplam"].sum()) if (not vezne_kasa_df.empty and "tahsilatToplam" in vezne_kasa_df.columns) else 0.0,
        "odemeToplam": float(vezne_kasa_df["odemeToplam"].sum()) if (not vezne_kasa_df.empty and "odemeToplam" in vezne_kasa_df.columns) else 0.0,
        "kalan": float(vezne_kasa_df["kalan"].sum()) if (not vezne_kasa_df.empty and "kalan" in vezne_kasa_df.columns) else 0.0,
        "iptalToplam": float(vezne_kasa_df["iptalToplam"].sum()) if (not vezne_kasa_df.empty and "iptalToplam" in vezne_kasa_df.columns) else 0.0,
    }

    selected_kasa_id = request.args.get('kasaId')
    if (not selected_kasa_id) and vezne_kasa_rows:
        selected_kasa_id = str(vezne_kasa_rows[0].get('kasaId'))

    try:
        selected_kasa_id_int = int(selected_kasa_id) if selected_kasa_id is not None else None
    except (TypeError, ValueError):
        selected_kasa_id_int = None

    vezne_hareket_rows = []
    vezne_aylik_rows = []
    vezne_hareket_totals = {"tahsilatToplam": 0.0, "odemeToplam": 0.0}
    fig_vezne_kasa = None
    fig_vezne_aylik = None
    fig_vezne_hareket = None
    if selected_kasa_id_int is not None:
        hareket_df = kasa_hareket_turu_verisi_yukle(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'), selected_kasa_id_int)
        aylik_df = kasa_aylik_verisi_yukle(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'), selected_kasa_id_int)
        vezne_hareket_rows = hareket_df.to_dict(orient='records') if not hareket_df.empty else []
        vezne_aylik_rows = aylik_df.to_dict(orient='records') if not aylik_df.empty else []
        if not hareket_df.empty:
            if "tahsilatToplam" in hareket_df.columns:
                vezne_hareket_totals["tahsilatToplam"] = float(hareket_df["tahsilatToplam"].sum())
            if "odemeToplam" in hareket_df.columns:
                vezne_hareket_totals["odemeToplam"] = float(hareket_df["odemeToplam"].sum())
            
            hareket_chart_df = hareket_df.copy()
            if "tahsilatToplam" in hareket_chart_df.columns:
                hareket_chart_df["tahsilatToplam"] = pd.to_numeric(hareket_chart_df["tahsilatToplam"], errors="coerce").fillna(0)
                hareket_chart_df["tahsilat_text"] = hareket_chart_df["tahsilatToplam"].apply(format_tr_money)
            
            fig_vezne_hareket = go.Figure()
            hx_max = 1
            for _, row in hareket_chart_df.iterrows():
                val = float(row.get("tahsilatToplam", 0))
                if val > hx_max: hx_max = val
                fig_vezne_hareket.add_trace(go.Bar(
                    name=str(row["hareketTurAd"]),
                    x=[str(row["hareketTurAd"])],
                    y=[val],
                    text=[str(row["tahsilat_text"])],
                    textposition='outside'
                ))
            fig_vezne_hareket.update_layout(
                template="plotly_dark",
                height=360,
                margin=dict(l=20, r=20, t=55, b=50),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(title="", tickangle=-10),
                yaxis=dict(title="", range=[0, hx_max * 1.2], showgrid=True, gridcolor="rgba(148,163,184,0.18)"),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.15, xanchor="center", x=0.5),
            )

    # Vezne grafikleri
    if not vezne_kasa_df.empty:
        kasa_chart_df = vezne_kasa_df.copy()
        for col in ["tahsilatToplam", "odemeToplam", "kalan", "iptalToplam"]:
            if col in kasa_chart_df.columns:
                kasa_chart_df[col] = kasa_chart_df[col].astype(float)
        kasa_chart_df["kasaAd"] = kasa_chart_df["kasaAd"].astype(str)
        kasa_chart_df = kasa_chart_df.sort_values("kasaAd", ascending=True)

        melted_kasa = kasa_chart_df.melt(id_vars=["kasaAd"], value_vars=["tahsilatToplam", "kalan", "iptalToplam"], var_name="Tur", value_name="Miktar")
        melted_kasa["Miktar"] = pd.to_numeric(melted_kasa["Miktar"], errors="coerce").fillna(0)
        melted_kasa["Tur"] = melted_kasa["Tur"].map({"tahsilatToplam": "Tahsilat", "kalan": "Kalan", "iptalToplam": "İptal"})
        melted_kasa["Miktar_text"] = melted_kasa["Miktar"].apply(format_tr_money)

        custom_colors = {"Tahsilat": "#3b82f6", "Kalan": "#22c55e", "İptal": "#ef4444"}
        
        mx_max = float(melted_kasa["Miktar"].max() if not melted_kasa.empty else 100)
        fig_vezne_kasa = go.Figure()
        unique_kasas = melted_kasa["kasaAd"].unique().tolist()
        
        for tur, color in custom_colors.items():
            df_sub = melted_kasa[melted_kasa["Tur"] == tur]
            y_vals = []
            text_vals = []
            for k in unique_kasas:
                r = df_sub[df_sub["kasaAd"] == k]
                if not r.empty:
                    y_vals.append(float(r.iloc[0]["Miktar"]))
                    text_vals.append(str(r.iloc[0]["Miktar_text"]))
                else:
                    y_vals.append(0.0)
                    text_vals.append("0 ₺")
            
            fig_vezne_kasa.add_trace(go.Bar(
                name=tur,
                x=[str(x) for x in unique_kasas],
                y=y_vals,
                text=text_vals,
                textposition='outside',
                marker_color=color
            ))

        fig_vezne_kasa.update_layout(
            title="",
            template="plotly_dark",
            height=360,
            margin=dict(l=20, r=20, t=55, b=50),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="", tickangle=-10),
            yaxis=dict(title="", range=[0, mx_max * 1.2 if mx_max > 0 else 100], showgrid=True, gridcolor="rgba(148,163,184,0.18)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, title=""),
        )

    if selected_kasa_id_int is not None and not aylik_df.empty:
        aylik_chart_df = aylik_df.copy()
        ax_max = 100
        if "TahsilatToplam" in aylik_chart_df.columns:
            aylik_chart_df["TahsilatToplam"] = pd.to_numeric(aylik_chart_df["TahsilatToplam"], errors="coerce").fillna(0)
            aylik_chart_df["tahsilat_text"] = aylik_chart_df["TahsilatToplam"].apply(format_tr_money)
            ax_max = aylik_chart_df["TahsilatToplam"].max()
        if "Ay" in aylik_chart_df.columns:
            aylik_chart_df["Ay"] = pd.to_numeric(aylik_chart_df["Ay"], errors="coerce").fillna(0).astype(int)
            aylik_chart_df = aylik_chart_df.sort_values("Ay")

        x_list = [str(x) for x in aylik_chart_df["AyAdi"].tolist()] if "AyAdi" in aylik_chart_df.columns else []
        y_list = [float(y) for y in aylik_chart_df["TahsilatToplam"].tolist()] if "TahsilatToplam" in aylik_chart_df.columns else []
        text_list = aylik_chart_df["tahsilat_text"].tolist() if "TahsilatToplam" in aylik_chart_df.columns else []
        
        fig_vezne_aylik = go.Figure()
        fig_vezne_aylik.add_trace(go.Bar(
            name="Tahsilat",
            x=x_list,
            y=y_list,
            text=text_list,
            textposition='outside',
            marker_color="#3b82f6"
        ))

        fig_vezne_aylik.update_layout(
            title="",
            template="plotly_dark",
            height=380,
            margin=dict(l=25, r=20, t=55, b=45),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="", tickangle=0, showgrid=False),
            yaxis=dict(title="", range=[0, ax_max * 1.2 if ax_max > 0 else 100], showgrid=True, gridcolor="rgba(148,163,184,0.18)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0),
        )

    amount_col = GELIR_TUTAR_KOLONU
    t_gelir = float(df[amount_col].sum()) if (not df.empty and amount_col in df.columns) else 0.0
    t_fatura = int(df['FATURA_NO'].nunique()) if not df.empty else 0
    t_kisi = int(df['FATURA_KISI_SAYISI'].sum()) if not df.empty else 0

    charts = {}

    if not df.empty and amount_col in df.columns:
        # Kurum Performansı
        kurum_tur_df = (
            df.groupby('KURUM_TURU')[amount_col]
            .sum()
            .reset_index()
            .sort_values(amount_col, ascending=False)
        )
        kurum_tur_df['tutar_text'] = kurum_tur_df[amount_col].apply(format_tr_money)
        fig_pie = go.Figure(data=[go.Pie(
            labels=kurum_tur_df['KURUM_TURU'].tolist(),
            values=kurum_tur_df[amount_col].tolist(),
            hole=0.6,
            sort=False,
            textinfo='none',
            texttemplate='%{label}<br>%{customdata}',
            textposition='outside',
            customdata=kurum_tur_df['tutar_text'].tolist(),
            hovertemplate='%{label}<br>Net tutar: %{customdata}<extra></extra>',
        )])
        fig_pie.update_layout(
            template='plotly_dark',
            height=460,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            margin=dict(l=50, r=50, t=40, b=40),
            uniformtext_minsize=10,
            uniformtext_mode='hide',
        )

        top_kurum = (
            df.groupby('FATURA_ILGILI')[amount_col]
            .sum()
            .nlargest(10)
            .reset_index()
        )
        fig_bar = px.bar(
            top_kurum.sort_values(amount_col),
            x=amount_col,
            y='FATURA_ILGILI',
            orientation='h',
            color=amount_col,
            color_continuous_scale='Blues',
            labels={amount_col: '', 'FATURA_ILGILI': ''},
        )
        fig_bar.update_traces(texttemplate='%{x:.3s}', textposition='outside', cliponaxis=False)
        fig_bar.update_layout(
            template='plotly_dark',
            height=420,
            margin=dict(l=10, r=60, t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, tickformat='.3s', title=''),
            yaxis=dict(title='', tickfont=dict(size=10)),
            coloraxis_colorbar=dict(title='', tickformat='.2s'),
            showlegend=False,
        )

        # Gelir Trendi — seçilen aralıkta her günün net fatura toplamı (KDV hariç)
        # Not: Eksik günleri 0 ile doldurmuyoruz; tek bir büyük fatura grafigi
        # düz çizgi gibi göstermesin ve alan grafiği görsel olarak dolu kalsın.
        daily = (
            df.groupby(df['FATURA_TARIHI'].dt.date)[amount_col]
            .sum()
            .reset_index()
        )
        daily.columns = ['Tarih', 'Gelir']
        daily['Gelir'] = daily['Gelir'].astype(float)
        daily['gelir_text'] = daily['Gelir'].apply(format_tr_money)

        fig_trend = px.area(
            daily,
            x='Tarih',
            y='Gelir',
            markers=True,
            custom_data=['gelir_text'],
        )
        fig_trend.update_traces(
            line_color='#6366f1',
            fillcolor='rgba(99,102,241,0.25)',
            hovertemplate='Tarih: %{x|%d.%m.%Y}<br>Net gelir (KDV hariç): %{customdata[0]}<extra></extra>',
        )
        fig_trend.update_layout(
            template='plotly_dark',
            height=460,
            margin=dict(l=70, r=20, t=30, b=50),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode='x unified',
            xaxis=dict(
                title='Fatura tarihi',
                tickformat='%d.%m.%Y',
                showgrid=True,
                gridcolor='rgba(148,163,184,0.12)',
            ),
            yaxis=dict(
                title='Net gelir (₺, KDV hariç)',
                showgrid=True,
                gridcolor='rgba(148,163,184,0.12)',
                tickformat=',.0f',
                separatethousands=True,
            ),
        )

        # Fatura Listesi (son 500)
        table_cols = [
            'FATURA_NO',
            'FATURA_TARIHI',
            'FATURA_ILGILI',
            'KURUM_TURU',
            'FATURA_KDVLI_TOPLAM_TUTAR',
            'FATURA_KISI_SAYISI',
            'FATURA_ACIKLAMA',
            'FATURA_TOPLAM_KDV',
            'FATURA_TOPLAM_TUTAR',
        ]
        existing_cols = [c for c in table_cols if c in df.columns]
        table_df = df.sort_values('FATURA_TARIHI', ascending=False)[existing_cols].head(500)
        table_columns = _table_columns_meta(existing_cols)
        table_rows = [
            {col: _format_table_cell(col, row.get(col)) for col in existing_cols}
            for row in table_df.to_dict(orient='records')
        ]

        charts['fig_pie'] = fig_pie.to_html(full_html=False, include_plotlyjs=False)
        charts['fig_bar'] = fig_bar.to_html(full_html=False, include_plotlyjs=False)
        charts['fig_trend'] = fig_trend.to_html(full_html=False, include_plotlyjs=False)
    else:
        existing_cols = []
        table_columns = []
        table_rows = []
    if fig_vezne_kasa is not None:
        charts["fig_vezne_kasa"] = fig_vezne_kasa.to_html(full_html=False, include_plotlyjs=False)
    if fig_vezne_aylik is not None:
        charts["fig_vezne_aylik"] = fig_vezne_aylik.to_html(full_html=False, include_plotlyjs=False)
    if fig_vezne_hareket is not None:
        charts["fig_vezne_hareket"] = fig_vezne_hareket.to_html(full_html=False, include_plotlyjs=False)

    return render_template(
        'gelir.html',
        start_date=sd,
        end_date=ed,
        no_data=(df.empty and vezne_kasa_df.empty),
        t_gelir=t_gelir,
        t_fatura=t_fatura,
        t_kisi=t_kisi,
        charts=charts,
        table_rows=table_rows,
        table_cols=existing_cols,
        table_columns=table_columns,
        t_vezne_gelir=t_vezne_gelir,
        vezne_kasa_rows=vezne_kasa_rows,
        vezne_kasa_totals=vezne_kasa_totals,
        vezne_hareket_rows=vezne_hareket_rows,
        vezne_hareket_totals=vezne_hareket_totals,
        vezne_aylik_rows=vezne_aylik_rows,
        selected_kasa_id=str(selected_kasa_id_int) if selected_kasa_id_int is not None else "",
        page_sql_kodlari=PAGE_SQL_KODLARI,
    )


@gelir_bp.route('/gelir/csv')
@login_required
def gelir_csv():
    """Seçili tarih filtresine göre tüm fatura verisini CSV indirir."""
    sd, ed, df = _load_invoice_df()
    if df.empty:
        return Response('', mimetype='text/csv')

    csv_data = df.to_csv(index=False, encoding='utf-8-sig', sep=';')
    filename = f"fatura_gelir_{sd.strftime('%Y%m%d')}_{ed.strftime('%Y%m%d')}.csv"
    headers = {
        'Content-Disposition': f'attachment; filename={filename}',
        'Content-Type': 'text/csv; charset=utf-8',
    }
    return Response(csv_data, headers=headers)
