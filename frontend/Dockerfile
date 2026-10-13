
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.29-alpine

USER root
RUN apk upgrade --no-cache

ENV BACKEND_URL=http://backend:8000

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

USER 101
EXPOSE 8080
