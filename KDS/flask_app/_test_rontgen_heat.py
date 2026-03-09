import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.xray_loaders import load_xray_analysis_data
import pandas as pd


def _find_column(candidates, df_cols):
    for cand in candidates:
        clean = cand.upper().strip()
        for col in df_cols:
            cu = str(col).upper()
            if clean == cu.replace("_", " ").strip() or clean == cu.strip():
                return col
    return None


def main():
    sd = "2025-01-01"
    ed = "2025-12-31"
    df = load_xray_analysis_data(sd, ed)
    print("shape:", df.shape)

    C_HEKIM = _find_column(["DKTAD", "HEKIM ADI", "DOKTOR", "HEKIM"], df.columns)
    C_PERI = _find_column(["PERIAPICAL RÖNTGEN SAYISI", "PERIAPIKAL RÖNTGEN SAYISI"], df.columns)
    C_PAN = _find_column(["PANORAMIK RÖNTGEN SAYISI"], df.columns)
    C_SEF = _find_column(["SEFALOMETRIK RÖNTGEN SAYISI"], df.columns)
    C_TOMO = _find_column(["DENTAL TOMOGRAFI RÖNTGEN SAYISI"], df.columns)
    print("C_HEKIM:", C_HEKIM)
    print("film cols raw:", C_PERI, C_PAN, C_SEF, C_TOMO)

    film_cols = [c for c in [C_PERI, C_PAN, C_SEF, C_TOMO] if c is not None]
    print("film_cols:", film_cols)

    for col in film_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["TOPLAM_FILM"] = df[film_cols].sum(axis=1)
    hekim_sum = (
        df.groupby(C_HEKIM)[film_cols]
        .sum()
        .reset_index()
    )
    hekim_sum["TOPLAM_FILM"] = hekim_sum[film_cols].sum(axis=1)
    hekim_sum = hekim_sum.sort_values("TOPLAM_FILM", ascending=False)
    print("hekim_sum head:\n", hekim_sum.head(10).to_string())

    top_n = 15
    hekim_top = hekim_sum.head(top_n)
    heat_df = hekim_top.set_index(C_HEKIM)[film_cols]
    print("\nheat_df shape:", heat_df.shape)
    print("heat_df head:\n", heat_df.head().to_string())


if __name__ == "__main__":
    main()

