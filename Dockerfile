# syntax=docker/dockerfile:1.7

# ===== builder =====
FROM python:3.12-slim AS builder
WORKDIR /app

# 기본 도구
RUN apt-get update && apt-get install -y --no-install-recommends \
    procps \
    curl git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
# uv 설치
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}" \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy

# 의존성 정의만 먼저 복사
COPY pyproject.toml ./
# uv.lock은 있으면 복사, 없으면 스킵(패턴 사용)
COPY uv.lock* ./

# GitHub PAT를 이미지 히스토리에 남기지 않기 위해 BuildKit secret 사용
# buildx에서: with.secrets: "gh_pat=${{ secrets.GH_PAT }}"
RUN --mount=type=secret,id=gh_pat \
    sh -lc 'git config --global url."https://$(cat /run/secrets/gh_pat):x-oauth-basic@github.com/".insteadOf "https://github.com/"'

# uv 캐시를 BuildKit 캐시로 마운트해서 빠르게 설치
# - uv.lock 없으면 생성
# - 재현성 모드는 신경 안 쓰고 빠른 설치 위주 (--frozen 미사용)
RUN --mount=type=cache,target=/root/.cache/uv \
    bash -euxo pipefail -c '\
      if [ ! -f uv.lock ]; then \
        echo "[builder] uv.lock not found -> generating"; \
        uv lock; \
      fi; \
      uv sync --no-dev --no-install-project \
    '

# 앱 소스는 나중에 복사(의존성 레이어 재사용을 위해)
COPY src ./src

# 프로젝트 설치 (개발 의존성 제외)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev

# ===== runtime =====
FROM python:3.12-slim AS runtime
WORKDIR /app/src

RUN apt-get update && apt-get install -y --no-install-recommends \
    procps \
    curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# 빌더에서 완성된 가상환경/코드/락 복사
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/pyproject.toml /app/pyproject.toml
COPY --from=builder /app/uv.lock /app/uv.lock
COPY global-bundle.pem /app/global-bundle.pem

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1
    
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD pgrep -f 'app.py' || exit 1