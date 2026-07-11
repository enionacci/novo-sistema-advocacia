"""
Views para Scanner & Análise com IA
"""

from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.http import JsonResponse
from django.db import transaction
from .models import Documento, DocumentoAnaliseIA
from .serializers import (
    DocumentoAnaliseIAListSerializer,
    DocumentoAnaliseIADetailSerializer,
    DocumentoAnaliseIACreateSerializer
)
from .ai_service import OCRService, AIAnalysisService
from .progress_service import progress_tracker
from escritorios.permissions import HasPermission
import os
import uuid
import threading
import tempfile


class DocumentoOCRAsyncView(views.APIView):
    """
    View para processar OCR assíncrono com rastreamento de progresso
    POST: Inicia processamento OCR e retorna task_id para acompanhamento
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Inicia processamento OCR assíncrono
        """
        try:
            # Validação
            if 'arquivo' not in request.FILES:
                return Response(
                    {'error': 'Arquivo não fornecido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            arquivo = request.FILES['arquivo']
            tipo_arquivo = os.path.splitext(arquivo.name)[1].lower().replace('.', '')
            
            # Valida tipo de arquivo
            tipos_suportados = ['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'bmp']
            if tipo_arquivo not in tipos_suportados:
                return Response(
                    {'error': f'Tipo de arquivo não suportado. Use: {", ".join(tipos_suportados)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Gera ID único para a tarefa
            task_id = str(uuid.uuid4())
            
            # Inicia o rastreamento do progresso imediatamente para evitar race condition
            progress_tracker.start_progress(task_id)
            
            # Salva arquivo temporariamente (compatível com Windows)
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f'{task_id}_{arquivo.name}')
            print(f"💾 Salvando arquivo temporário em: {temp_path}")
            
            with open(temp_path, 'wb+') as temp_file:
                for chunk in arquivo.chunks():
                    temp_file.write(chunk)
            
            # Inicia processamento em thread separada
            def processar_ocr():
                try:
                    print(f"🔄 Iniciando processamento OCR para task {task_id}")
                    texto_extraido = OCRService.extract_text(temp_path, tipo_arquivo, task_id)
                    print(f"✅ OCR concluído. Texto extraído: {len(texto_extraido)} caracteres")
                    
                    # ✅ CORREÇÃO PRINCIPAL - COMPLETAR O PROGRESSO
                    with progress_tracker._lock:
                        if task_id in progress_tracker._progress_data:
                            progress_tracker._progress_data[task_id]['resultado'] = {
                                'texto': texto_extraido,
                                'nome_arquivo': arquivo.name,
                                'tipo_arquivo': tipo_arquivo,
                                'tamanho': arquivo.size
                            }
                            print(f"💾 Resultado salvo no tracker para task {task_id}")
                    
                    # 🚀 MARCAR COMO CONCLUÍDO
                    progress_tracker.complete_progress(task_id, success=True, message="OCR concluído com sucesso!")
                    print(f"✅ Progresso marcado como concluído para task {task_id}")
                    
                except Exception as e:
                    print(f"❌ Erro no processamento OCR: {str(e)}")
                    progress_tracker.complete_progress(task_id, False, f"Erro: {str(e)}")
                finally:
                    # Remove arquivo temporário
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        print(f"🗑️ Arquivo temporário removido: {temp_path}")
            
            # Inicia thread de processamento
            thread = threading.Thread(target=processar_ocr)
            thread.daemon = True
            thread.start()
            
            # Retorna task_id para acompanhamento
            return Response({
                'success': True,
                'task_id': task_id,
                'message': 'Processamento iniciado. Use o task_id para acompanhar o progresso.'
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            return Response(
                {'error': f'Erro ao iniciar processamento OCR: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DocumentoOCRWithMarginsView(views.APIView):
    permission_classes = [HasPermission]
    required_permission = 'escanear_documento'

    def post(self, request):
        if 'arquivo' not in request.FILES:
            return Response({'error': 'Arquivo não fornecido'}, status=status.HTTP_400_BAD_REQUEST)
        if 'margins' not in request.data:
            return Response({'error': 'Margens não fornecidas'}, status=status.HTTP_400_BAD_REQUEST)

        arquivo = request.FILES['arquivo']
        try:
            import json
            margins = json.loads(request.data['margins'])
        except (json.JSONDecodeError, TypeError):
            return Response({'error': 'Formato das margens inválido'}, status=status.HTTP_400_BAD_REQUEST)

        tipo_arquivo = os.path.splitext(arquivo.name)[1].lower().replace('.', '')
        if tipo_arquivo != 'pdf':
            return Response({'error': 'Seleção de margens só é suportada para arquivos PDF.'}, status=status.HTTP_400_BAD_REQUEST)

        task_id = str(uuid.uuid4())
        progress_tracker.start_progress(task_id)

        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f'{task_id}_{arquivo.name}')
        with open(temp_path, 'wb+') as temp_file:
            for chunk in arquivo.chunks():
                temp_file.write(chunk)

        def processar_ocr_margens():
            try:
                texto_extraido = OCRService.extract_text_with_margins(temp_path, task_id, margins)
                print(f"✅ OCR com margens concluído: {len(texto_extraido)} caracteres")
                
                # ✅ CORREÇÃO PRINCIPAL - COMPLETAR O PROGRESSO
                with progress_tracker._lock:
                    if task_id in progress_tracker._progress_data:
                        progress_tracker._progress_data[task_id]['resultado'] = {
                            'texto': texto_extraido,
                            'nome_arquivo': arquivo.name,
                            'tipo_arquivo': tipo_arquivo,
                            'tamanho': arquivo.size
                        }
                        print(f"💾 Resultado salvo no tracker para task {task_id}")
                
                # 🚀 MARCAR COMO CONCLUÍDO
                progress_tracker.complete_progress(task_id, success=True, message="OCR concluído com sucesso!")
                print(f"✅ Progresso marcado como concluído para task {task_id}")
                
            except Exception as e:
                print(f"❌ Erro no OCR com margens: {str(e)}")
                progress_tracker.complete_progress(task_id, False, f"Erro: {str(e)}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        thread = threading.Thread(target=processar_ocr_margens)
        thread.daemon = True
        thread.start()

        return Response({
            'success': True,
            'task_id': task_id,
            'message': 'Processamento com margens iniciado. Use o task_id para acompanhar.'
        }, status=status.HTTP_202_ACCEPTED)

class DocumentoOCRProgressView(views.APIView):
    """
    View para consultar progresso de processamento OCR
    GET: Retorna status atual do processamento
    """
#    permission_classes = [HasPermission]
#   required_permission = 'criar_documento'
    
    def get(self, request, task_id):
        """
        Consulta progresso de uma tarefa de OCR
        """
        try:
            progress_data = progress_tracker.get_progress(task_id)
            
            # ✅ DEBUG DETALHADO
            print(f"🔍 RECEBIDO do tracker para {task_id}: {progress_data}")
            
            if not progress_data:
                print(f"❌ Task {task_id} não encontrada no tracker")
                return Response({
                    'error': 'Tarefa não encontrada ou expirada',
                    'task_id': task_id,
                    'status': 'not_found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Se concluído com sucesso, inclui o resultado
            response_data = {
                'task_id': task_id,
                'status': progress_data['status'],
                'current_page': progress_data['current_page'],
                'total_pages': progress_data['total_pages'],
                'percentage': progress_data['percentage'],
                'message': progress_data['message'],
                'elapsed_seconds': progress_data['elapsed_seconds']
            }
            
            # ✅ VERIFICAR SE TEM RESULTADO
            if progress_data['status'] == 'concluido' and 'resultado' in progress_data:
                response_data['resultado'] = progress_data['resultado']
                print(f"📤 INCLUINDO resultado na resposta: {len(str(progress_data['resultado']))}")
                print(f"📤 Texto extraído: {len(progress_data['resultado'].get('texto', ''))} chars")
            else:
                print(f"❌ SEM resultado - status: {progress_data['status']}, tem resultado: {'resultado' in progress_data}")
            
            print(f"📤 ENVIANDO resposta: {len(str(response_data))} chars, status: {response_data['status']}")
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ ERRO na DocumentoOCRProgressView: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return Response({
                'error': f'Erro ao consultar progresso: {str(e)}',
                'task_id': task_id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class DocumentoOCRView(views.APIView):
    """
    View para processar OCR em documentos
    POST: Faz upload de documento e extrai texto via OCR
    """
    permission_classes = [HasPermission]
    required_permission = 'escanear_documento'
    
    def post(self, request):
        """
        Processa OCR em um documento enviado
        """
        try:
            # Validação
            if 'arquivo' not in request.FILES:
                return Response(
                    {'error': 'Arquivo não fornecido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            arquivo = request.FILES['arquivo']
            tipo_arquivo = os.path.splitext(arquivo.name)[1].lower().replace('.', '')
            
            # Valida tipo de arquivo
            tipos_suportados = ['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'bmp']
            if tipo_arquivo not in tipos_suportados:
                return Response(
                    {'error': f'Tipo de arquivo não suportado. Use: {", ".join(tipos_suportados)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Salva arquivo temporariamente
            temp_path = f'/tmp/{arquivo.name}'
            with open(temp_path, 'wb+') as temp_file:
                for chunk in arquivo.chunks():
                    temp_file.write(chunk)
            
            # Processa OCR
            texto_extraido = OCRService.extract_text(temp_path, tipo_arquivo)
            
            # Remove arquivo temporário
            os.remove(temp_path)
            
            # Retorna resultado
            return Response({
                'success': True,
                'texto': texto_extraido,
                'nome_arquivo': arquivo.name,
                'tipo_arquivo': tipo_arquivo,
                'tamanho': arquivo.size
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Erro ao processar OCR: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentoSalvarOCRView(views.APIView):
    """
    View para salvar documento com texto OCR sem análise IA
    POST: Salva documento com texto extraído
    """
    permission_classes = [HasPermission]
    required_permission = 'criar_documento'
    
    def post(self, request):
        """
        Salva um documento com texto OCR extraído
        """
        from clientes.models import Cliente
        
        texto = request.data.get('texto')
        cliente_id = request.data.get('cliente_id')
        titulo = request.data.get('titulo')
        
        # Validações
        if not texto:
            return Response(
                {'error': 'Texto é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obter dados do usuário autenticado
        usuario = request.user
        escritorio = usuario.perfil.escritorio
        
        # Obter cliente (opcional)
        cliente = None
        if cliente_id:
            try:
                cliente = Cliente.objects.get(id=cliente_id, escritorio=escritorio)
            except Cliente.DoesNotExist:
                return Response(
                    {'error': 'Cliente não encontrado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Define título padrão se não fornecido
        if not titulo:
            titulo = f'Documento Escaneado - {timezone.now().strftime("%d/%m/%Y %H:%M")}'
        
        # Cria documento com texto extraído
        documento = Documento.objects.create(
            escritorio=escritorio,
            cliente=cliente,
            titulo=titulo,
            nome_original='documento_escaneado.pdf',
            tipo_arquivo='pdf',
            tamanho=len(texto),
            texto_extraido=texto,
            usuario_upload=usuario
        )
        
        return Response({
            'success': True,
            'message': 'Documento salvo com sucesso',
            'documento_id': documento.id,
            'titulo': documento.titulo
        }, status=status.HTTP_201_CREATED)


class DocumentoAnaliseIAListCreateView(generics.ListCreateAPIView):
    """
    View para listar e criar análises de IA
    GET: Lista análises do escritório
    POST: Cria nova análise a partir de texto
    """
    permission_classes = [HasPermission]
    required_permission = 'visualizar_analise_ia'
    
    def get_permissions(self):
        """Retorna permissões baseadas no método HTTP"""
        if self.request.method == 'POST':
            self.required_permission = 'solicitar_analise_ia'
        else:
            self.required_permission = 'visualizar_analise_ia'
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DocumentoAnaliseIACreateSerializer
        return DocumentoAnaliseIAListSerializer
    
    def get_queryset(self):
        """Retorna análises do escritório do usuário"""
        return DocumentoAnaliseIA.objects.filter(
            escritorio=self.request.user.perfil.escritorio
        ).select_related('documento', 'usuario').order_by('-data_solicitacao')
    
    def create(self, request, *args, **kwargs):
        """
        Cria uma análise de IA a partir de documento existente ou texto
        """
        from clientes.models import Cliente
        
        documento_id = request.data.get('documento_id')
        texto = request.data.get('texto')
        tipo_analise = request.data.get('tipo_analise', 'resumo')
        prompt_personalizado = request.data.get('prompt_personalizado')
        modelo_ia = request.data.get('modelo_ia', 'gpt-5-nano-2025-08-07')
        cliente_id = request.data.get('cliente_id')
        
        # Obter dados do usuário autenticado
        usuario = request.user
        escritorio = usuario.perfil.escritorio
        
        # Se foi fornecido documento_id, usa o documento existente
        if documento_id:
            try:
                documento = Documento.objects.get(
                    id=documento_id, 
                    escritorio=escritorio
                )
                print(f"✅ Usando documento existente: {documento.titulo} (ID: {documento.id})")
            except Documento.DoesNotExist:
                return Response(
                    {'error': 'Documento não encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Se não foi fornecido documento_id, cria um novo documento a partir do texto
            if not texto:
                return Response(
                    {'error': 'Texto ou documento_id é obrigatório'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obter cliente
            if cliente_id:
                try:
                    cliente = Cliente.objects.get(id=cliente_id, escritorio=escritorio)
                except Cliente.DoesNotExist:
                    return Response(
                        {'error': 'Cliente não encontrado'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                # Se não foi informado cliente_id, pega o primeiro do escritório
                cliente = Cliente.objects.filter(escritorio=escritorio).first()
                if not cliente:
                    return Response(
                        {'error': 'Nenhum cliente encontrado no escritório. Por favor, cadastre um cliente primeiro.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Cria documento temporário
            documento = Documento.objects.create(
                escritorio=escritorio,
                cliente=cliente,
                titulo=f'Documento Escaneado - {timezone.now().strftime("%d/%m/%Y %H:%M")}',
                nome_original='documento_escaneado.pdf',
                tipo_arquivo='pdf',
                tamanho=len(texto),
                texto_extraido=texto,
                usuario_upload=usuario
            )
            print(f"📝 Documento temporário criado: {documento.titulo} (ID: {documento.id})")
        
        # Validações
        if tipo_analise == 'personalizado' and not prompt_personalizado:
            return Response(
                {'error': 'Prompt personalizado é obrigatório para análise personalizada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cria análise
        analise = DocumentoAnaliseIA.objects.create(
            escritorio=escritorio,
            documento=documento,
            usuario=usuario,
            tipo_analise=tipo_analise,
            prompt_personalizado=prompt_personalizado,
            modelo_ia=modelo_ia,
            status='pendente'
        )
        print(f"🔬 Análise criada (ID: {analise.id}) para documento: {documento.titulo}")
        
        # Processa análise
        try:
            self._processar_analise(analise)
        except Exception as e:
            analise.status = 'erro'
            analise.mensagem_erro = str(e)
            analise.save()
        
        # Recarrega análise do banco para ter dados atualizados
        analise.refresh_from_db()
        
        # Retorna análise criada
        serializer = DocumentoAnaliseIADetailSerializer(analise)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @transaction.atomic
    def _processar_analise(self, analise: DocumentoAnaliseIA):
        """
        Processa a análise com IA
        """
        # Marca como processando
        analise.status = 'processando'
        analise.save()
        
        # Obtém texto do documento
        documento = analise.documento
        if not documento.texto_extraido:
            # Se não tem texto, faz OCR primeiro
            arquivo_path = documento.arquivo.path
            texto = OCRService.extract_text(arquivo_path, documento.tipo_arquivo)
            documento.texto_extraido = texto
            documento.save()
        else:
            texto = documento.texto_extraido
        
        # Obtém API Key do escritório
        api_key = analise.escritorio.openai_api_key
        if not api_key:
            raise Exception("API Key da OpenAI não configurada no escritório")
        
        # Processa com IA
        ai_service = AIAnalysisService(api_key=api_key)
        resultado = ai_service.analyze_document(
            texto=texto,
            tipo_analise=analise.tipo_analise,
            prompt_personalizado=analise.prompt_personalizado,
            modelo=analise.modelo_ia
        )
        
        # 🐛 DEBUG
        print(f"🔍 Resultado da IA:")
        print(f"  - Status: {resultado.get('status')}")
        print(f"  - Resultado chars: {len(resultado.get('resultado', ''))}")
        print(f"  - Tokens: {resultado.get('tokens_usados')}")
        print(f"  - Custo: {resultado.get('custo_estimado')}")
        print(f"  - Erro: {resultado.get('mensagem_erro')}")
        
        # Atualiza análise
        try:
            resultado_texto = resultado['resultado']
            print(f"🔍 Salvando resultado com {len(resultado_texto)} caracteres")
            
            analise.resultado = resultado_texto
            analise.tokens_usados = resultado['tokens_usados']
            analise.custo_estimado = resultado['custo_estimado']
            
            # O campo tempo_processamento é DurationField, então deve receber timedelta
            analise.tempo_processamento = resultado['tempo_processamento']
                
            analise.modelo_ia = resultado['modelo_ia']
            analise.status = resultado['status']
            analise.data_conclusao = timezone.now()
            
            if resultado.get('mensagem_erro'):
                analise.mensagem_erro = resultado['mensagem_erro']
            
            analise.save()
            print(f"✅ Análise salva com sucesso")
            
            # Recarrega do banco para verificar
            analise.refresh_from_db()
            print(f"🔍 Após reload - Resultado chars: {len(analise.resultado) if analise.resultado else 0}")
            
        except Exception as save_error:
            print(f"❌ Erro ao salvar análise: {str(save_error)}")
            analise.status = 'erro'
            analise.mensagem_erro = f"Erro ao salvar: {str(save_error)}"
            analise.save()
            raise


class DocumentoAnaliseIADetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View para detalhes, atualização e exclusão de análises de IA
    GET: Retorna detalhes da análise
    PUT/PATCH: Atualiza análise
    DELETE: Remove análise
    """
    serializer_class = DocumentoAnaliseIADetailSerializer
    permission_classes = [HasPermission]
    required_permission = 'visualizar_analise_ia'
    
    def get_queryset(self):
        """Retorna análises do escritório do usuário"""
        return DocumentoAnaliseIA.objects.filter(
            escritorio=self.request.user.perfil.escritorio
        ).select_related('documento', 'usuario').order_by('-data_solicitacao')


class DocumentoAnaliseIAReprocessView(views.APIView):
    """
    View para reprocessar uma análise de IA
    POST: Reprocessa a análise
    """
    permission_classes = [HasPermission]
    required_permission = 'solicitar_analise_ia'
    
    def post(self, request, pk):
        """Reprocessa uma análise existente"""
        try:
            analise = DocumentoAnaliseIA.objects.get(
                pk=pk,
                escritorio=request.user.perfil.escritorio
            )
            
            # Reseta status
            analise.status = 'pendente'
            analise.resultado = ''
            analise.mensagem_erro = ''
            analise.save()
            
            # Reprocessa
            view = DocumentoAnaliseIAListCreateView()
            view.request = request
            view._processar_analise(analise)
            
            # Retorna análise atualizada
            serializer = DocumentoAnaliseIADetailSerializer(analise)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except DocumentoAnaliseIA.DoesNotExist:
            return Response(
                {'error': 'Análise não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Erro ao reprocessar análise: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )