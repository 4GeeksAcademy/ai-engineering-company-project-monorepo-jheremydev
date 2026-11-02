FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir uv

WORKDIR /app/services/api

COPY api/ ./
COPY telemetry/ /app/services/telemetry/
COPY reporting/ /app/services/reporting/
COPY --from=monorepo data/pipelines/ /app/data/pipelines/
ENV PYTHONPATH=/app/services:/app
COPY --from=monorepo docs/telemetry/event-schemas.json /app/docs/telemetry/event-schemas.json
RUN uv pip install --system -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]