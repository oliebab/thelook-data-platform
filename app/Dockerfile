# Streamlit app for TheLook Data Platform.
# Built by the `streamlit` service in airflow/docker-compose.yaml (build context: ../app).
# On the VM, the BigQuery client picks up the VM's service account automatically:
# no credentials file is needed.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN pip install \
        streamlit \
        plotly \
        pandas \
        db-dtypes \
        google-cloud-bigquery

# The build context is app/, so this copies Home.py, data.py and pages/.
COPY . .

# Run as a non-root user.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

# 0.0.0.0 so the app is reachable from outside the container;
# compose publishes it on 127.0.0.1 only.
CMD ["streamlit", "run", "Home.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
