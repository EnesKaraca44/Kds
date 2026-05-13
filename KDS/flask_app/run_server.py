import os

from waitress import serve

from wsgi import app


if __name__ == "__main__":
    host = os.getenv("KDS_HOST", "0.0.0.0")
    port = int(os.getenv("KDS_PORT", "5000"))
    threads = int(os.getenv("KDS_THREADS", "8"))

    serve(app, host=host, port=port, threads=threads)
