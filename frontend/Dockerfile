# Frontend Dockerfile para React - PRODUÇÃO
# Multi-stage build para otimização

# Stage 1: Build da aplicação
FROM node:20-alpine AS builder

LABEL maintainer="Sistema de Advocacia"
LABEL description="Frontend React - Build Stage"

WORKDIR /app

# Copiar arquivos de dependências
COPY frontend/package*.json ./

# Instalar dependências
RUN npm install

# Copiar código da aplicação
COPY frontend/ ./

# Copiar variáveis de ambiente de produção
# O React (CRA) incorpora REACT_APP_* no bundle em tempo de build
COPY frontend/.env.production .env

# Build da aplicação para produção
RUN npm run build

# Stage 2: Servidor Nginx para produção
FROM nginx:alpine

LABEL maintainer="Sistema de Advocacia"
LABEL description="Frontend React - Production"

# Copiar arquivos buildados do stage anterior
COPY --from=builder /app/build /usr/share/nginx/html

# Copiar configuração do nginx
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expor porta 80
EXPOSE 80

# Iniciar nginx
CMD ["nginx", "-g", "daemon off;"]
