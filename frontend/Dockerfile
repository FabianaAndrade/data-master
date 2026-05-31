# ─────────────────────────────────────────────
# Stage 1: build
# ─────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copia manifests primeiro (cache de layer)
COPY package.json package-lock.json ./

RUN npm ci

# Copia o restante e gera o bundle de produção
COPY . .

RUN npm run build

# ─────────────────────────────────────────────
# Stage 2: servir com nginx na porta 3000
# ─────────────────────────────────────────────
FROM nginx:1.27-alpine

# Configuração nginx customizada (porta 3000 + SPA fallback)
RUN printf 'server {\n\
    listen 3000;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    \n\
    # SPA fallback — todas as rotas devolvem index.html\n\
    location / {\n\
    try_files $uri $uri/ /index.html;\n\
    }\n\
    \n\
    # Cache de assets com hash no nome\n\
    location ~* \\.(js|css|png|jpg|svg|ico|woff2?)$ {\n\
    expires 1y;\n\
    add_header Cache-Control "public, immutable";\n\
    }\n\
    }\n' > /etc/nginx/conf.d/default.conf

# Copia o build do stage anterior
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
