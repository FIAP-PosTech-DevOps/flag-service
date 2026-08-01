# BASE_REGISTRY permite trocar a origem das imagens base sem editar o
# Dockerfile. O default é o Docker Hub, para o build local continuar
# funcionando; o build-and-push.sh sobrescreve com o ECR privado espelhado.
ARG BASE_REGISTRY=docker.io/library

# Stage 1: instala as dependências isoladamente. O compilador e o cache do pip
# ficam neste estágio e não entram na imagem final.
FROM ${BASE_REGISTRY}/python:3.9-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: runtime enxuto e sem root.
ARG BASE_REGISTRY=docker.io/library
FROM ${BASE_REGISTRY}/python:3.9-slim
RUN useradd --uid 1000 --create-home appuser
WORKDIR /app
COPY --from=builder --chown=1000:1000 /root/.local /home/appuser/.local
COPY --chown=1000:1000 . .
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1
USER 1000
EXPOSE 8002
CMD ["gunicorn", "--bind", "0.0.0.0:8002", "app:app"]
