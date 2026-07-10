"""
Views para o Sistema de Processos Judiciais
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from .models import Processo, Parte, Movimentacao, Prazo, Audiencia
from .serializers import (
    ProcessoListSerializer, ProcessoDetailSerializer, ProcessoCreateSerializer,
    ParteSerializer, MovimentacaoSerializer, PrazoSerializer, AudienciaSerializer
)
from .permissions import (
    ProcessoPermission, PartePermission, MovimentacaoPermission,
    PrazoPermission, AudienciaPermission
)
from .datajud_service import DataJudService
from documentos.ai_service import AIAnalysisService
import json


class ProcessoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de processos
    """
    permission_classes = [IsAuthenticated, ProcessoPermission]
    
    def get_queryset(self):
        """Filtra processos pelo escritório do usuário"""
        escritorio = self.request.user.perfil.escritorio
        queryset = Processo.objects.filter(escritorio=escritorio)
        
        # Filtros opcionais
        status_filter = self.request.query_params.get('status', None)
        tipo_filter = self.request.query_params.get('tipo', None)
        cliente_filter = self.request.query_params.get('cliente', None)
        advogado_filter = self.request.query_params.get('advogado', None)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if tipo_filter:
            queryset = queryset.filter(tipo=tipo_filter)
        if cliente_filter:
            queryset = queryset.filter(cliente_principal_id=cliente_filter)
        if advogado_filter:
            queryset = queryset.filter(advogado_responsavel_id=advogado_filter)
        
        return queryset.select_related('cliente_principal', 'advogado_responsavel', 'escritorio')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProcessoListSerializer
        elif self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return ProcessoCreateSerializer
        return ProcessoDetailSerializer
    
    def perform_create(self, serializer):
        """Define o escritório e usuário de cadastro"""
        processo = serializer.save(
            escritorio=self.request.user.perfil.escritorio,
            usuario_cadastro=self.request.user
        )
        
        # Se veio dados da API PJe, cria partes, movimentações, prazos e audiências automaticamente
        dados_api = self.request.data.get('_dados_api_pje')
        
        if dados_api:
            self._criar_dados_relacionados(processo, dados_api)
    
    def _criar_dados_relacionados(self, processo, dados_api):
        """
        Cria automaticamente partes, movimentações, prazos e audiências
        a partir dos dados da API PJe
        """
        from datetime import datetime
        
        print(f"\n🔧 Criando dados relacionados ao processo {processo.numero_processo}")
        
        # 1. Criar Partes (extraídas dos destinatários da API)
        # destinatarios = partes do processo (autor, réu)
        # destinatarioadvogados = advogados (não usado ainda)
        partes_info = dados_api.get('partes_info', {})
        
        autor = partes_info.get('autor', '').strip()
        if autor:
            Parte.objects.create(
                processo=processo,
                tipo_parte='autor',
                tipo_pessoa='fisica',  # Assume física, pode ajustar depois
                nome=autor,
                representado_escritorio=False  # Usuário pode marcar depois
            )
            print(f"   👤 Parte criada: Autor - {autor}")
        
        reu = partes_info.get('reu', '').strip()
        if reu:
            Parte.objects.create(
                processo=processo,
                tipo_parte='reu',
                tipo_pessoa='juridica',  # Assume jurídica, pode ajustar depois  
                nome=reu,
                representado_escritorio=False
            )
            print(f"   👤 Parte criada: Réu - {reu}")
        
        # 2. Criar Movimentações
        movimentacoes = dados_api.get('movimentacoes_list', [])
        for mov_data in movimentacoes:
            try:
                data_mov = datetime.fromisoformat(mov_data['data_movimentacao'].replace('Z', '+00:00'))
                Movimentacao.objects.create(
                    processo=processo,
                    data_movimentacao=data_mov,
                    tipo=mov_data['tipo'],
                    descricao=mov_data['descricao'],
                    importante=mov_data.get('importante', False),
                    lido=False,
                    cadastrado_por=self.request.user
                )
            except Exception as e:
                print(f"   ⚠️ Erro ao criar movimentação: {e}")
        
        print(f"   📝 {len(movimentacoes)} movimentações criadas")
        
        # 3. Criar Prazos
        prazos = dados_api.get('prazos_list', [])
        for prazo_data in prazos:
            try:
                Prazo.objects.create(
                    processo=processo,
                    descricao=prazo_data['descricao'],
                    data_inicio=prazo_data['data_inicio'],
                    data_limite=prazo_data['data_limite'],
                    prazo_dias=prazo_data['prazo_dias'],
                    status=prazo_data['status'],
                    prioridade=prazo_data['prioridade'],
                    responsavel=self.request.user
                )
            except Exception as e:
                print(f"   ⚠️ Erro ao criar prazo: {e}")
        
        print(f"   ⏰ {len(prazos)} prazos criados")
        
        # 4. Criar Audiências
        audiencias = dados_api.get('audiencias_list', [])
        for aud_data in audiencias:
            try:
                Audiencia.objects.create(
                    processo=processo,
                    tipo=aud_data['tipo'],
                    data_hora=aud_data['data_hora'],
                    pauta=aud_data['pauta'],
                    status=aud_data['status'],
                    alertar=aud_data.get('alertar', True),
                    cadastrado_por=self.request.user
                )
            except Exception as e:
                print(f"   ⚠️ Erro ao criar audiência: {e}")
        
        print(f"   🎤 {len(audiencias)} audiências criadas")
        print(f"✅ Dados relacionados criados com sucesso!\n")
    
    @action(detail=True, methods=['get'])
    def movimentacoes(self, request, pk=None):
        """Retorna todas as movimentações do processo"""
        processo = self.get_object()
        movimentacoes = processo.movimentacoes.all()
        serializer = MovimentacaoSerializer(movimentacoes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def prazos(self, request, pk=None):
        """Retorna todos os prazos do processo"""
        processo = self.get_object()
        prazos = processo.prazos.all()
        serializer = PrazoSerializer(prazos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def audiencias(self, request, pk=None):
        """Retorna todas as audiências do processo"""
        processo = self.get_object()
        audiencias = processo.audiencias.all()
        serializer = AudienciaSerializer(audiencias, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Retorna estatísticas dos processos do escritório"""
        escritorio = request.user.perfil.escritorio
        processos = Processo.objects.filter(escritorio=escritorio)
        
        stats = {
            'total': processos.count(),
            'por_status': {},
            'por_tipo': {},
            'prazos_proximos': Prazo.objects.filter(
                processo__escritorio=escritorio,
                status='pendente',
                data_limite__lte=timezone.now().date() + timedelta(days=7)
            ).count(),
            'audiencias_proximas': Audiencia.objects.filter(
                processo__escritorio=escritorio,
                status='agendada',
                data_hora__lte=timezone.now() + timedelta(days=7)
            ).count()
        }
        
        # Conta por status
        for status_key, status_label in Processo.STATUS_CHOICES:
            stats['por_status'][status_key] = processos.filter(status=status_key).count()
        
        # Conta por tipo
        for tipo_key, tipo_label in Processo.TIPO_CHOICES:
            stats['por_tipo'][tipo_key] = processos.filter(tipo=tipo_key).count()
        
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def buscar_datajud(self, request):
        """
        Busca dados de um processo na API DataJud do TJSP
        Body: { "numero_processo": "0000832-35.2018.8.26.0000" }
        """
        numero_processo = request.data.get('numero_processo')
        
        if not numero_processo:
            return Response(
                {'erro': 'Número do processo é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cria instância do serviço (API key fixa do TJSP)
        datajud = DataJudService()
        
        # Busca o processo
        resultado = datajud.buscar_processo(numero_processo)
        
        if not resultado.get('sucesso'):
            return Response(
                {'erro': resultado.get('erro', 'Erro desconhecido')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Retorna os dados do processo E todos os dados relacionados
        response_data = resultado['dados'].copy()
        
        # Adiciona informações das partes, movimentações, prazos e audiências
        response_data['_partes_info'] = resultado.get('partes_info', {})
        response_data['_movimentacoes_list'] = resultado.get('movimentacoes_list', [])
        response_data['_prazos_list'] = resultado.get('prazos_list', [])
        response_data['_audiencias_list'] = resultado.get('audiencias_list', [])
        
        # Estatísticas
        response_data['_stats'] = {
            'total_movimentacoes': len(resultado.get('movimentacoes_list', [])),
            'total_prazos': len(resultado.get('prazos_list', [])),
            'total_audiencias': len(resultado.get('audiencias_list', []))
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def atualizar_movimentacoes(self, request, pk=None):
        """
        Atualiza movimentações de um processo específico buscando no PJe
        Compara com movimentações existentes e adiciona apenas as novas
        """
        processo = self.get_object()
        
        # Cria instância do serviço
        datajud = DataJudService()
        
        # Busca o processo no PJe
        resultado = datajud.buscar_processo(processo.numero_processo)
        
        if not resultado.get('sucesso'):
            return Response(
                {'erro': resultado.get('erro', 'Erro ao buscar no PJe')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Pega movimentações do PJe
        movimentacoes_pje = resultado.get('movimentacoes_list', [])
        
        if not movimentacoes_pje:
            return Response({
                'mensagem': 'Nenhuma movimentação encontrada no PJe',
                'novas': 0,
                'movimentacoes': []
            })
        
        # Pega movimentações existentes
        movimentacoes_existentes = processo.movimentacoes.all()
        
        # Cria conjunto de identificadores únicos (data + início da descrição)
        existentes_set = set()
        for mov in movimentacoes_existentes:
            # Normaliza data para apenas YYYY-MM-DD (sem hora)
            data_str = str(mov.data_movimentacao).split('T')[0].split(' ')[0]
            identificador = f"{data_str}|{mov.descricao[:100]}"
            existentes_set.add(identificador)
        
        print(f"\n🔍 Verificando movimentações:")
        print(f"📊 Existentes no banco: {len(movimentacoes_existentes)}")
        print(f"📥 Recebidas do PJe: {len(movimentacoes_pje)}")
        
        # Filtra apenas novas movimentações
        novas_movimentacoes = []
        for mov_data in movimentacoes_pje:
            # Normaliza data do PJe (remove timestamp se houver)
            data_pje = mov_data['data_movimentacao'].split('T')[0].split(' ')[0]
            identificador = f"{data_pje}|{mov_data['descricao'][:100]}"
            
            if identificador not in existentes_set:
                novas_movimentacoes.append(mov_data)
                print(f"✅ NOVA: {data_pje} - {mov_data['descricao'][:50]}...")
            else:
                print(f"⏭️ JÁ EXISTE: {data_pje} - {mov_data['descricao'][:50]}...")
        
        # Adiciona as novas movimentações
        movimentacoes_criadas = []
        print(f"\n📝 Adicionando {len(novas_movimentacoes)} novas movimentações...")
        for mov_data in novas_movimentacoes:
            movimentacao = Movimentacao.objects.create(
                processo=processo,
                **mov_data
            )
            movimentacoes_criadas.append(MovimentacaoSerializer(movimentacao).data)
            print(f"   ✅ Criada: {movimentacao.data_movimentacao} - {movimentacao.descricao[:50]}...")
        
        print(f"\n✅ Total de movimentações após atualização: {processo.movimentacoes.count()}")
        
        return Response({
            'mensagem': f'{len(movimentacoes_criadas)} nova(s) movimentação(ões) adicionada(s)',
            'novas': len(movimentacoes_criadas),
            'movimentacoes': movimentacoes_criadas
        })
    
    @action(detail=False, methods=['post'])
    def analisar_intimacao_ia(self, request):
        """
        Analisa texto de intimação com IA para extrair prazos e audiências
        Body: { 
            "texto": "conteúdo da intimação...", 
            "data_intimacao": "2025-11-02",
            "movimentacao_id": 123  # Opcional - ID da movimentação sendo analisada
        }
        """
        texto = request.data.get('texto', '').strip()
        data_intimacao = request.data.get('data_intimacao', '')
        movimentacao_id = request.data.get('movimentacao_id')
        
        if not texto:
            return Response(
                {'erro': 'Texto da intimação é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Se forneceu movimentacao_id, busca a movimentação
        movimentacao = None
        if movimentacao_id:
            try:
                movimentacao = Movimentacao.objects.get(id=movimentacao_id)
            except Movimentacao.DoesNotExist:
                return Response(
                    {'erro': 'Movimentação não encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        try:
            # Busca API key do escritório
            escritorio = request.user.perfil.escritorio
            api_key = escritorio.openai_api_key
            
            if not api_key:
                return Response(
                    {'erro': 'API Key da OpenAI não configurada para o escritório. Configure em Configurações do Sistema.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Cria o prompt para a IA
            prompt = f"""Analise a seguinte intimação/comunicação processual e extraia TODOS os prazos e audiências mencionados.

TEXTO DA INTIMAÇÃO:
{texto}

DATA DA INTIMAÇÃO: {data_intimacao if data_intimacao else 'não informada'}

Retorne APENAS um JSON válido (sem markdown, sem ```json) no seguinte formato:
{{
  "prazos": [
    {{
      "descricao": "Prazo para apresentar contestação",
      "prazo_dias": 15,
      "prioridade": "alta"
    }}
  ],
  "audiencias": [
    {{
      "tipo": "conciliacao",
      "descricao": "Audiência de conciliação",
      "data": "2025-11-15",
      "hora": "14:30"
    }}
  ]
}}

INSTRUÇÕES:
- Para prazos: extraia a AÇÃO (manifestar, contestar, informar, etc) e QUANTIDADE DE DIAS
- Prioridade: "alta" se <= 5 dias, "media" se <= 15 dias, "baixa" se > 15 dias
- Para audiências: identifique o TIPO (conciliacao, instrucao, inicial, julgamento, outras), DATA e HORA
- Se não houver data/hora específica na audiência, use null
- Se não encontrar prazos ou audiências, retorne arrays vazios []
"""
            
            # Chama a IA (usa GPT-5-mini para análise rápida)
            ai_service = AIAnalysisService(api_key=api_key)
            
            # O método correto é analyze_document, não analisar_documento
            resultado_dict = ai_service.analyze_document(
                texto=texto,
                tipo_analise='extracao_dados',
                prompt_personalizado=prompt,
                modelo='gpt-5-mini-2025-08-07'
            )
            
            resultado_ia = resultado_dict.get('resultado', '')
            
            if not resultado_ia:
                return Response(
                    {'erro': 'Erro ao processar análise com IA'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            print(f"📥 Resposta da IA: {resultado_ia[:500]}...")
            
            # Tenta fazer parse do JSON retornado pela IA
            try:
                # Remove possíveis marcadores de código
                resultado_limpo = resultado_ia.strip()
                if resultado_limpo.startswith('```'):
                    resultado_limpo = resultado_limpo.split('```')[1]
                    if resultado_limpo.startswith('json'):
                        resultado_limpo = resultado_limpo[4:]
                resultado_limpo = resultado_limpo.strip()
                
                dados = json.loads(resultado_limpo)
                
                # Processa prazos para adicionar datas calculadas
                from datetime import datetime, timedelta
                prazos_processados = []
                
                for prazo in dados.get('prazos', []):
                    try:
                        dias = prazo.get('prazo_dias', 0)
                        if data_intimacao:
                            data_inicio = datetime.fromisoformat(data_intimacao).date()
                        else:
                            data_inicio = timezone.now().date()
                        
                        data_limite = data_inicio + timedelta(days=dias + 1)
                        
                        prazos_processados.append({
                            'descricao': prazo.get('descricao', ''),
                            'data_inicio': data_inicio.isoformat(),
                            'data_limite': data_limite.isoformat(),
                            'prazo_dias': dias,
                            'status': 'pendente',
                            'prioridade': prazo.get('prioridade', 'media')
                        })
                    except Exception as e:
                        print(f"Erro ao processar prazo: {e}")
                        continue
                
                # Processa audiências
                audiencias_processadas = []
                for aud in dados.get('audiencias', []):
                    try:
                        # Monta data_hora se tiver data e hora
                        data_hora_str = None
                        if aud.get('data') and aud.get('hora'):
                            data_hora_str = f"{aud['data']}T{aud['hora']}:00"
                        elif aud.get('data'):
                            data_hora_str = f"{aud['data']}T00:00:00"
                        
                        audiencias_processadas.append({
                            'tipo': aud.get('tipo', 'outras'),
                            'data_hora': data_hora_str,
                            'pauta': aud.get('descricao', ''),
                            'status': 'agendada',
                            'alertar': True
                        })
                    except Exception as e:
                        print(f"Erro ao processar audiência: {e}")
                        continue
                
                # Salva o resultado na movimentação se foi fornecida
                if movimentacao:
                    from django.utils import timezone as tz
                    
                    # Converte dados para formato serializável (apenas strings e números)
                    resultado_serializavel = {
                        'total_prazos': len(prazos_processados),
                        'total_audiencias': len(audiencias_processadas),
                        'analisado_em': tz.now().isoformat(),
                        'prazos': [
                            {
                                'descricao': p.get('descricao', ''),
                                'prazo_dias': p.get('prazo_dias', 0),
                                'prioridade': p.get('prioridade', 'media'),
                                'data_inicio': str(p.get('data_inicio', '')),
                                'data_limite': str(p.get('data_limite', ''))
                            } for p in prazos_processados
                        ],
                        'audiencias': [
                            {
                                'tipo': a.get('tipo', 'outras'),
                                'descricao': a.get('pauta', ''),
                                'data_hora': str(a.get('data_hora', '')) if a.get('data_hora') else None
                            } for a in audiencias_processadas
                        ]
                    }
                    
                    movimentacao.analisada_ia = True
                    movimentacao.data_analise_ia = tz.now()
                    movimentacao.resultado_analise_ia = resultado_serializavel
                    movimentacao.analisada_por = request.user
                    movimentacao.save()
                    
                    print(f"✅ Análise salva na movimentação #{movimentacao.id}")
                
                return Response({
                    'sucesso': True,
                    'prazos': prazos_processados,
                    'audiencias': audiencias_processadas,
                    'total_prazos': len(prazos_processados),
                    'total_audiencias': len(audiencias_processadas),
                    'movimentacao_analisada': movimentacao.id if movimentacao else None
                })
                
            except json.JSONDecodeError as e:
                print(f"Erro ao fazer parse do JSON da IA: {e}")
                print(f"Resposta da IA: {resultado_ia}")
                return Response(
                    {'erro': 'IA retornou formato inválido', 'detalhes': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        except Exception as e:
            print(f"Erro na análise com IA: {e}")
            return Response(
                {'erro': f'Erro ao analisar intimação: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ParteViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de partes do processo"""
    permission_classes = [IsAuthenticated, PartePermission]
    serializer_class = ParteSerializer
    
    def get_queryset(self):
        """Filtra partes pelo escritório do usuário"""
        escritorio = self.request.user.perfil.escritorio
        return Parte.objects.filter(processo__escritorio=escritorio)
    
    @action(detail=False, methods=['post'])
    def importar_cliente(self, request):
        """
        Importa dados de um cliente para criar uma parte
        Body: { "cliente_id": 123, "processo_id": 456, "tipo_parte": "autor" }
        """
        from clientes.models import Cliente
        
        cliente_id = request.data.get('cliente_id')
        processo_id = request.data.get('processo_id')
        tipo_parte = request.data.get('tipo_parte', 'autor')
        
        if not cliente_id or not processo_id:
            return Response(
                {'error': 'cliente_id e processo_id são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verifica se o cliente existe e pertence ao escritório
        escritorio = request.user.perfil.escritorio
        cliente = get_object_or_404(Cliente, id=cliente_id, escritorio=escritorio)
        processo = get_object_or_404(Processo, id=processo_id, escritorio=escritorio)
        
        # Cria a parte com dados do cliente
        parte_data = {
            'processo': processo.id,
            'tipo_parte': tipo_parte,
            'cliente_vinculado': cliente.id
        }
        
        serializer = ParteSerializer(data=parte_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MovimentacaoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de movimentações"""
    permission_classes = [IsAuthenticated, MovimentacaoPermission]
    serializer_class = MovimentacaoSerializer
    
    def get_queryset(self):
        """Filtra movimentações pelo escritório do usuário"""
        escritorio = self.request.user.perfil.escritorio
        return Movimentacao.objects.filter(processo__escritorio=escritorio)
    
    def perform_create(self, serializer):
        """Define o usuário que cadastrou"""
        serializer.save(cadastrado_por=self.request.user)


class PrazoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de prazos"""
    permission_classes = [IsAuthenticated, PrazoPermission]
    serializer_class = PrazoSerializer
    
    def get_queryset(self):
        """Filtra prazos pelo escritório do usuário"""
        escritorio = self.request.user.perfil.escritorio
        queryset = Prazo.objects.filter(processo__escritorio=escritorio)
        
        # Filtro por status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filtro por responsável
        responsavel_filter = self.request.query_params.get('responsavel', None)
        if responsavel_filter:
            queryset = queryset.filter(responsavel_id=responsavel_filter)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def pendentes(self, request):
        """Retorna prazos pendentes ordenados por data"""
        escritorio = request.user.perfil.escritorio
        prazos = Prazo.objects.filter(
            processo__escritorio=escritorio,
            status='pendente'
        ).order_by('data_limite')
        
        serializer = self.get_serializer(prazos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def marcar_cumprido(self, request, pk=None):
        """Marca um prazo como cumprido"""
        prazo = self.get_object()
        prazo.status = 'cumprido'
        prazo.data_cumprimento = timezone.now()
        prazo.observacoes = request.data.get('observacoes', prazo.observacoes)
        prazo.save()
        
        serializer = self.get_serializer(prazo)
        return Response(serializer.data)


class AudienciaViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de audiências"""
    permission_classes = [IsAuthenticated, AudienciaPermission]
    serializer_class = AudienciaSerializer
    
    def get_queryset(self):
        """Filtra audiências pelo escritório do usuário"""
        escritorio = self.request.user.perfil.escritorio
        return Audiencia.objects.filter(processo__escritorio=escritorio)
    
    def perform_create(self, serializer):
        """Define o usuário que cadastrou"""
        serializer.save(cadastrado_por=self.request.user)
    
    @action(detail=False, methods=['get'])
    def proximas(self, request):
        """Retorna audiências futuras"""
        escritorio = request.user.perfil.escritorio
        audiencias = Audiencia.objects.filter(
            processo__escritorio=escritorio,
            status='agendada',
            data_hora__gte=timezone.now()
        ).order_by('data_hora')
        
        serializer = self.get_serializer(audiencias, many=True)
        return Response(serializer.data)
