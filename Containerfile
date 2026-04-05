# ragdeck — admin UI for rag-suite
# Base: UBI10 minimal, pinned to digest for reproducibility
FROM registry.access.redhat.com/ubi10@sha256:1b616c4a90d6444b394d5c8f4bd9e15a394d95dd628925d0ec80c257fdc5099c

# hadolint ignore=DL3041
RUN dnf install -y -q python3 python3-pip curl && \
    dnf clean all && \
    rm -rf /var/cache/dnf

WORKDIR /app

COPY pyproject.toml README.md ./
COPY ragdeck/ ragdeck/
RUN pip install --no-cache-dir .

USER 1001

EXPOSE 8092

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -sf http://localhost:8092/health || exit 1

CMD ["uvicorn", "ragdeck.main:app", "--host", "0.0.0.0", "--port", "8092"]
