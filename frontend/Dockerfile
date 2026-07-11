# Frontend Dockerfile para React - PRODUÇÃO
# Usa build pré-compilado (feito localmente) para evitar consumo de recursos na VPS

FROM nginx:alpine

LABEL maintainer="Sistema de Advocacia"
LABEL description="Frontend React - Production"

# Copiar arquivos buildados (pré-compilados localmente)
COPY frontend/build /usr/share/nginx/html

# Copiar configuração do nginx
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expor porta 80
EXPOSE 80

# Iniciar nginx
CMD ["nginx", "-g", "daemon off;"]
