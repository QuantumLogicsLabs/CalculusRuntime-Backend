FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip uninstall -y fpdf pyfpdf pypdf 2>/dev/null || true
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Platforms like Railway/Render inject $PORT
ENV PORT=8000
EXPOSE 8000

# Entry is main:app (Starlette in main.py) — there is no app.py
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
