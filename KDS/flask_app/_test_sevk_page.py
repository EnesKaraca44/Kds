from app import create_app


def main():
    app = create_app()

    with app.test_client() as client:
        # Fake login
        with client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["logged_in_user"] = "test"

        resp = client.get("/sevk")
        html = resp.data.decode("utf-8", errors="ignore")

        out_path = "_test_sevk_render.html"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print("Status:", resp.status_code)
        print("Saved HTML to", out_path, "size:", len(html))


if __name__ == "__main__":
    main()

