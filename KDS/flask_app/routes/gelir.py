from flask import Blueprint, render_template, request, Response
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from database.fatura_sorgular import fatura_gelir_verisi_yukle
from routes.dashboard import get_date_range

gelir_bp = Blueprint('gelir', __name__)


def _load_invoice_df():
    """Seçili tarih aralığına göre fatura verisini döndürür."""
    sd, ed = get_date_range()
    df = fatura_gelir_verisi_yukle(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))
    if df.empty:
        return sd, ed, df

    df = df.copy()
    df.columns = [c.upper().strip() for c in df.columns]
    df['FATURA_TARIHI'] = pd.to_datetime(df['FATURA_TARIHI'], errors='coerce')
    return sd, ed, df


@gelir_bp.route('/gelir')
@login_required
def gelir():
    sd, ed, df = _load_invoice_df()

    if df.empty:
        return render_template('gelir.html', start_date=sd, end_date=ed, no_data=True)

    t_gelir_kdvli = float(df['FATURA_KDVLI_TOPLAM_TUTAR'].sum())
    t_gelir_net = float(df['FATURA_TOPLAM_TUTAR'].sum())
    t_fatura = int(df['FATURA_NO'].nunique())
    t_kisi = int(df['FATURA_KISI_SAYISI'].sum())

    # Kurum Performansı
    kurum_tur_df = (
        df.groupby('KURUM_TURU')['FATURA_KDVLI_TOPLAM_TUTAR']
        .sum()
        .reset_index()
        .sort_values('FATURA_KDVLI_TOPLAM_TUTAR', ascending=False)
    )
    fig_pie = px.pie(
        kurum_tur_df,
        values='FATURA_KDVLI_TOPLAM_TUTAR',
        names='KURUM_TURU',
        hole=0.6,
    )
    fig_pie.update_traces(textinfo='percent+label')
    fig_pie.update_layout(
        template='plotly_dark',
        height=420,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
    )

    top_kurum = (
        df.groupby('FATURA_ILGILI')['FATURA_KDVLI_TOPLAM_TUTAR']
        .sum()
        .nlargest(10)
        .reset_index()
    )
    fig_bar = px.bar(
        top_kurum.sort_values('FATURA_KDVLI_TOPLAM_TUTAR'),
        x='FATURA_KDVLI_TOPLAM_TUTAR',
        y='FATURA_ILGILI',
        orientation='h',
        color='FATURA_KDVLI_TOPLAM_TUTAR',
        color_continuous_scale='Blues',
        labels={'FATURA_KDVLI_TOPLAM_TUTAR': 'Fatura KDVli Toplam Tutar', 'FATURA_ILGILI': ''},
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
        coloraxis_colorbar=dict(title='Tutar', tickformat='.2s'),
        showlegend=False,
    )

    # Gelir Trendi
    daily = (
        df.groupby(df['FATURA_TARIHI'].dt.date)['FATURA_KDVLI_TOPLAM_TUTAR']
        .sum()
        .reset_index()
    )
    daily.columns = ['Tarih', 'Gelir']
    fig_trend = px.area(
        daily,
        x='Tarih',
        y='Gelir',
        markers=True,
    )
    fig_trend.update_traces(line_color='#6366f1', fillcolor='rgba(99,102,241,0.25)')
    fig_trend.update_layout(
        template='plotly_dark',
        height=460,
        margin=dict(l=20, r=20, t=30, b=30),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title='Tarih',
        yaxis_title='Gelir',
        yaxis=dict(tickformat='.3s'),
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
    table_rows = table_df.to_dict(orient='records')

    charts = {
        'fig_pie': fig_pie.to_html(full_html=False, include_plotlyjs=False),
        'fig_bar': fig_bar.to_html(full_html=False, include_plotlyjs=False),
        'fig_trend': fig_trend.to_html(full_html=False, include_plotlyjs=False),
    }

    return render_template(
        'gelir.html',
        start_date=sd,
        end_date=ed,
        no_data=False,
        t_gelir_kdvli=t_gelir_kdvli,
        t_gelir_net=t_gelir_net,
        t_fatura=t_fatura,
        t_kisi=t_kisi,
        charts=charts,
        table_rows=table_rows,
        table_cols=existing_cols,
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
