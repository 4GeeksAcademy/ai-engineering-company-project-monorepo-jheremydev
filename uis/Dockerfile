FROM node:22-alpine

WORKDIR /workspace

COPY --from=monorepo package.json package-lock.json ./
COPY --from=monorepo uis/website/package.json ./uis/website/package.json
COPY --from=monorepo uis/backoffice/package.json ./uis/backoffice/package.json
COPY --from=monorepo packages/shared/package.json ./packages/shared/package.json

RUN npm install --workspace=uis/website --include-workspace-root=false \
    && npm install --workspace=uis/backoffice --include-workspace-root=false

COPY --from=monorepo uis/website/ ./uis/website/
COPY --from=monorepo uis/backoffice/ ./uis/backoffice/
COPY --from=monorepo packages/shared/ ./packages/shared/
COPY start.sh ./start.sh

RUN chmod +x ./start.sh

EXPOSE 5173 5174

CMD ["./start.sh"]