import os
import sys
import io

# Windows servis ortaminda sistem kod sayfasi (cp1254 / ANSI) yerine her zaman UTF-8 kullan.
# Bu satirlar PYTHONUTF8=1 ortam degiskeni olmadan calisan eski kurulumlar icin de gerekli.
if sys.stdout and hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer') and getattr(sys.stderr, 'encoding', '').lower() not in ('utf-8', 'utf8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from waitress import serve

from wsgi import app


if __name__ == "__main__":
    host = os.getenv("KDS_HOST", "0.0.0.0")
    port = int(os.getenv("KDS_PORT", "5000"))
    threads = int(os.getenv("KDS_THREADS", "8"))

    serve(app, host=host, port=port, threads=threads)
