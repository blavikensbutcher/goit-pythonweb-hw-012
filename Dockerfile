FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock* ./

RUN uv sync --frozen

COPY . .

RUN mkdir -p src/certs

EXPOSE 8090

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]