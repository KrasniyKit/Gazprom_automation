FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_API_URL=
ARG VITE_UPLOAD_ENDPOINT=/api/passports/upload
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_UPLOAD_ENDPOINT=${VITE_UPLOAD_ENDPOINT}

RUN npm run build

FROM nginx:1.27-alpine AS runner

ENV API_UPSTREAM=host.docker.internal:9099
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
