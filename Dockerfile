ARG PY_VER=3.12
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
    uv sync --frozen --no-dev --no-editable --no-install-project

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system app && useradd --system --gid app app
USER app

ENTRYPOINT ["uv", "run", "smartgit"]
CMD ["--help"]