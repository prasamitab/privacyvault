FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        git \
        libgomp1 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work

RUN python -m pip install --no-cache-dir "Pyfhel==3.5.0"

COPY test_he.py .

CMD ["python", "test_he.py"]
