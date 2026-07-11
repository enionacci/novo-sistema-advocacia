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
from django.http import FileResponse, Http404, JsonResponse, HttpResponse
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
import os
import io
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
# OCR HÍBRIDO - Página por página (digital + escaneado)
# ========================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def extrair_texto_pdf(request):
    """
    Endpoint HÍBRIDO que extrai texto de PDFs página por página.
    Para cada página, decide automaticamente entre:
    - pypdf (instantâneo) para páginas digitais
    - Tesseract OCR para páginas escaneadas
    
    POST /api/documentos/extrair-texto/
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
        
        # Usa o método HÍBRIDO do OCRService
        from .ai_service import OCRService
        texto_final = OCRService.extract_text_from_pdf(arquivo_bytes)
        
        return Response({
            'success': True,
            'texto': texto_final,
            'total_paginas': texto_final.count('--- Página'),
            'tamanho': len(arquivo_bytes),
            'nome_arquivo': arquivo.name,
            'mensagem': 'Texto extraído com método híbrido (digital + OCR).'
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


# ========================================
# FERRAMENTAS DE PDF
# ========================================

def pdf_tool_required(view_func):
    """Decorator que verifica permissão para usar ferramentas PDF."""
    from functools import wraps
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'error': 'Não autenticado.'}, status=401)
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        try:
            if hasattr(request.user, 'perfil') and request.user.perfil:
                tem_perm = request.user.perfil.papeis.filter(
                    permissoes__codename='usar_ferramentas_pdf'
                ).exists()
                if tem_perm:
                    return view_func(request, *args, **kwargs)
        except Exception:
            pass
        return Response({'error': 'Permissão negada.'}, status=403)
    return _wrapped_view


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@pdf_tool_required
def merge_pdfs(request):
    """
    Junta múltiplos PDFs em um único arquivo.
    """
    try:
        files = request.FILES.getlist('arquivos')
        if len(files) < 2:
            return Response(
                {'error': 'Envie pelo menos 2 arquivos PDF.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Valida extensões
        for f in files:
            if not f.name.lower().endswith('.pdf'):
                return Response(
                    {'error': f'O arquivo "{f.name}" não é um PDF.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        from .pdf_tools import merge_pdfs as merge_tool
        arquivos_bytes = [f.read() for f in files]
        pdf_resultado = merge_tool(arquivos_bytes)

        response = HttpResponse(pdf_resultado, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="pdf_merged.pdf"'
        return response

    except Exception as e:
        print(f"❌ Erro ao juntar PDFs: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return Response(
            {'error': f'Erro ao juntar PDFs: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@pdf_tool_required
def split_pdf(request):
    """
    Divide um PDF em múltiplos arquivos.
    """

    POST /api/documentos/pdf/split/

    Recebe: arquivo PDF + JSON com intervalos de páginas
    Exemplo: {"intervalos": [{"inicio": 1, "fim": 3}, {"inicio": 4, "fim": 5}]}
    Retorna: ZIP com os PDFs divididos
    """
    try:
        if 'arquivo' not in request.FILES:
            return Response(
                {'error': 'Nenhum arquivo enviado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        arquivo = request.FILES['arquivo']
        if not arquivo.name.lower().endswith('.pdf'):
            return Response(
                {'error': 'O arquivo deve ser um PDF.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        import json
        try:
            data = json.loads(request.data.get('data', '{}'))
            intervalos = data.get('intervalos', [])
        except (json.JSONDecodeError, TypeError):
            return Response(
                {'error': 'Formato de dados inválido.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not intervalos:
            return Response(
                {'error': 'Nenhum intervalo de páginas fornecido.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from .pdf_tools import split_pdf_to_zip
        pdf_bytes = arquivo.read()
        page_ranges = [(r['inicio'], r['fim']) for r in intervalos]
        nomes = [r.get('nome', f'parte_{i+1}.pdf') for i, r in enumerate(intervalos)]

        zip_resultado = split_pdf_to_zip(pdf_bytes, page_ranges, nomes)

        response = HttpResponse(zip_resultado, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="pdf_split.zip"'
        return response

    except Exception as e:
        print(f"❌ Erro ao dividir PDF: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return Response(
            {'error': f'Erro ao dividir PDF: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@pdf_tool_required
def compress_pdf(request):
    """
    Compacta um PDF reduzindo o tamanho.

    POST /api/documentos/pdf/compress/

    Recebe: arquivo PDF + qualidade (low/medium/high)
    Retorna: PDF compactado para download
    """
    try:
        if 'arquivo' not in request.FILES:
            return Response(
                {'error': 'Nenhum arquivo enviado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        arquivo = request.FILES['arquivo']
        if not arquivo.name.lower().endswith('.pdf'):
            return Response(
                {'error': 'O arquivo deve ser um PDF.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        quality = request.data.get('quality', 'medium')
        if quality not in ('low', 'medium', 'high'):
            quality = 'medium'

        from .pdf_tools import compress_pdf as compress_tool
        pdf_bytes = arquivo.read()
        pdf_resultado = compress_tool(pdf_bytes, quality)

        response = HttpResponse(pdf_resultado, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="pdf_compactado.pdf"'
        return response

    except Exception as e:
        print(f"❌ Erro ao compactar PDF: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return Response(
            {'error': f'Erro ao compactar PDF: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@pdf_tool_required
def convert_images_to_pdf(request):
    """
    Converte imagens em um PDF.

    POST /api/documentos/pdf/convert-image/

    Recebe: uma ou mais imagens (jpg, png, etc.)
    Retorna: PDF gerado para download
    """
    try:
        files = request.FILES.getlist('imagens')
        if not files:
            return Response(
                {'error': 'Nenhuma imagem enviada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Valida extensões
        ext_validas = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')
        for f in files:
            ext = os.path.splitext(f.name.lower())[1]
            if ext not in ext_validas:
                return Response(
                    {'error': f'O arquivo "{f.name}" não é uma imagem suportada.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        from .pdf_tools import images_to_pdf
        imagens_bytes = [f.read() for f in files]
        pdf_resultado = images_to_pdf(imagens_bytes)

        response = HttpResponse(pdf_resultado, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="imagens_convertidas.pdf"'
        return response

    except Exception as e:
        print(f"❌ Erro ao converter imagens: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return Response(
            {'error': f'Erro ao converter imagens: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@pdf_tool_required
def pdf_to_images_view(request):
    """
    Converte cada página de um PDF em imagens PNG.
    Retorna um ZIP com as imagens.

    POST /api/documentos/pdf/to-images/
    """
    try:
        if 'arquivo' not in request.FILES:
            return Response({'error': 'Nenhum arquivo enviado.'}, status=400)

        arquivo = request.FILES['arquivo']
        if not arquivo.name.lower().endswith('.pdf'):
            return Response({'error': 'O arquivo deve ser um PDF.'}, status=400)

        dpi = int(request.data.get('dpi', 200))

        from .pdf_tools import pdf_to_images
        pdf_bytes = arquivo.read()
        imagens = pdf_to_images(pdf_bytes, dpi)

        import zipfile
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i, img_bytes in enumerate(imagens):
                zf.writestr(f'pagina_{i+1}.png', img_bytes)

        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="pdf_imagens.zip"'
        return response

    except Exception as e:
        print(f"❌ Erro ao converter PDF para imagens: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@pdf_tool_required
def extract_pdf_pages(request):
    """
    Extrai páginas específicas de um PDF.

    POST /api/documentos/pdf/extract-pages/

    Recebe: arquivo PDF + JSON com lista de páginas
    Exemplo: {"paginas": [1, 3, 5]}
    """
    try:
        if 'arquivo' not in request.FILES:
            return Response({'error': 'Nenhum arquivo enviado.'}, status=400)

        arquivo = request.FILES['arquivo']
        if not arquivo.name.lower().endswith('.pdf'):
            return Response({'error': 'O arquivo deve ser um PDF.'}, status=400)

        import json
        try:
            data = json.loads(request.data.get('data', '{}'))
            paginas = data.get('paginas', [])
        except (json.JSONDecodeError, TypeError):
            return Response({'error': 'Formato de dados inválido.'}, status=400)

        if not paginas:
            return Response({'error': 'Nenhuma página fornecida.'}, status=400)

        from .pdf_tools import extract_pages
        pdf_bytes = arquivo.read()
        pdf_resultado = extract_pages(pdf_bytes, paginas)

        response = HttpResponse(pdf_resultado, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="paginas_extraidas.pdf"'
        return response

    except Exception as e:
        print(f"❌ Erro ao extrair páginas: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@pdf_tool_required
def insert_blank_page_view(request):
    """
    Insere uma página em branco em um PDF.

    POST /api/documentos/pdf/insert-blank/

    Recebe: arquivo PDF + posição opcional (padrão: final)
    """
    try:
        if 'arquivo' not in request.FILES:
            return Response({'error': 'Nenhum arquivo enviado.'}, status=400)

        arquivo = request.FILES['arquivo']
        if not arquivo.name.lower().endswith('.pdf'):
            return Response({'error': 'O arquivo deve ser um PDF.'}, status=400)

        position = request.data.get('position')
        if position:
            position = int(position)

        from .pdf_tools import insert_blank_page
        pdf_bytes = arquivo.read()
        pdf_resultado = insert_blank_page(pdf_bytes, position)

        response = HttpResponse(pdf_resultado, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="pdf_com_pagina_branca.pdf"'
        return response

    except Exception as e:
        print(f"❌ Erro ao inserir página em branco: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@pdf_tool_required
def rotate_pdf_pages_view(request):
    """
    Rotaciona páginas de um PDF.

    POST /api/documentos/pdf/rotate/

    Recebe: arquivo PDF + rotação (90/180/270) + páginas opcionais
    """
    try:
        if 'arquivo' not in request.FILES:
            return Response({'error': 'Nenhum arquivo enviado.'}, status=400)

        arquivo = request.FILES['arquivo']
        if not arquivo.name.lower().endswith('.pdf'):
            return Response({'error': 'O arquivo deve ser um PDF.'}, status=400)

        rotation = int(request.data.get('rotation', 90))
        if rotation not in (90, 180, 270):
            return Response({'error': 'Rotação deve ser 90, 180 ou 270.'}, status=400)

        import json
        paginas = None
        try:
            data = json.loads(request.data.get('data', '{}'))
            paginas = data.get('paginas')
        except (json.JSONDecodeError, TypeError):
            pass

        from .pdf_tools import rotate_pdf_pages
        pdf_bytes = arquivo.read()
        pdf_resultado = rotate_pdf_pages(pdf_bytes, rotation, paginas)

        response = HttpResponse(pdf_resultado, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="pdf_rotacionado.pdf"'
        return response

    except Exception as e:
        print(f"❌ Erro ao rotacionar PDF: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@pdf_tool_required
def pdf_to_docx_view(request):
    """
    Converte um PDF para formato Word (DOCX).

    POST /api/documentos/pdf/to-docx/
    """
    try:
        if 'arquivo' not in request.FILES:
            return Response({'error': 'Nenhum arquivo enviado.'}, status=400)

        arquivo = request.FILES['arquivo']
        if not arquivo.name.lower().endswith('.pdf'):
            return Response({'error': 'O arquivo deve ser um PDF.'}, status=400)

        from .pdf_tools import pdf_to_docx
        pdf_bytes = arquivo.read()
        docx_bytes = pdf_to_docx(pdf_bytes)

        response = HttpResponse(docx_bytes, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = 'attachment; filename="documento_convertido.docx"'
        return response

    except Exception as e:
        print(f"❌ Erro ao converter PDF para Word: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@pdf_tool_required
def add_page_numbers_view(request):
    """
    Adiciona numeração de páginas a um PDF.

    POST /api/documentos/pdf/add-numbers/

    Parâmetros:
        arquivo: PDF
        position: 'bottom' ou 'top' (padrão: bottom)
        start_number: número inicial (padrão: 1)
        prefix: texto antes do número (opcional)
        suffix: texto depois do número (opcional)
    """
    try:
        if 'arquivo' not in request.FILES:
            return Response({'error': 'Nenhum arquivo enviado.'}, status=400)

        arquivo = request.FILES['arquivo']
        if not arquivo.name.lower().endswith('.pdf'):
            return Response({'error': 'O arquivo deve ser um PDF.'}, status=400)

        position = request.data.get('position', 'bottom')
        start_number = int(request.data.get('start_number', 1))
        prefix = request.data.get('prefix', '')
        suffix = request.data.get('suffix', '')

        from .pdf_tools import add_page_numbers
        pdf_bytes = arquivo.read()
        pdf_resultado = add_page_numbers(pdf_bytes, position, start_number, prefix, suffix)

        response = HttpResponse(pdf_resultado, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="pdf_numerado.pdf"'
        return response

    except Exception as e:
        print(f"❌ Erro ao numerar páginas: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return Response({'error': str(e)}, status=500)