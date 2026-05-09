"""Run the Django app under the Waitress WSGI server.

Usage:
    python serve.py
    HOST=0.0.0.0 PORT=8000 python serve.py
"""
import os

from waitress import serve

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tasksite.settings")

from tasksite.wsgi import application  # noqa: E402


def main() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "9000"))
    threads = int(os.environ.get("WAITRESS_THREADS", "4"))
    print(f"Serving Django on http://{host}:{port} with Waitress ({threads} threads)")
    serve(application, host=host, port=port, threads=threads)


if __name__ == "__main__":
    main()
