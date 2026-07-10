# 🔄 Rebuild Local - Recria containers com nova configuração

Write-Host "🔄 Rebuild Local - Sistema de Advocacia" -ForegroundColor Cyan
Write-Host ""

# ============================================
# PARAR CONTAINERS
# ============================================
Write-Host "🛑 Parando containers..." -ForegroundColor Yellow
docker-compose down

Write-Host "✅ Containers parados!" -ForegroundColor Green
Write-Host ""

# ============================================
# REMOVER IMAGENS ANTIGAS
# ============================================
Write-Host "🗑️  Removendo imagens antigas..." -ForegroundColor Yellow
docker rmi advocacia-frontend -f 2>$null
docker rmi advocacia-backend -f 2>$null

Write-Host "✅ Imagens removidas!" -ForegroundColor Green
Write-Host ""

# ============================================
# REBUILD SEM CACHE
# ============================================
Write-Host "🏗️  Rebuilding frontend (produção otimizada)..." -ForegroundColor Yellow
docker-compose build --no-cache frontend

Write-Host "🏗️  Rebuilding backend..." -ForegroundColor Yellow
docker-compose build --no-cache backend

Write-Host "✅ Build concluído!" -ForegroundColor Green
Write-Host ""

# ============================================
# SUBIR CONTAINERS
# ============================================
Write-Host "🚀 Iniciando containers..." -ForegroundColor Yellow
docker-compose up -d

Write-Host "✅ Containers iniciados!" -ForegroundColor Green
Write-Host ""

# ============================================
# MOSTRAR STATUS
# ============================================
Write-Host "📊 Status dos containers:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "🎉 Rebuild local concluído!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Para ver logs:" -ForegroundColor Yellow
Write-Host "   docker-compose logs -f frontend" -ForegroundColor White
Write-Host "   docker-compose logs -f backend" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Acesse: http://localhost" -ForegroundColor Cyan
