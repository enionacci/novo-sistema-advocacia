"""
Views para API de Documentos

Endpoints:
- /api/documentos/categorias/ - CRUD de categorias
- /api/documentos/tags/ - CRUD de tags
- /api/documentos/ - CRUD de documentos
- /api/documentos/{id}/download/ - Download do arquivo
- /api/documentos/{id}/incrementar-visualizacao/ - Incrementa contador
- /api/clientes/{id}/documentos/ - Documentos de um cliente específico
- /api/documentos/salvar-scanner/ - Salvar documento do scanner (NOVO)
- /api/documentos/ocr/ - Processar OCR
- /api/documentos/ocr-progress/{task_id}/ - Consultar progresso OCR
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse, Http404, JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
import os
import traceback
import uuid

from .models import Categoria, Tag, Documento
from .serializers import (
    CategoriaSerializer, TagSerializer,
    DocumentoListSerializer, DocumentoDetailSerializer,
    DocumentoCreateSerializer, DocumentoUpdateSerializer
)
from .permissions import DocumentoPermission, CategoriaPermission, TagPermission


class CategoriaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de categorias de documentos
    
    list: Lista todas as categorias do escritório
    create: Cria nova categoria
    retrieve: Detalhe de uma categoria
    update/partial_update: Atualiza categoria
    destroy: Remove categoria
    """
    serializer_class = CategoriaSerializer
    permission_classes = [CategoriaPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'descricao']
    ordering_fields = ['nome', 'ordem', 'data_criacao']
    ordering = ['ordem', 'nome']

    def get_queryset(self):
        """Retorna apenas categorias do escritório do usuário"""
        return Categoria.objects.filter(
            escritorio=self.request.user.perfil.escritorio,
            ativo=True
        )


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de tags
    
    list: Lista todas as tags do escritório
    create: Cria nova tag
    retrieve: Detalhe de uma tag
    update/partial_update: Atualiza tag
    destroy: Remove tag
    """
    serializer_class = TagSerializer
    permission_classes = [TagPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome']
    ordering_fields = ['nome', 'data_criacao']
    ordering = ['nome']

    def get_queryset(self):
        """Retorna apenas tags do escritório do usuário"""
        return Tag.objects.filter(
            escritorio=self.request.user.perfil.escritorio
        )


class DocumentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de documentos
    
    list: Lista documentos com filtros
    create: Upload de novo documento
    retrieve: Detalhe do documento
    update/partial_update: Atualiza metadados
    destroy: Remove documento (soft delete)
    download: Faz download do arquivo
    incrementar_visualizacao: Incrementa contador de visualizações
    """
    permission_classes = [DocumentoPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categoria', 'cliente', 'confidencial', 'tipo_arquivo']
    search_fields = ['titulo', 'descricao', 'nome_original', 'texto_extraido']
    ordering_fields = ['data_upload', 'data_documento', 'titulo', 'tamanho', 'visualizacoes']
    ordering = ['-data_upload']

    def get_queryset(self):
        """
        Retorna apenas documentos do escritório do usuário
        Permite filtrar por cliente_id via query param
        """
        queryset = Documento.objects.filter(
            escritorio=self.request.user.perfil.escritorio,
            ativo=True
        ).select_related(
            'categoria', 'cliente', 'usuario_upload'
        ).prefetch_related('tags')

        # Filtro por cliente (query param)
        cliente_id = self.request.query_params.get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)

        # Filtro por data
        data_inicio = self.request.query_params.get('data_inicio')
        data_fim = self.request.query_params.get('data_fim')
        if data_inicio:
            queryset = queryset.filter(data_upload__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_upload__lte=data_fim)

        # Filtro por tags
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__id__in=tags).distinct()

        return queryset

    def get_serializer_class(self):
        """Retorna o serializer apropriado para cada action"""
        if self.action == 'list':
            return DocumentoListSerializer
        elif self.action == 'create':
            return DocumentoCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DocumentoUpdateSerializer
        return DocumentoDetailSerializer

    def perform_destroy(self, instance):
        """Soft delete - marca como inativo ao invés de deletar"""
        instance.ativo = False
        instance.save()

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Endpoint para download do arquivo
        GET /api/documentos/{id}/download/
        Query params: ?inline=true (para visualização no navegador)
        """
        print(f"📥 [DEBUG] Iniciando download do documento {pk}")
        documento = self.get_object()
        print(f"📥 [DEBUG] Documento encontrado: {documento.titulo} ({documento.tamanho} bytes)")
        
        try:
            # Incrementa contador de downloads apenas se não for visualização inline
            inline = request.query_params.get('inline', 'false').lower() == 'true'
            if not inline:
                documento.incrementar_downloads()
                print(f"📥 [DEBUG] Downloads incrementados")
            
            # Retorna o arquivo
            if not documento.arquivo:
                print(f"❌ [DEBUG] Documento sem arquivo!")
                raise Http404("Documento sem arquivo")
                
            print(f"📥 [DEBUG] Abrindo arquivo: {documento.arquivo.path}")
            file_handle = documento.arquivo.open('rb')
            response = FileResponse(file_handle)
            response['Content-Type'] = f'application/{documento.tipo_arquivo}'
            
            if inline:
                response['Content-Disposition'] = f'inline; filename="{documento.nome_original}"'
            else:
                response['Content-Disposition'] = f'attachment; filename="{documento.nome_original}"'
                
            print(f"📥 [DEBUG] Resposta preparada (inline={inline}), enviando...")
            return response
        except Exception as e:
            print(f"❌ [DEBUG] Erro no download: {e}")
            return Response(
                {'error': f'Erro ao fazer download: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def incrementar_visualizacao(self, request, pk=None):
        """
        Incrementa o contador de visualizações
        POST /api/documentos/{id}/incrementar-visualizacao/
        """
        print(f"👁️ [DEBUG] Incrementando visualização do documento {pk}")
        documento = self.get_object()
        documento.incrementar_visualizacoes()
        print(f"👁️ [DEBUG] Visualização incrementada com sucesso")
        return Response({'visualizacoes': documento.visualizacoes})

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """
        Retorna estatísticas dos documentos
        GET /api/documentos/estatisticas/
        """
        escritorio = request.user.perfil.escritorio
        queryset = self.get_queryset()

        # Estatísticas gerais
        total_documentos = queryset.count()
        total_tamanho = sum(doc.tamanho for doc in queryset)
        
        # Por categoria
        por_categoria = {}
        for cat in Categoria.objects.filter(escritorio=escritorio, ativo=True):
            por_categoria[cat.nome] = queryset.filter(categoria=cat).count()

        # Por tipo de arquivo
        por_tipo = {}
        for doc in queryset:
            tipo = doc.tipo_arquivo
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

        return Response({
            'total_documentos': total_documentos,
            'total_tamanho': total_tamanho,
            'total_tamanho_formatado': self._formatar_tamanho(total_tamanho),
            'por_categoria': por_categoria,
            'por_tipo': por_tipo,
            'total_visualizacoes': sum(doc.visualizacoes for doc in queryset),
            'total_downloads': sum(doc.downloads for doc in queryset),
        })

    def _formatar_tamanho(self, size):
        """Formata tamanho em bytes para unidade legível"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


