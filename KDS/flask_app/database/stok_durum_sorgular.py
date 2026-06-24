import pandas as pd
import re
from datetime import datetime

from .baglanti import baglanti_olustur
from .cache_helper import ttl_cache
from .malzeme_sorgular import _parse_miad_dates, _safe_read_sql
from .sql_api_client import get_remote_sql


def _fix_stok_durum_sql(sql: str) -> str:
    """
    STOK_DURUM rapor SQL'inde bilinen yazim hatalarini duzeltir.
    Kalici cozum: Rapor API'deki STOK_DURUM sablonunu guncellemek.
    """
    if not isinstance(sql, str) or not sql:
        return sql

    fixed = sql
    # STOK_SEVIYE_JENERIK tablosunda SH_BIRIM_ID yok; dogru kolon BIRIM_ID
    fixed = re.sub(r"\bsvj\.SH_BIRIM_ID\b", "svj.BIRIM_ID", fixed, flags=re.IGNORECASE)
    # JOIN alias tutarsizligi: LEFT JOIN ... sfis ... ama SELECT'te sFis
    fixed = re.sub(r"\bsFis\.", "sfis.", fixed)
    # GROUP BY icinde sh. oneki eksik kolonlar
    fixed = re.sub(
        r"(\bsh\.SH_BATCH_NO,\s*)SH_DOVIZ_KUR,\s*SH_DOVIZ_TOPLAM,\s*SH_DOVIZ_TUR_ID,\s*SH_FIYAT_DVZ",
        r"\1sh.SH_DOVIZ_KUR, sh.SH_DOVIZ_TOPLAM, sh.SH_DOVIZ_TUR_ID, sh.SH_FIYAT_DVZ",
        fixed,
        flags=re.IGNORECASE,
    )
    return fixed


def _normalize_stok_durum_columns(df: pd.DataFrame) -> pd.DataFrame:
    """API/SQL Server kolon adlarini tek forma getirir."""
    if df is None or df.empty:
        return df

    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]

    rename = {}
    for col in list(out.columns):
        key = col.replace(" ", "").lower()
        canonical = {
            "rownumber": "RowNumber",
            "hareketturbelgead": "hareketTurBelgeAd",
            "hareket_tur_belge_ad": "hareketTurBelgeAd",
            "belgead": "hareketTurBelgeAd",
            "hareket_tur_ad": "hareketTurBelgeAd",
            "shstokkod": "shStokKod",
            "stokkodu": "shStokKod",
            "stok_kodu": "shStokKod",
            "shstokad": "shStokAd",
            "stokad": "shStokAd",
            "stok_ad": "shStokAd",
            "shstokaciklama": "shStokAciklama",
            "stokaciklama": "shStokAciklama",
            "sholcubirimad": "shOlcuBirimAd",
            "olcubirimad": "shOlcuBirimAd",
            # birimAd = is yeri adi (BIRIM_AD); olcu birimi degil
            "shmiktar": "shMiktar",
            "girismiktari": "shMiktar",
            "shcikismiktar": "shCikisMiktar",
            "cikismiktari": "shCikisMiktar",
            "shmevcutmiktar": "shMevcutMiktar",
            "mevcutmiktar": "shMevcutMiktar",
            "kritikstokmiktar": "kritikStokMiktar",
            "kritikmiktar": "kritikStokMiktar",
            "minstokmiktar": "minStokMiktar",
            "minimummiktar": "minStokMiktar",
            "maxstokmiktar": "maxStokMiktar",
            "maximummiktar": "maxStokMiktar",
            "yillikstokmiktar": "yillikStokMiktar",
            "yillikmiktar": "yillikStokMiktar",
            "shvadetarih": "shVadeTarih",
            "sonkullanimtarihi": "shVadeTarih",
            "shserilotnumber": "shSeriLotNumber",
            "serilotnumber": "shSeriLotNumber",
            "serilotnumarasi": "shSeriLotNumber",
            "shkunyno": "shKunyeNo",
            "kunyno": "shKunyeNo",
            "shbatchno": "shBatchNo",
            "batchno": "shBatchNo",
        }.get(key)
        if canonical and col != canonical:
            rename[col] = canonical

    if rename:
        out = out.rename(columns=rename)

    if out.columns.duplicated().any():
        out = out.loc[:, ~out.columns.duplicated(keep="first")]

    return out


