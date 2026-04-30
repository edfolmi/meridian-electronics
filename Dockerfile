FROM node:20-bookworm AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend ./
ARG NEXT_PUBLIC_API_BASE_URL=
ARG BACKEND_API_BASE_URL=http://127.0.0.1:8000
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV BACKEND_API_BASE_URL=$BACKEND_API_BASE_URL
RUN npm run build

FROM python:3.12-slim

WORKDIR /app
ENV APP_ENV=production
ENV BACKEND_API_BASE_URL=http://127.0.0.1:8000
ENV FRONTEND_ORIGIN=http://localhost:7860
ENV PORT=7860

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

COPY backend ./backend
COPY --from=frontend-build /app/frontend ./frontend
COPY docker/start.sh ./docker/start.sh
RUN chmod +x ./docker/start.sh

EXPOSE 7860
CMD ["./docker/start.sh"]

