from app import create_app


def dump_variant(label: str, query: str, save_html: bool = False) -> None:
    app = create_app()
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["logged_in_user"] = "test"

        resp = client.get("/sevk" + query)
        html = resp.data.decode("utf-8", errors="ignore")
        print(f"\n=== {label} ===")
        print("status:", resp.status_code, "len:", len(html))
        print("contains 'Sevk Oran Tablosu' ?", 'Sevk Oran Tablosu' in html)
        print("contains 'Hekim Bazlı Sevk Verimliliği' ?", 'Hekim Bazlı Sevk Verimliliği' in html)
        print("contains 'js-plotly-plot' ?", 'js-plotly-plot' in html)
        # Small snippet around Sevk Oran Tablosu if exists
        idx = html.find("Sevk Oran Tablosu")
        if idx != -1:
            start = max(0, idx - 200)
            end = idx + 200
            print("...snippet around 'Sevk Oran Tablosu' ...")
            print(html[start:end])

        if save_html:
            fname = f"_test_sevk_{label.replace(' ', '_').lower()}.html"
            with open(fname, "w", encoding="utf-8") as f:
                f.write(html)
            print("saved full html to", fname)


if __name__ == "__main__":
    dump_variant("NO QUERY (default)", "")
    dump_variant("BU YIL", "?quick=bu-yil")
    dump_variant("GECEN YIL", "?quick=gecen-yil", save_html=True)
    dump_variant("SON 30 GUN", "?quick=son-30")

