import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.denture_loaders import load_prosthetic_performance_data


def main():
    sd = "2025-01-01"
    ed = "2025-12-31"
    df = load_prosthetic_performance_data(sd, ed)
    print("shape:", df.shape)
    print("cols:", list(df.columns))
    print("dtypes:\n", df.dtypes)
    print("\nhead:\n", df.head(10).to_string())


if __name__ == "__main__":
    main()

