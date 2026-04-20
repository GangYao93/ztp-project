FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ANSIBLE_HOST_KEY_CHECKING=False

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openssh-client \
        sshpass \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install ansible-core \
    && ansible-galaxy collection install vyos.vyos

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
