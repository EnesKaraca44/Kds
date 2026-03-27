const hekimStats = 1;
const hekimHizmet = 1;
const kurumOrtGelir = 1;

document.getElementById('hekimSelect')?.addEventListener('change', function() {
    const hekim = this.value;
    const kpis = document.getElementById('hekimKpis');
    const tblContainer = document.getElementById('hekimTableContainer');
    
    if(!hekim || !hekimStats[hekim]) {
        kpis.style.display = 'none';
        tblContainer.style.display = 'none';
        document.getElementById('hekimBarChartContainer').style.display = 'none';
        return;
    }
    
    kpis.style.display = 'grid';
    tblContainer.style.display = 'block';
    
    const stats = hekimStats[hekim];
    document.getElementById('kpiGun').innerText = stats.Calisma_Gun + ' Gün';
    document.getElementById('kpiPuan').innerText = new Intl.NumberFormat('tr-TR').format(stats.Toplam_Puan);
    document.getElementById('kpiGelir').innerText = '₺ ' + new Intl.NumberFormat('tr-TR', {minimumFractionDigits:2, maximumFractionDigits:2}).format(stats.Toplam_Gelir);
    
    const avgHekimGelir = 1;
    const kiyasFark = stats.Toplam_Gelir - avgHekimGelir;
    const kiyasYuzde = avgHekimGelir > 0 ? (kiyasFark / avgHekimGelir) * 100 : 0;
    
    document.getElementById('kpiKiyas').innerHTML = `₺ ${new Intl.NumberFormat('tr-TR', {minimumFractionDigits:0}).format(avgHekimGelir)} <br><span style="font-size:14px;color:${kiyasFark>0?'#4ade80':'#f87171'}">${kiyasFark>0?'+':''}${kiyasYuzde.toFixed(1)}%</span>`;
    
    const hData = hekimHizmet[hekim] || [];
    document.getElementById('hekimTableName').innerText = hekim + ' - Hizmet Dağılımı (' + hData.length + ' Kayıt)';
    
    const trace1 = {
        x: [stats.Toplam_Gelir],
        y: [hekim],
        type: 'bar',
        orientation: 'h',
        marker: { color: stats.Toplam_Gelir >= avgHekimGelir ? '#e74c3c' : '#e74c3c' },
        text: ['₺ ' + new Intl.NumberFormat('tr-TR', {minimumFractionDigits:0}).format(stats.Toplam_Gelir)],
        textposition: 'auto',
        hoverinfo: 'none'
    };
    
    const layout = {
        margin: { t: 20, l: 150, r: 20, b: 40 },
        height: 150,
        xaxis: { 
            range: [0, Math.max(stats.Toplam_Gelir, avgHekimGelir) * 1.3],
            showgrid: false,
            zeroline: false
        },
        yaxis: { title: '', fixedrange: true },
        shapes: [
            {
                type: 'line',
                x0: avgHekimGelir,
                y0: -0.5,
                x1: avgHekimGelir,
                y1: 0.5,
                line: { color: 'grey', width: 2, dash: 'dash' }
            }
        ],
        annotations: [
            {
                x: avgHekimGelir,
                y: 0.5,
                xref: 'x',
                yref: 'y',
                text: 'Kurum Ort.',
                showarrow: false,
                yshift: 15
            }
        ],
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)'
    };
    
    if (typeof Plotly !== 'undefined') {
    const tbody = document.querySelector('#hizmetTable tbody');
    let rowsHtml = '';
    
    if (hData && hData.length > 0) {
        hData.forEach(r => {
            let name = r.TETKIK_ADI || '-';
            let cnt = r.TETKIK_ADET || 0;
            let pnt = new Intl.NumberFormat('tr-TR').format(r.TETKIK_TOPLAM_PUAN || 0);
            let gel = '₺ ' + new Intl.NumberFormat('tr-TR', {minimumFractionDigits:2, maximumFractionDigits:2}).format(r.TOPLAM_GELIR || 0);
            rowsHtml += `<tr><td>${name}</td><td>${cnt}</td><td>${pnt}</td><td>${gel}</td></tr>`;
        });
    } else {
        rowsHtml = `<tr><td colspan="4" style="text-align:center;">Tabloda kayıt bulunamadı / Veri yok</td></tr>`;
    }
    
    if($.fn.DataTable.isDataTable('#hizmetTable')) {
        $('#hizmetTable').DataTable().destroy();
    }
    
    tbody.innerHTML = rowsHtml;
    // We will intentionally NOT initialize DataTables here for debugging purposes!
});

$(document).ready(function() {
    $('#detayliListeTable').DataTable({
        language: { url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/tr.json' },
        pageLength: 25
    });
    $('#riskTable').DataTable({
        language: { url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/tr.json' },
        pageLength: 25,
        order: [[1, 'desc']]
    });
    $('#kiyasTable').DataTable({
        language: { url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/tr.json' },
        pageLength: 25,
        order: [[3, 'desc']]
    });
});
