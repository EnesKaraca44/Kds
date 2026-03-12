from flask import Blueprint, render_template, request
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from database.sevk_sorgular import sevk_verisi_yukle
from routes.dashboard import get_date_range

sevk_bp = Blueprint('sevk', __name__)


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


@sevk_bp.route('/sevk')
@login_required
def sevk():
    sd, ed = get_date_range()
    df_referrals = sevk_verisi_yukle(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))

    if df_referrals is None or df_referrals.empty:
        return render_template('sevk.html', start_date=sd, end_date=ed, no_data=True)

    df = df_referrals.copy()

    COL_EDEN_DR = 'Sevk_Eden_Doktor_Ad'
    COL_KABUL_DR = 'Sevk_Kabul_Doktor_Ad'
    COL_EDEN_SRV = 'Sevk_Eden_Srv_Ad'
    COL_KABUL_SRV = 'Sevk_Kabul_Srv_Ad'
    COL_HASTA = 'TOPLAM_HASTA'
    COL_SEVK = 'TOPLAM_SEVK'

    import numpy as np, sys

    hasta_map = df.groupby('DOKTOR_ADI')[COL_HASTA].max().to_dict()

    eden_sevk = df.groupby(COL_EDEN_DR)[COL_SEVK].sum().reset_index()
    eden_sevk[COL_HASTA] = (
        eden_sevk[COL_EDEN_DR]
        .map(hasta_map)
        .fillna(0)
        .astype(float)
    )
    eden_sevk[COL_SEVK] = eden_sevk[COL_SEVK].astype(float)
    oran_df = eden_sevk.copy()

    oran_df['ORAN'] = np.where(
        oran_df[COL_HASTA] > 0,
        (oran_df[COL_SEVK] / oran_df[COL_HASTA] * 100.0),
        0.0,
    )
    oran_df['ORAN'] = oran_df['ORAN'].replace([np.inf, -np.inf], 0.0).fillna(0.0).astype(float)

    print(f"[SEVK] oran_df rows={len(oran_df)}, hasta>0={int((oran_df[COL_HASTA]>0).sum())}, oran>0={int((oran_df['ORAN']>0).sum())}", flush=True, file=sys.stderr)
    print(f"[SEVK] oran_df sample:\n{oran_df.head(10).to_string()}", flush=True, file=sys.stderr)

    total_h = int(oran_df[COL_HASTA].sum())
    total_s = int(df[COL_SEVK].sum())
    genel_ort = (total_s / total_h * 100.0) if total_h > 0 else 0.0
    aktif_hekim = int(oran_df[COL_EDEN_DR].nunique())

    try:
        top_n = int(request.args.get('top', 10))
    except (TypeError, ValueError):
        top_n = 10
    top_n = max(5, min(30, (top_n // 5) * 5))

    top_eden = (
        df.groupby(COL_EDEN_DR)[COL_SEVK]
        .sum()
        .nlargest(top_n)
        .reset_index()
    )
    fig_eden = px.bar(
        top_eden.sort_values(COL_SEVK),
        x=COL_SEVK,
        y=COL_EDEN_DR,
        orientation='h',
        color=COL_SEVK,
        color_continuous_scale='Purples',
        labels={COL_SEVK: 'TOPLAM_SEVK', COL_EDEN_DR: ''},
    )
    fig_eden.update_traces(texttemplate='%{x:.3s}', textposition='outside', cliponaxis=False)
    fig_eden.update_layout(
        template='plotly_dark',
        height=420,
        margin=dict(l=10, r=60, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickformat='.3s', title=''),
        yaxis=dict(title='', tickfont=dict(size=10)),
        showlegend=False,
    )

    top_kabul = (
        df.groupby(COL_KABUL_DR)[COL_SEVK]
        .sum()
        .nlargest(top_n)
        .reset_index()
    )
    fig_kabul = px.bar(
        top_kabul.sort_values(COL_SEVK),
        x=COL_SEVK,
        y=COL_KABUL_DR,
        orientation='h',
        color=COL_SEVK,
        color_continuous_scale='Blues',
        labels={COL_SEVK: 'TOPLAM_SEVK', COL_KABUL_DR: ''},
    )
    fig_kabul.update_traces(texttemplate='%{x:.3s}', textposition='outside', cliponaxis=False)
    fig_kabul.update_layout(
        template='plotly_dark',
        height=420,
        margin=dict(l=10, r=60, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickformat='.3s', title=''),
        yaxis=dict(title='', tickfont=dict(size=10)),
        showlegend=False,
    )

    # Scatter için sadece sevk adedi > 0 olan hekimleri al
    # (TOPLAM_HASTA 0 olsa bile nokta çizilsin; kısa dönem filtrelerde hasta=0 sık görülüyor)
    oran_scatter = oran_df[oran_df[COL_SEVK] > 0].copy()
    print(
        f"[SEVK] scatter rows={len(oran_scatter)}, "
        f"min_hasta={oran_scatter[COL_HASTA].min() if not oran_scatter.empty else '-'}, "
        f"min_sevk={oran_scatter[COL_SEVK].min() if not oran_scatter.empty else '-'}",
        flush=True,
        file=sys.stderr,
    )

    # Boyutu dinamik yapmak bazı ortamlarda balonların görünmemesine yol açabiliyor.
    # Daha stabil olması için sabit marker boyutu, rengi ORAN'a göre yaptık.
    fig_oran = px.scatter(
        oran_scatter,
        x=COL_HASTA,
        y=COL_SEVK,
        color='ORAN',
        hover_name=COL_EDEN_DR,
        color_continuous_scale='Plasma',
        labels={COL_HASTA: 'TOPLAM_HASTA', COL_SEVK: 'TOPLAM_SEVK', 'ORAN': 'ORAN'},
    )
    fig_oran.update_traces(
        marker=dict(size=14, opacity=0.85),
        hovertemplate="<b>%{hovertext}</b><br>"
        "TOPLAM_HASTA=%{x:.0f}<br>"
        "TOPLAM_SEVK=%{y:.0f}<br>"
        "ORAN=%{marker.color:.1f}<extra></extra>",
    )
    fig_oran.update_layout(
        template='plotly_dark',
        height=420,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title='TOPLAM_HASTA', tickformat='.3s'),
        yaxis=dict(title='TOPLAM_SEVK', tickformat='.3s'),
        coloraxis_colorbar=dict(title='ORAN', tickformat='.1f'),
    )

    oran_table = (
        oran_df[[COL_EDEN_DR, COL_HASTA, COL_SEVK, 'ORAN']]
        .sort_values('ORAN', ascending=False)
        .to_dict(orient='records')
    )
    oran_table_ui = []
    max_oran = max(_safe_float(oran_df['ORAN'].max()), 1.0) if not oran_df.empty else 1.0
    for row in (
        oran_df[[COL_EDEN_DR, COL_HASTA, COL_SEVK, 'ORAN']]
        .sort_values('ORAN', ascending=False)
        .head(30)
        .to_dict(orient='records')
    ):
        oran = _safe_float(row['ORAN'])
        if oran >= 100:
            seviye = 'high'
            yorum = 'Cok yuksek'
        elif oran >= 50:
            seviye = 'medium'
            yorum = 'Yuksek'
        else:
            seviye = 'low'
            yorum = 'Normal'
        oran_table_ui.append({
            'hekim': row[COL_EDEN_DR],
            'hasta': int(_safe_float(row[COL_HASTA])),
            'sevk': int(_safe_float(row[COL_SEVK])),
            'oran': round(oran, 1),
            'bar_width': max(6, min(int((oran / max_oran) * 100), 100)),
            'seviye': seviye,
            'yorum': yorum,
        })

    brans_flow = (
        df.groupby([COL_EDEN_SRV, COL_KABUL_SRV])[COL_SEVK]
        .sum()
        .reset_index()
    )
    top_k_br = (
        brans_flow.groupby(COL_KABUL_SRV)[COL_SEVK]
        .sum()
        .idxmax()
        if not brans_flow.empty
        else ''
    )
    top_e_br = (
        brans_flow.groupby(COL_EDEN_SRV)[COL_SEVK]
        .sum()
        .idxmax()
        if not brans_flow.empty
        else ''
    )

    fig_brans = px.bar(
        brans_flow.nlargest(15, COL_SEVK),
        x=COL_EDEN_SRV,
        y=COL_SEVK,
        color=COL_KABUL_SRV,
        barmode='stack',
        labels={COL_EDEN_SRV: 'Kaynak Servis', COL_SEVK: 'Sevk Adedi', COL_KABUL_SRV: 'Hedef Servis'},
    )
    fig_brans.update_layout(
        template='plotly_dark',
        height=420,
        margin=dict(l=20, r=20, t=30, b=90),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_tickangle=-45,
    )

    brans_top10 = (
        brans_flow.nlargest(10, COL_SEVK)
        .rename(columns={COL_EDEN_SRV: 'Kaynak', COL_KABUL_SRV: 'Hedef', COL_SEVK: 'Adet'})
        .to_dict(orient='records')
    )

    dr_brans_map = (
        df.groupby([COL_EDEN_DR, COL_KABUL_SRV])[COL_SEVK]
        .sum()
        .reset_index()
    )
    all_drs = sorted(dr_brans_map[COL_EDEN_DR].dropna().unique())
    selected_drs_param = request.args.get('drs', '')
    selected_drs = [d for d in selected_drs_param.split(',') if d] or all_drs[:10]

    filtered_map = dr_brans_map[dr_brans_map[COL_EDEN_DR].isin(selected_drs)]
    fig_drs_map = px.bar(
        filtered_map,
        x=COL_EDEN_DR,
        y=COL_SEVK,
        color=COL_KABUL_SRV,
        barmode='stack',
        labels={COL_EDEN_DR: 'Hekim', COL_SEVK: 'Sevk Adedi', COL_KABUL_SRV: 'Hedef Branş'},
    )
    fig_drs_map.update_layout(
        template='plotly_dark',
        height=420,
        margin=dict(l=20, r=20, t=30, b=100),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_tickangle=-45,
    )

    fav_brans = (
        filtered_map.sort_values([COL_EDEN_DR, COL_SEVK], ascending=[True, False])
        .groupby(COL_EDEN_DR)
        .head(1)
        .rename(columns={COL_EDEN_DR: 'Hekim', COL_KABUL_SRV: 'EnCokSevkBrans', COL_SEVK: 'Adet'})
        .to_dict(orient='records')
    )

    df_pair = df.dropna(subset=[COL_EDEN_DR, COL_KABUL_DR]).groupby([COL_EDEN_DR, COL_KABUL_DR])[COL_SEVK].sum().reset_index()
    df_pair['KANAL'] = df_pair[COL_EDEN_DR] + ' → ' + df_pair[COL_KABUL_DR]
    fig_pair = px.bar(
        df_pair.nlargest(15, COL_SEVK).sort_values(COL_SEVK),
        x=COL_SEVK,
        y='KANAL',
        orientation='h',
        labels={COL_SEVK: 'Toplam Sevk', 'KANAL': ''},
        color_discrete_sequence=['#6366f1'],
    )
    fig_pair.update_traces(texttemplate='%{x:.3s}', textposition='outside', cliponaxis=False)
    fig_pair.update_layout(
        template='plotly_dark',
        height=420,
        margin=dict(l=10, r=60, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickformat='.3s', title=''),
        yaxis=dict(title='', tickfont=dict(size=10)),
    )

    hekim_list = sorted(df[COL_EDEN_DR].dropna().unique())
    selected_dr = request.args.get('dr') or (hekim_list[0] if hekim_list else '')
    detail_metrics = None
    detail_pie_html = ''
    detail_bars_html = ''
    detail_accept_table = []

    if selected_dr:
        dr_data = df[df[COL_EDEN_DR] == selected_dr]
        out_refs = dr_data.groupby(COL_KABUL_DR)[COL_SEVK].sum().reset_index()
        if not out_refs.empty:
            total_out = int(out_refs[COL_SEVK].sum())
            hastasi = int(dr_data[COL_HASTA].max()) if COL_HASTA in dr_data.columns else 0
            orani = (total_out / hastasi * 100.0) if hastasi > 0 else 0.0
            detail_metrics = {
                'hasta': hastasi,
                'sevk': total_out,
                'oran': orani,
                'fark': orani - genel_ort,
            }

            fig_out = px.pie(out_refs, values=COL_SEVK, names=COL_KABUL_DR, hole=0.45)
            fig_out.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=380,
            )
            detail_pie_html = fig_out.to_html(full_html=False, include_plotlyjs=False)

            dr_brans = dr_data.groupby(COL_KABUL_SRV)[COL_SEVK].sum().reset_index()
            fig_hb = px.bar(
                dr_brans.sort_values(COL_SEVK),
                x=COL_SEVK,
                y=COL_KABUL_SRV,
                orientation='h',
                labels={COL_SEVK: 'Sevk Adedi', COL_KABUL_SRV: ''},
            )
            fig_hb.update_layout(
                template='plotly_dark',
                height=380,
                margin=dict(l=10, r=40, t=10, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
            )
            detail_bars_html = fig_hb.to_html(full_html=False, include_plotlyjs=False)

            detail_accept_table = (
                out_refs.sort_values(COL_SEVK, ascending=False)
                .rename(columns={COL_KABUL_DR: 'Hekim', COL_SEVK: 'Adet'})
                .to_dict(orient='records')
            )

    raw_cols = list(df.columns)
    raw_rows = df.head(500).to_dict(orient='records')

    _cfg = {'responsive': True}
    charts = {
        'fig_eden': fig_eden.to_html(full_html=False, include_plotlyjs=False, config=_cfg),
        'fig_kabul': fig_kabul.to_html(full_html=False, include_plotlyjs=False, config=_cfg),
        'fig_oran': fig_oran.to_html(full_html=False, include_plotlyjs=False, config=_cfg),
        'fig_brans': fig_brans.to_html(full_html=False, include_plotlyjs=False, config=_cfg),
        'fig_drs_map': fig_drs_map.to_html(full_html=False, include_plotlyjs=False, config=_cfg),
        'fig_pair': fig_pair.to_html(full_html=False, include_plotlyjs=False, config=_cfg),
        'detail_pie': detail_pie_html,
        'detail_bars': detail_bars_html,
    }

    return render_template(
        'sevk.html',
        start_date=sd,
        end_date=ed,
        no_data=False,
        total_h=total_h,
        total_s=total_s,
        genel_ort=genel_ort,
        aktif_hekim=aktif_hekim,
        top_n=top_n,
        charts=charts,
        oran_table=oran_table,
        oran_table_ui=oran_table_ui,
        brans_top10=brans_top10,
        top_k_br=top_k_br,
        top_e_br=top_e_br,
        all_drs=all_drs,
        selected_drs=selected_drs,
        fav_brans=fav_brans,
        hekim_list=hekim_list,
        selected_dr=selected_dr,
        detail_metrics=detail_metrics,
        detail_accept_table=detail_accept_table,
        raw_cols=raw_cols,
        raw_rows=raw_rows,
    )
