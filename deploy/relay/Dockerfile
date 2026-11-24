FROM python:3.12-slim

WORKDIR /app
COPY deploy/relay/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && useradd --create-home --uid 10001 relay
COPY scripts/pk_relay.py /app/pk_relay.py
RUN chown relay:relay /app/pk_relay.py

USER relay
ENV HOST=0.0.0.0
ENV PORT=8765
EXPOSE ${PORT}
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('PORT', '8765') + '/health', timeout=3).read()"
CMD ["python", "/app/pk_relay.py"]
