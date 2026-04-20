FROM python:3.11-alpine
WORKDIR /app
COPY pyproject.toml README.md ./
COPY evaluator/ ./evaluator/
COPY eval/ ./eval/
COPY copilot_cli/ ./copilot_cli/
RUN pip install --no-cache-dir .
ENTRYPOINT ["uvicorn"]
CMD ["evaluator.api:app", "--host", "0.0.0.0", "--port", "8000"]
