FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Avval requirements — Docker qatlam keshini samarali ishlatish uchun
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ma'lumotlar va rasmlar uchun katalog (compose'da volume ulanadi)
RUN mkdir -p /data/media
ENV DATABASE_URL=sqlite+aiosqlite:////data/luqma.db \
    MEDIA_DIR=/data/media

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status==200 else 1)"

# API + bot bitta process ichida
CMD ["python", "main.py"]
