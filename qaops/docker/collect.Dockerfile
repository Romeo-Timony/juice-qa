# Isolated runtime for `pytest --collect-only` of generated autotests (QAOps Seam 3).
# Browsers are intentionally not installed: collection needs imports and fixtures, not Chromium.
FROM python:3.12-slim
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
WORKDIR /work