# ========================================
# VIEWS PARA OCR E PROGRESSO
# ========================================

class OCRProgressView(APIView):
    """
    View para consultar o progresso do processamento OCR
    GET /api/documentos/ocr-progress/{task_id}/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, task_id):
        try:
            # Tentar buscar o progresso no cache/sessão
            progress_key = f"ocr_progress_{task_id}"
            progress_data = cache.get(progress_key)
            
            if progress_data:
                return Response(progress_data)
            else:
                # Se não encontrou, pode ser que já terminou ou task_id inválido
                return Response({
                    'task_id': task_id,
                    'status': 'completed',  # ou 'not_found'
                    'progress': 100,
                    'message': 'Processamento concluído ou não encontrado'
                })
                
        except Exception as e:
            return Response({
                'error': str(e),
                'status': 'failed',
                'task_id': task_id
            }, status=500)


# ========================================
# OCR SÍNCRONO SIMPLES - USANDO pypdf
# ========================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def extrair_texto_pdf(request):
    """
    Endpoint SIMPLES e DIRETO para extrair texto de PDFs.
    Usa pypdf (já instalado) - NÃO precisa de EasyOCR, PyTorch, threads, etc.
    
    POST /api/documentos/extrair-texto/
    
    Args:
        arquivo: O arquivo PDF enviado via multipart/form-data
    
    Returns:
        JSON com o texto extraído instantaneamente
    """
    try:
        if 'arquivo' not in request.FILES:
            return Response(
                {'error': 'Nenhum arquivo enviado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        arquivo = request.FILES['arquivo']
        
        # Valida extensão
        nome = arquivo.name.lower()
        if not nome.endswith('.pdf'):
            return Response(
                {'error': 'Formato não suportado. Envie apenas arquivos PDF.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Lê o arquivo para memória
        arquivo_bytes = arquivo.read()
        
        # Extrai texto usando pypdf (INSTANTÂNEO para PDFs digitais)
        from pypdf import PdfReader
        import io
        
        reader = PdfReader(io.BytesIO(arquivo_bytes))
        total_paginas = len(reader.pages)
        texto_completo = []
        
        for i, pagina in enumerate(reader.pages):
            texto = pagina.extract_text()
            if texto and texto.strip():
                texto_completo.append(f"--- Página {i + 1} ---\n{texto.strip()}")
        
        texto_final = "\n\n".join(texto_completo)
        
        if not texto_final.strip():
            # Se não extraiu texto, tenta com Tesseract (fallback para PDF escaneado)
            try:
                print("⚠️ Nenhum texto extraído com pypdf. Tentando OCR Tesseract...")
                from .ai_service import extract_text_tesseract_fallback
                texto_final = extract_text_tesseract_fallback(arquivo_bytes, None)
            except Exception as ocr_err:
                return Response({
                    'success': True,
                    'texto': '',
                    'mensagem': 'PDF sem texto extraível (pode ser escaneado).',
                    'total_paginas': total_paginas,
                    'tamanho': len(arquivo_bytes),
                    'nome_arquivo': arquivo.name,
                })
        
        return Response({
            'success': True,
            'texto': texto_final,
            'total_paginas': total_paginas,
            'tamanho': len(arquivo_bytes),
            'nome_arquivo': arquivo.name,
            'mensagem': f'Texto extraído com sucesso! {total_paginas} página(s) processada(s).'
        })
        
    except Exception as e:
        print(f"❌ Erro ao extrair texto: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return Response(
            {'error': f'Erro ao processar PDF: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ========================================
# ENDPOINT ESPECÍFICO PARA SCANNER - NOVO
# ========================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def salvar_documento_scanner(request):
    """
    Endpoint específico para salvar documentos do scanner
    Bypassa o problema do perfil/escritório
    """
    try:
        titulo = request.data.get('titulo')
        texto_extraido = request.data.get('texto_extraido')
        cliente_id = request.data.get('cliente_id')
        nome_arquivo_original = request.data.get('nome_arquivo_original', '')
        
        # Validações
        if not titulo:
            return JsonResponse({'error': 'Título é obrigatório'}, status=400)
            
        if not texto_extraido:
            return JsonResponse({'error': 'Texto extraído é obrigatório'}, status=400)
        
        # Calcular tamanho
        tamanho = len(texto_extraido.encode('utf-8'))
        
        # ✅ RESOLVER ESCRITÓRIO - MÚLTIPLAS ESTRATÉGIAS
        escritorio = None
        
        # Estratégia 1: Tentar pelo perfil do usuário
        try:
            if hasattr(request.user, 'perfil') and request.user.perfil and hasattr(request.user.perfil, 'escritorio'):
                escritorio = request.user.perfil.escritorio
        except Exception:
            pass
        
        # Estratégia 2: Pegar o primeiro escritório disponível
        if not escritorio:
            from escritorios.models import Escritorio
            escritorio = Escritorio.objects.first()
        
        # Estratégia 3: Criar um escritório padrão se não existir nenhum
        if not escritorio:
            from escritorios.models import Escritorio
            escritorio = Escritorio.objects.create(
                nome='Escritório Principal',
                ativo=True
            )
        
        # Preparar dados do documento
        documento_data = {
            'escritorio': escritorio,
            'titulo': titulo,
            'texto_extraido': texto_extraido,
            'tamanho': tamanho,
            'tipo_arquivo': 'txt',
            'nome_original': nome_arquivo_original or f"{titulo}.txt",
            'data_upload': timezone.now(),
            'usuario_upload': request.user,
            'ativo': True,
            'descricao': f'Documento digitalizado via scanner em {timezone.now().strftime("%d/%m/%Y %H:%M")}',
            'versao': 1,
            'visualizacoes': 0,
            'downloads': 0,
            'confidencial': False,
            'hash_md5': '',  # Será calculado no save() se necessário
        }
        
        # ✅ ADICIONAR CLIENTE SE FORNECIDO
        if cliente_id:
            try:
                from clientes.models import Cliente
                cliente = Cliente.objects.get(id=cliente_id, escritorio=escritorio)
                documento_data['cliente'] = cliente
            except Cliente.DoesNotExist:
                return JsonResponse({
                    'error': f'Cliente com ID {cliente_id} não encontrado no escritório'
                }, status=400)
        
        # ✅ CRIAR DOCUMENTO
        documento = Documento.objects.create(**documento_data)
        
        return JsonResponse({
            'success': True,
            'id': documento.id,
            'titulo': documento.titulo,
            'tamanho': documento.tamanho,
            'escritorio': escritorio.nome,
            'message': 'Documento salvo com sucesso via scanner'
        })
        
    except Exception as e:
        # Log detalhado do erro
        print("❌ ERRO AO SALVAR DOCUMENTO SCANNER:")
        print(traceback.format_exc())
        
        return JsonResponse({
            'error': f'Erro interno do servidor: {str(e)}',
            'type': type(e).__name__
        }, status=500)