@ttl_cache(maxsize=32, ttl=60)
def stok_durum_verisi_yukle(start_date_str, end_date_str, birim_id=None, birim_id_list=None):
    """Stok durum listesi — Rapor API (STOK_DURUM)."""
    conn = baglanti_olustur()
    if not conn:
        return pd.DataFrame()

    if birim_id:
        birim_id_param = str(int(birim_id))
    elif birim_id_list:
        birim_id_param = ",".join(str(int(x)) for x in birim_id_list)
    else:
        birim_id_param = ""

    try:
        sql = get_remote_sql(
            "stok_durum.stok_durum_verisi_yukle",
            {
                "start_date": start_date_str,
                "end_date": end_date_str,
                "BIRIM_ID": birim_id_param,
                "TARIH": end_date_str,
            },
        )
        if not sql:
            return pd.DataFrame()

        sql = _fix_stok_durum_sql(sql)

        start_dt = datetime.strptime(f"{start_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(f"{end_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")

        df = _safe_read_sql(
            conn,
            sql,
            [
                (start_dt, end_dt, birim_id_param),
                (start_date_str, end_date_str, birim_id_param),
                (start_dt, end_dt, birim_id_param, birim_id_param),
                (start_date_str, end_date_str, birim_id_param, birim_id_param),
                (start_dt, end_dt),
                (start_date_str, end_date_str),
                (birim_id_param,),
            ],
        )

        df = _normalize_stok_durum_columns(df)

        if not df.empty:
            print(f"[STOK_DURUM] rows={len(df)} cols={list(df.columns)}")
            if "shStokAd" not in df.columns:
                sample = df.iloc[0].to_dict()
                print(f"[STOK_DURUM] UYARI: shStokAd yok — ilk satir ornegi: {sample}")

        if not df.empty and "shVadeTarih" in df.columns:
            df["shVadeTarih"] = _parse_miad_dates(df["shVadeTarih"])

        for col in (
            "shMiktar",
            "shCikisMiktar",
            "shMevcutMiktar",
            "kritikStokMiktar",
            "minStokMiktar",
            "maxStokMiktar",
            "yillikStokMiktar",
        ):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df
    except Exception as e:
        print(f"Stok durum veri yukleme hatasi: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


# Tek bir stok kartinin hareket detayini (alis/satis fiyat, miktar, fis) doner.
# Parametreler: {start_date}, {end_date} (YYYY-MM-DD), {butce} (butce tur id), {stok_id} (STOK_ID)
_STOK_DURUM_DETAY_SQL = """
select row_number() OVER (order by sfTarih asc) as rowNumber, * from
(select   b.BIRIM_AD as birimAd, shTarih, belgeAd, stokHareketTip, hareketEnvanterTip,
 stokKod, stokAd, shOlcuBirimAd, shStokAciklama, shMiktar, shKdvOran, shFiyat, shToplam, shKdvMatrah, shKdvNetTutar,shKdvNetTutarDvz, shCikisMlytTutar, shNetSatisTutar,
sf.STOK_FS_BELGE_NO as sfBelgeNo,
isnull(ck.CARI_KART_ADI, stokAd) as cariKartAdi,
isnull(sf.STOK_FS_FATURA_TARIHI,isnull(sf.STOK_FS_IRSALIYE_TARIHI,sf.STOK_FS_FIS_TARIHI)) as sfTarih,
sf.STOK_FS_FIS_KOD as stokFsFisNo,sf.STOK_FS_FATURA_NO as sfFaturaNo,
kdvsizShFiyat,shKdvDhAd
 from (select sh.STOK_HAREKET_ID as stokHareketId, sh.SH_BIRIM_ID as shBirimId , sh.SH_STOKKART_ID as shStokKartId, sh.SH_BIRIM_TUR_ID as shBirimTurId,
  sh.SH_STOK_FIS_ID as shStokFisId, sh.SH_FATURA_ID as shFaturaId, sh.SH_IRSALIYE_ID as shIrsaliyeId, sh.SH_TARIH as shTarih,sht.HAREKET_TUR_AD as belgeAd,
  sk.STOK_KODU as stokKod, sk.STOK_AD as stokAd, td.TUR_DEGER as shOlcuBirimAd,isnull(sh.SH_STOK_ACIKLAMA, sk.STOK_AD) as shStokAciklama, sh.SH_OZEL_KOD as ozelKod,
  sh.SH_MIKTAR * isnull(sh.SH_BIRIM_CARPAN,1) / 1 as shMiktar, sh.SH_HAREKET_TUR_ID as shHareketTurId, tdSht.TUR_DEGER_KOD as stokHareketTip,
  sh.SH_MIKTAR * isnull(sh.SH_BIRIM_CARPAN,1) / 1 - SUM(CASE WHEN sff.STOK_HAREKET_MIKTAR IS NULL THEN 0 ELSE sff.STOK_HAREKET_MIKTAR / 1 END) AS shMevcutMiktar,
  SUM(CASE WHEN sff.STOK_HAREKET_MIKTAR IS NULL THEN 0 ELSE sff.STOK_HAREKET_MIKTAR / 1 END) AS shCikisMiktar,
   sh.SH_KDV_DH as shKdvDh,case when sh.SH_KDV_DH = 0 then 'Haric' else 'Dahil' end as shKdvDhAd,sh.SH_KDV_ORAN as shKdvOran,
  CASE WHEN sht.HAREKET_ENVANTER_TIP = 1 AND sht.HAREKET_FIS_TIP = 4 THEN (sh.SH_KDV_MATRAH + sh.SH_KDV_NET_TUTAR) / sh.SH_MIKTAR ELSE sh.SH_FIYAT END as shFiyat,
  sh.SH_TOPLAM as shToplam, sh.SH_KDV_MATRAH as shKdvMatrah, sh.SH_KDV_NET_TUTAR as shKdvNetTutar,
  sh.SH_KDV_NET_TUTAR_DVZ as shKdvNetTutarDvz, sh.SH_CIKIS_MLYT_TUTAR as shCikisMlytTutar, sh.SH_NET_SATIS_TUTAR as shNetSatisTutar,
  sh.SH_BIRIM_CARPAN as shBirimCarpan, sh.SH_VADE_TARIH as shVadeTarih, sh.SH_VADE_GUN as shVadeGun, sh.SH_ISLEM_SAAT as shIslemSaat,
  sh.SH_KUNYE_NO as shKunyeNo, sh.SH_BARKOD_NO as shBarkodNo, sh.SH_ACIKLAMA as shAciklama,  sht.HAREKET_ENVANTER_TIP as hareketEnvanterTip,
  isnull(sh.SH_STOK_FIS_ID, isnull(sh.SH_FATURA_ID, sh.SH_IRSALIYE_ID)) as shOrtakFisId, sht.HAREKET_DEVIR_FISI as hareketDevirFisi,
  sg.GRUP_KOD as grupKod, sg.GRUP_AD as grupAd, skt.STOK_KART_TIPI_ID as stokKartTipId, skt.KART_ADI as stokKartTipAd, sht.HAREKET_FIS_TIP as hareketFisTip,
  sh.SH_MKYS_STOK_HAREKET_ID as shMkysStokHareketId, sh.SH_MKYS_STOK_HAREKET_CIKIS_ID as shMkysStokHareketCikisId, sh.SH_MKYS_STOK_HAREKET_DEVIR_ID as shMkysStokHareketDevirId,
  shh.HASTA_AD_SOYAD as hastaAdSoyad,shh.HASTA_SERVIS_AD as servisAd,shh.HASTA_GELIS_ID as hastaGelisNo,shh.HST_YIL as hstYil,shh.HASTA_YATIS_ID as hastaYatisNoStr,sk.TERAPOTIK_ILAC_TUR_ID as terapotikIlacTurId,
  sem.ETKEN_MADDE_GEBELIK as etkenMaddeGebelik,sem.ETKEN_MADDE_EMZIRME as etkenMaddeEmzirme,sk.YUKSEK_RISKLI_ILAC as yuksekRiskliIlac,shh.HASTA_YATIS_TRH as hastaYatisTrh,shh.HASTA_GELIS_TRH as hastaGelisTrh,
  shh.HEKIM_AD_SOYAD as hekimAdSoyad,shh.HASTA_ID as hastaKimlikId,shh.HASTA_SERVIS_ID as hastaServisId,sh.SH_FIYAT as kdvsizShFiyat,
  sh.SH_DOVIZ_KUR as Dvz_Kur,isnull(sh.SH_DOVIZ_TOPLAM,0) as Doviz_Tutar,pr.PARA_BIRIM_KISA_AD as Para_Birim,isnull(sh.SH_FIYAT_DVZ,0) as Doviz_Birim_Fiyat,sk.ILAC_JENERIK_KODU as jenerikKod
from STOK_HAREKET sh
inner join STOK_KART sk with (nolock)
on sk.STOK_ID = sh.SH_STOKKART_ID and sk.STOK_OZELLIK & 1 = 1  and isnull(sk.PSF_ID,0)= 0
inner join TUR_DETAY td with (nolock)
on td.TUR_DETAY_ID = sh.SH_BIRIM_TUR_ID and isnull(td.PSF_ID,0)= 0
inner join STOK_HAREKET_TUR sht with (nolock)
on sh.SH_HAREKET_TUR_ID = sht.STOK_HAREKET_TUR_ID  and isnull(sht.PSF_ID,0)= 0
left join TUR_DETAY tdSht with (nolock)
on tdSht.TUR_DETAY_ID = sht.HAREKET_TIP and isnull(tdSht.PSF_ID,0)=0
left join STOK_FIFO sff with (nolock)
on sff.STOK_HAREKET_GIRIS_ID = sh.STOK_HAREKET_ID and isnull(sff.PSF_ID,0)=0
left join STOK_GRUP sg with (nolock)
on sg.STOK_GRUP_ID = sk.STOK_GRUP_ID and isnull(sg.PSF_ID,0) = 0
left join STOK_KART_TIPI skt with (nolock)
on skt.STOK_KART_TIPI_ID = sk.STOK_TUR_ID and isnull(skt.PSF_ID,0) = 0
left join STOK_HAREKET_HASTA as shh with (nolock)
on shh.STOK_FIS_ID = sh.SH_STOK_FIS_ID and isnull(shh.PSF_ID,0)=0
left join SKRS_ILAC as si with (nolock)
on si.BARKODU =  sk.STOK_BARKOD and isnull(si.PSF_ID,0)=0
left join SBS_ILAC_ETKEN_MADDE as ilacEtken with (nolock)
on ilacEtken.SKRS_ILAC_ID = si.SKRS_ILAC_ID and isnull(ilacEtken.PSF_ID,0)=0
left join SKRS_ETKEN_MADDE as sem with (nolock)
on sem.SKRS_ETKEN_MADDE_ID = ilacEtken.SKRS_ETKEN_MADDE_ID and isnull(sem.PSF_ID,0)=0
left join PARA_BIRIM  pr with (nolock)
on pr.PARA_BIRIM_ID = sh.SH_DOVIZ_TUR_ID and isnull(pr.PSF_ID,0)=0
where isnull(sh.PSF_ID,0)= 0 AND (sh.SH_TARIH >= '{start_date}') AND ( sh.SH_TARIH< DATEADD(day, 1, '{end_date}'))
AND isnull(sht.HAREKET_FIS_TIP,0) <> 2
 AND sht.HAREKET_ENVANTER_TIP IN (1,2,3)
group by sh.STOK_HAREKET_ID, sh.SH_BIRIM_ID, sh.SH_STOKKART_ID, sh.SH_BIRIM_TUR_ID, sh.SH_HAREKET_TUR_ID,
sh.SH_STOK_FIS_ID, sh.SH_FATURA_ID, sh.SH_IRSALIYE_ID, sh.SH_TARIH,sht.HAREKET_TUR_AD,sht.HAREKET_DEVIR_FISI ,
sk.STOK_KODU, sk.STOK_AD, td.TUR_DEGER,isnull(sh.SH_STOK_ACIKLAMA, sk.STOK_AD), sh.SH_OZEL_KOD, sh.SH_MIKTAR, sht.HAREKET_FIS_TIP,
sh.SH_KDV_DH , sh.SH_KDV_ORAN, sh.SH_FIYAT,sh.SH_TOPLAM, sh.SH_KDV_MATRAH, sh.SH_KDV_NET_TUTAR, tdSht.TUR_DEGER_KOD,
sh.SH_KDV_NET_TUTAR_DVZ, sh.SH_CIKIS_MLYT_TUTAR, sh.SH_NET_SATIS_TUTAR, sh.SH_BIRIM_CARPAN, sh.SH_VADE_TARIH, sh.SH_VADE_GUN, sh.SH_ISLEM_SAAT,
sh.SH_KUNYE_NO, sh.SH_BARKOD_NO, sh.SH_ACIKLAMA, isnull(sh.SH_STOK_FIS_ID, isnull(sh.SH_FATURA_ID, sh.SH_IRSALIYE_ID)),
sg.GRUP_KOD , sg.GRUP_AD , skt.STOK_KART_TIPI_ID ,skt.KART_ADI, sh.SH_MKYS_STOK_HAREKET_ID, sh.SH_MKYS_STOK_HAREKET_CIKIS_ID, sh.SH_MKYS_STOK_HAREKET_DEVIR_ID,
sht.HAREKET_ENVANTER_TIP, sht.HAREKET_FIS_TIP,
shh.HASTA_AD_SOYAD,shh.HASTA_SERVIS_AD,shh.HASTA_GELIS_ID,shh.HST_YIL,shh.HASTA_YATIS_ID,sk.TERAPOTIK_ILAC_TUR_ID,sem.ETKEN_MADDE_GEBELIK,sem.ETKEN_MADDE_EMZIRME ,
sk.YUKSEK_RISKLI_ILAC,shh.HASTA_YATIS_TRH,shh.HASTA_GELIS_TRH,shh.HEKIM_AD_SOYAD,shh.HASTA_ID,shh.HASTA_SERVIS_ID,
sh.SH_DOVIZ_KUR ,sh.SH_DOVIZ_TOPLAM ,pr.PARA_BIRIM_KISA_AD,sh.SH_FIYAT_DVZ,sk.ILAC_JENERIK_KODU
) as tmpSh
inner join STOK_FIS sf with (nolock)
on tmpSh.shOrtakFisId = sf.STOK_FS_ID and isnull(sf.PSF_ID,0)=0
AND convert(date,tmpSh.shTarih) = convert(date,isnull(sf.STOK_FS_MAL_KABUL_TARIHI,sf.STOK_FS_BELGE_TARIHI))
left join STOK_SEVIYE sv with (nolock)
on sv.STOK_ID = tmpSh.shStokKartId and sv.SEVIYE_BIRIM_ID = tmpSh.shBirimId  and sv.SEVIYE_BIRIM_TUR_ID = tmpSh.shBirimTurId and sf.STOK_FS_BUTCE_TUR_ID = sv.SEVIYE_BUTCE_TUR_ID and isnull(sv.PSF_ID,0)=0
left join CARI_KART ck with (nolock)
on ck.CARI_KART_ID = sf.STOK_FS_CARI_KART_ID and isnull(ck.PSF_ID,0)=0
left join BIRIM b with (nolock)
on b.BIRIM_ID = sf.STOK_FS_GIRIS_BIRIM_ID and isnull(b.PSF_ID,0)=0
where (isnull(null,0)=0 or (tmpSh.shBirimId = null))
and (isnull({butce},0)=0 or sf.STOK_FS_BUTCE_TUR_ID = {butce})
and (isnull({stok_id},0)=0 or (tmpSh.shStokKartId IN (select Data from dbo.TextToInConditionConvert('{stok_id}',','))))
and (isnull('HAREKETSATINALMA,HAREKETSATIS,HAREKETSTOK,HAREKETECZANE','')='' or (tmpSh.stokHareketTip IN (select Data from dbo.TextToInConditionConvert('HAREKETSATINALMA,HAREKETSATIS,HAREKETSTOK,HAREKETECZANE',','))))
group by stokHareketId, shBirimId, shStokKartId, shBirimTurId, shHareketTurId,shStokFisId, shFaturaId, shIrsaliyeId, shTarih, belgeAd, stokHareketTip, b.BIRIM_AD, hareketFisTip,
       stokKod, stokAd, shOlcuBirimAd, shStokAciklama, ozelKod, shMiktar, shMevcutMiktar,shCikisMiktar, shKdvDh, shKdvOran, shFiyat, shToplam, shKdvMatrah, shKdvNetTutar,
       shKdvNetTutarDvz, shCikisMlytTutar, shNetSatisTutar, shBirimCarpan, shVadeTarih, shVadeGun, shIslemSaat, sf.STOK_FS_FATURA_NO,sf.STOK_FS_BELGE_NO ,
shKunyeNo, shBarkodNo, shAciklama, shOrtakFisId, grupKod, grupAd, stokKartTipId,stokKartTipAd, sf.STOK_FS_IRSALIYE_TARIHI,sf.STOK_FS_FIS_TARIHI, sf.STOK_FS_TOPLAM_INDIRIM,
       shMkysStokHareketId, shMkysStokHareketCikisId, shMkysStokHareketDevirId, sf.STOK_FS_BUTCE_TUR_ID , sf.STOK_FS_IRSALIYE_NO, hareketEnvanterTip, hareketDevirFisi,
       sv.STOK_SEVIYE_KRITIK, sv.STOK_SEVIYE_ASGARI ,sv.STOK_SEVIYE_AZAMI, sv.STOK_SEVIYE_YILLIK,ck.CARI_KART_KODU,ck.CARI_KART_ADI,sf.STOK_FS_FATURA_TARIHI,
       sf.STOK_FS_IHALE_NO, sf.STOK_FS_IHALE_TARIHI,hastaAdSoyad,servisAd,hastaGelisNo,hstYil,hastaYatisNoStr,terapotikIlacTurId,etkenMaddeGebelik,etkenMaddeEmzirme,yuksekRiskliIlac,
       hastaYatisTrh,hastaGelisTrh,hekimAdSoyad,hastaKimlikId,hastaServisId,sf.STOK_FS_DAYANAK_NO,sf.STOK_FS_FIS_KOD,sf.STOK_FS_ISLEM_YAPAN_KIMLIK_ID,
       sf.STOK_FS_IHALE_NO,sf.STOK_FS_IHALE_TARIHI,kdvsizShFiyat,shKdvDhAd,
       Dvz_Kur, Doviz_Tutar,Para_Birim,Doviz_Birim_Fiyat
having (isnull(null,0) =0 or isnull(null,0) =0 or (dbo.numericConditionCheck(sum(convert(decimal(27,13),shMevcutMiktar)), null,null) = 1))
) as durumCount
"""


def _detay_satir_tipi(hareket_tip, envanter_tip, belge_ad) -> str:
    """
    Alis/satis/diger ayrimi:
    1) stokHareketTip kodu (HAREKETSATINALMA / HAREKETSATIS) en guvenilir.
    2) hareketEnvanterTip (1=giris->alis, 2=cikis->satis).
    3) Son care: belge adindan kelime eslesmesi.
    """
    kod = str(hareket_tip or "").strip().upper()
    if "SATINALMA" in kod or "ECZANE" in kod or "GIRIS" in kod:
        return "alis"
    if "SATIS" in kod or "CIKIS" in kod:
        return "satis"

    try:
        et = int(float(envanter_tip))
    except (TypeError, ValueError):
        et = 0
    if et == 1:
        return "alis"
    if et == 2:
        return "satis"

    low = str(belge_ad or "").lower()
    if "satinal" in low or "sat\u0131nal" in low or "al\u0131\u015f" in low or "alis" in low or "giri\u015f" in low or "giris" in low:
        return "alis"
    if "sat\u0131\u015f" in low or "satis" in low or "\u00e7\u0131k\u0131\u015f" in low or "cikis" in low:
        return "satis"
    return "diger"


def _detay_num(val) -> float:
    num = pd.to_numeric(val, errors="coerce")
    return float(num) if pd.notna(num) else 0.0


def _detay_tarih(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    if hasattr(val, "strftime"):
        try:
            return val.strftime("%d.%m.%Y")
        except (ValueError, OSError):
            return ""
    return str(val).strip()


@ttl_cache(maxsize=128, ttl=60)
def stok_durum_detay_yukle(stok_kart_id, start_date_str, end_date_str, butce_tur_id=831):
    """Tek bir stok kartinin hareket detayini doner: ozet + satirlar."""
    bos = {"ozet": {}, "satirlar": [], "count": 0}

    try:
        sid = int(float(str(stok_kart_id).strip()))
    except (TypeError, ValueError):
        return bos
    if sid <= 0:
        return bos

    try:
        butce = int(butce_tur_id)
    except (TypeError, ValueError):
        butce = 0

    conn = baglanti_olustur()
    if not conn:
        return bos

    try:
        sql = _STOK_DURUM_DETAY_SQL.format(
            start_date=start_date_str,
            end_date=end_date_str,
            butce=butce,
            stok_id=sid,
        )
        df = pd.read_sql(sql, conn)
        df = _normalize_stok_durum_columns(df)

        print(f"[STOK_DURUM_DETAY] stok_id={sid} rows={len(df)}")
        if df is not None and not df.empty:
            tipler = df["stokHareketTip"].dropna().unique().tolist() if "stokHareketTip" in df.columns else "-"
            envanter = df["hareketEnvanterTip"].dropna().unique().tolist() if "hareketEnvanterTip" in df.columns else "-"
            print(f"[STOK_DURUM_DETAY] stokHareketTip={tipler} hareketEnvanterTip={envanter}")

        if df is None or df.empty:
            return bos

        # SQL rowNumber = sfTarih asc (en eski once). Once eski->yeni siralayalim
        # ki son alis/satis dogru hesaplansin, sonra gosterim icin ters cevirelim.
        if "RowNumber" in df.columns:
            df = (
                df.assign(_rn=pd.to_numeric(df["RowNumber"], errors="coerce"))
                .sort_values("_rn", kind="stable")
                .drop(columns="_rn")
            )

        satirlar = []
        for _, row in df.iterrows():
            belge = str(row.get("belgeAd") or "").strip()
            satirlar.append(
                {
                    "tarih": _detay_tarih(row.get("sfTarih")) or _detay_tarih(row.get("shTarih")),
                    "belge": belge,
                    "tip": _detay_satir_tipi(
                        row.get("stokHareketTip"),
                        row.get("hareketEnvanterTip"),
                        belge,
                    ),
                    "cari": str(row.get("cariKartAdi") or "").strip(),
                    "birim": str(row.get("shOlcuBirimAd") or "").strip(),
                    "miktar": _detay_num(row.get("shMiktar")),
                    "fiyat": _detay_num(row.get("shFiyat")),
                    "kdvsiz_fiyat": _detay_num(row.get("kdvsizShFiyat")),
                    "kdv_oran": _detay_num(row.get("shKdvOran")),
                    "toplam": _detay_num(row.get("shToplam")),
                    "net_tutar": _detay_num(row.get("shKdvNetTutar")),
                    "belge_no": str(row.get("sfBelgeNo") or row.get("sfFaturaNo") or "").strip(),
                }
            )

        son_alis = next((s for s in reversed(satirlar) if s["tip"] == "alis"), None)
        son_satis = next((s for s in reversed(satirlar) if s["tip"] == "satis"), None)
        ilk = df.iloc[0]

        # Gosterimde en son islem en ustte olsun (yeni -> eski).
        satirlar.reverse()

        ozet = {
            "stok_kod": str(ilk.get("stokKod") or "").strip(),
            "stok_ad": str(ilk.get("stokAd") or "").strip(),
            "birim": str(ilk.get("shOlcuBirimAd") or "").strip(),
            "toplam_hareket": len(satirlar),
            "son_alis_fiyat": son_alis["fiyat"] if son_alis else None,
            "son_alis_tarih": son_alis["tarih"] if son_alis else "",
            "son_alis_cari": son_alis["cari"] if son_alis else "",
            "son_satis_fiyat": son_satis["fiyat"] if son_satis else None,
            "son_satis_tarih": son_satis["tarih"] if son_satis else "",
        }

        return {"ozet": ozet, "satirlar": satirlar, "count": len(satirlar)}
    except Exception as e:
        print(f"Stok durum detay yukleme hatasi: {e}")
        return bos
    finally:
        conn.close()
