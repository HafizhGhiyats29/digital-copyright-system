# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=1000
ENV PIP_RETRIES=10

WORKDIR /app

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install \
        --default-timeout=1000 \
        --retries=10 \
        --progress-bar off \
        --index-url https://download.pytorch.org/whl/cpu \
        torch \
        torchvision

RUN --mount=type=cache,target=/root/.cache/pip \
    grep -v -E '^(torch|torchvision)([=<> ].*)?$' requirements.txt > /tmp/requirements-without-torch.txt && \
    pip install \
        --default-timeout=1000 \
        --retries=10 \
        --progress-bar off \
        -r /tmp/requirements-without-torch.txt

COPY . .

EXPOSE 8002

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
