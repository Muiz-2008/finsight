# --- Build stage -----------------------------------------------------------
FROM node:22-alpine AS build

WORKDIR /app

# VITE_API_URL is compiled into the static bundle at build time (Vite env
# vars are not readable at container runtime), so it must be supplied as a
# build arg, e.g.:
#   docker build --build-arg VITE_API_URL=http://api.example.com -t finsight-frontend .
# or, in docker-compose.yml:
#   build:
#     context: ./frontend
#     args:
#       VITE_API_URL: http://localhost:8000
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# --- Serve stage -------------------------------------------------------------
FROM nginx:1.27-alpine AS serve

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
