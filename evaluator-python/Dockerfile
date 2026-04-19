FROM python:3.11-alpine
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .
ENTRYPOINT ["consequence"]
CMD ["--help"]
