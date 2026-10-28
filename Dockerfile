FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY goatcounter_mcp_server ./goatcounter_mcp_server

EXPOSE 8000

CMD ["python", "-m", "goatcounter_mcp_server"]
