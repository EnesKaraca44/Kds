from flask import Blueprint, render_template
import plotly.graph_objects as go
import sys, os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login_required
from routes.dashboard import get_date_range
from database.personel_sorgular import (
    get_personel_calisma_durumu_ozet,
    get_personel_kadro_unvan_ozet,
    get_personel_tur_ozet,
    get_personel_hizmet_sinif_ozet,
    get_personel_tam_liste
)

personel_sorgulama_bp = Blueprint('personel_sorgulama', __name__)


def _bar_chart(data, title, colors=None):
    """Verilen veri listesinden Plotly bar grafiği üretir."""
    if not data:
        return ""
        
    # Sort data by 'toplam' descending for better bar chart UX
    sorted_data = sorted(data, key=lambda x: x['toplam'], reverse=False)
    
    labels = [d['tur'] for d in sorted_data]
    values = [d['toplam'] for d in sorted_data]

    if colors is None:
        colors = [
            '#3b82f6', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444',
            '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#6366f1',
            '#84cc16', '#06b6d4', '#d946ef', '#0891b2', '#e11d48',
            '#059669', '#7c3aed', '#db2777', '#0d9488', '#ea580c',
        ]
        
    fig = go.Figure(data=[go.Bar(
        x=values,
        y=labels,
        orientation='h',
        marker=dict(
            color=colors[:len(labels)] if len(colors) >= len(labels) else '#3b82f6',
            line=dict(color='rgba(255,255,255,0.2)', width=1)
        ),
        text=values,
        textposition='outside',
        textfont=dict(family='Inter', size=12, color='#334155'),
        hovertemplate='<b>%{y}</b><br>Sayı: %{x}<extra></extra>'
    )])

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, family='Inter', color='#64748b')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color='#334155'),
        xaxis=dict(gridcolor='rgba(0,0,0,0.05)', title='Kişi Sayısı'),
        yaxis=dict(gridcolor='rgba(0,0,0,0)'),
        margin=dict(t=40, b=40, l=150, r=20),
        height=max(300, len(labels) * 30), # Dinamik yükseklik
        showlegend=False
    )

    return fig.to_html(full_html=False, include_plotlyjs=False)


@personel_sorgulama_bp.route('/personel-sorgulama')
@login_required
def personel_sorgulama():
    sd, ed = get_date_range()
    sd_str = sd.strftime('%Y-%m-%d')
    ed_str = ed.strftime('%Y-%m-%d')

    # 1. Çalışma Durumu
    df_calisma_ozet = get_personel_calisma_durumu_ozet(sd_str, ed_str)
    calisma_durumu = df_calisma_ozet.rename(columns={'data1': 'tur', 'data2': 'toplam'}).to_dict(orient='records')
    
    # 2. Kadro Unvan
    df_kadro_ozet = get_personel_kadro_unvan_ozet(sd_str, ed_str)
    kadro_unvan = df_kadro_ozet.rename(columns={'data1': 'tur', 'data2': 'toplam'}).to_dict(orient='records')
    
    # 3. Personel Türü
    df_tur_ozet = get_personel_tur_ozet(sd_str, ed_str)
    personel_tur = df_tur_ozet.rename(columns={'data1': 'tur', 'data2': 'toplam'}).to_dict(orient='records')
    
    # 4. Hizmet Sınıfı
    df_hizmet_ozet = get_personel_hizmet_sinif_ozet(sd_str, ed_str)
    hizmet_sinifi = df_hizmet_ozet.rename(columns={'data1': 'tur', 'data2': 'toplam'}).to_dict(orient='records')

    # 5. Master Personel Listesi
    df_personel_listesi = get_personel_tam_liste(sd_str, ed_str)
    personel_listesi = df_personel_listesi.rename(columns={
        'data1': 'ad', 
        'data3': 'kurum', 
        'data4': 'unvan',
    }).to_dict(orient='records')

    # KPI Değerleri
    toplam_personel = sum(d['toplam'] for d in calisma_durumu)
    toplam_unvan = len(kadro_unvan)
    toplam_tur = len(personel_tur)
    toplam_sinif = len(hizmet_sinifi)
    calisan = next((d['toplam'] for d in calisma_durumu if d['tur'] == 'ÇALIŞIYOR'), 0)
    izinli = next((d['toplam'] for d in calisma_durumu if d['tur'] == 'İZİNLİ'), 0)
    raporlu = next((d['toplam'] for d in calisma_durumu if d['tur'] == 'RAPORLU'), 0)

    # Grafikler
    chart_calisma = _bar_chart(calisma_durumu, 'Çalışma Durumu Dağılımı', ['#10b981', '#f59e0b', '#ef4444', '#3b82f6'])
    chart_kadro = _bar_chart(kadro_unvan, 'Kadro Unvan Dağılımı')
    chart_personel_tur = _bar_chart(personel_tur, 'Personel Türü Dağılımı', ['#2563eb', '#8b5cf6', '#14b8a6', '#f59e0b', '#ef4444'])
    chart_hizmet = _bar_chart(hizmet_sinifi, 'Hizmet Sınıfı Dağılımı', ['#2563eb', '#0ea5e9', '#f59e0b', '#10b981', '#8b5cf6', '#ef4444'])

    return render_template('personel_sorgulama.html',
        start_date=sd,
        end_date=ed,
        toplam_personel=toplam_personel,
        toplam_unvan=toplam_unvan,
        toplam_tur=toplam_tur,
        toplam_sinif=toplam_sinif,
        calisan=calisan,
        izinli=izinli,
        raporlu=raporlu,
        calisma_durumu=calisma_durumu,
        kadro_unvan=kadro_unvan,
        personel_tur=personel_tur,
        hizmet_sinifi=hizmet_sinifi,
        chart_calisma=chart_calisma,
        chart_kadro=chart_kadro,
        chart_personel_tur=chart_personel_tur,
        chart_hizmet=chart_hizmet,
        personel_listesi=personel_listesi
    )
