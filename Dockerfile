ARG PY_VER=3.13
ARG UV_VER=0.11.26

FROM ghcr.io/astral-sh/uv:${UV_VER} AS uv_base
FROM python:${PY_VER}-slim AS builder

COPY --from=uv_base /uv /uvx /bin

ENV UV_NO_MANAGED_PYTHON=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project --no-editable

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

ENV PATH="/app/.venv/bin:$PATH"

# TODO: Remove vim for production
RUN apt-get update \
    && apt-get install -y --no-install-recommends git vim \
    && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["uv", "run", "smartgit"]
CMD ["--help"]