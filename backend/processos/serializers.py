"""
Serializers para o Sistema de Processos Judiciais
"""

from rest_framework import serializers
from .models import Processo, Parte, Movimentacao, Prazo, Audiencia
from clientes.serializers import ClienteSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer simplificado para usuários"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class ParteSerializer(serializers.ModelSerializer):
    """Serializer para partes do processo"""
    cliente_vinculado_detalhes = ClienteSerializer(source='cliente_vinculado', read_only=True)
    tipo_parte_display = serializers.CharField(source='get_tipo_parte_display', read_only=True)
    tipo_pessoa_display = serializers.CharField(source='get_tipo_pessoa_display', read_only=True)
    
    class Meta:
        model = Parte
        fields = [
            'id', 'processo', 'tipo_parte', 'tipo_parte_display', 
            'tipo_pessoa', 'tipo_pessoa_display',
            'cliente_vinculado', 'cliente_vinculado_detalhes',
            'nome', 'cpf_cnpj',
            'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep',
            'advogado_nome', 'advogado_oab',
            'representado_escritorio'
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        """
        Se cliente_vinculado foi fornecido, importa dados automaticamente
        """
        cliente = validated_data.get('cliente_vinculado')
        if cliente and not validated_data.get('nome'):
            # O método save() do model já faz isso, mas garantimos aqui também
            validated_data['nome'] = cliente.nome_completo or cliente.razao_social
            validated_data['cpf_cnpj'] = cliente.cpf or cliente.cnpj
            validated_data['tipo_pessoa'] = 'fisica' if cliente.cpf else 'juridica'
            validated_data['logradouro'] = cliente.logradouro
            validated_data['numero'] = cliente.numero
            validated_data['complemento'] = cliente.complemento
            validated_data['bairro'] = cliente.bairro
            validated_data['cidade'] = cliente.cidade
            validated_data['estado'] = cliente.estado
            validated_data['cep'] = cliente.cep
            validated_data['representado_escritorio'] = True
        
        return super().create(validated_data)


class MovimentacaoSerializer(serializers.ModelSerializer):
    """Serializer para movimentações do processo"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    cadastrado_por_detalhes = UserSerializer(source='cadastrado_por', read_only=True)
    analisada_por_detalhes = UserSerializer(source='analisada_por', read_only=True)
    
    class Meta:
        model = Movimentacao
        fields = [
            'id', 'processo', 'data_movimentacao', 'tipo', 'tipo_display',
            'descricao', 'documento', 'numero_protocolo',
            'gera_prazo', 'prazo_dias', 'data_limite',
            'data_cadastro', 'cadastrado_por', 'cadastrado_por_detalhes',
            'importante', 'lido',
            'analisada_ia', 'data_analise_ia', 'resultado_analise_ia', 'analisada_por', 'analisada_por_detalhes'
        ]
        read_only_fields = ['id', 'data_cadastro']


class PrazoSerializer(serializers.ModelSerializer):
    """Serializer para prazos processuais"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    prioridade_display = serializers.CharField(source='get_prioridade_display', read_only=True)
    responsavel_detalhes = UserSerializer(source='responsavel', read_only=True)
    processo_numero = serializers.CharField(source='processo.numero_processo', read_only=True)
    
    class Meta:
        model = Prazo
        fields = [
            'id', 'processo', 'processo_numero', 'movimentacao',
            'descricao', 'data_inicio', 'data_limite', 'prazo_dias',
            'status', 'status_display', 'prioridade', 'prioridade_display',
            'responsavel', 'responsavel_detalhes',
            'data_cumprimento', 'observacoes',
            'alertar_dias_antes', 'alerta_enviado'
        ]
        read_only_fields = ['id']


class AudienciaSerializer(serializers.ModelSerializer):
    """Serializer para audiências"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    cadastrado_por_detalhes = UserSerializer(source='cadastrado_por', read_only=True)
    processo_numero = serializers.CharField(source='processo.numero_processo', read_only=True)
    
    class Meta:
        model = Audiencia
        fields = [
            'id', 'processo', 'processo_numero',
            'tipo', 'tipo_display', 'data_hora', 'local', 'link_virtual',
            'status', 'status_display',
            'pauta', 'resultado', 'ata',
            'alertar', 'data_cadastro', 'cadastrado_por', 'cadastrado_por_detalhes'
        ]
        read_only_fields = ['id', 'data_cadastro']


class ProcessoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para lista de processos"""
    cliente_nome = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    posicao_cliente_display = serializers.CharField(source='get_posicao_cliente_display', read_only=True)
    advogado_responsavel_nome = serializers.SerializerMethodField()
    
    # Contadores
    total_movimentacoes = serializers.IntegerField(source='movimentacoes.count', read_only=True)
    prazos_pendentes = serializers.SerializerMethodField()
    proxima_audiencia = serializers.SerializerMethodField()
    
    class Meta:
        model = Processo
        fields = [
            'id', 'numero_processo', 'cliente_principal', 'cliente_nome',
            'tipo', 'tipo_display', 'classe', 'assunto',
            'posicao_cliente', 'posicao_cliente_display',
            'status', 'status_display',
            'tribunal', 'comarca', 'vara', 'uf',
            'data_distribuicao', 'data_audiencia',
            'valor_causa', 'advogado_responsavel', 'advogado_responsavel_nome',
            'total_movimentacoes', 'prazos_pendentes', 'proxima_audiencia',
            'sigilo', 'ativo', 'data_cadastro'
        ]
    
    def get_cliente_nome(self, obj):
        """Retorna o nome do cliente, seja PF ou PJ"""
        if obj.cliente_principal:
            return obj.cliente_principal.nome_completo or obj.cliente_principal.razao_social or 'Cliente sem nome'
        return 'Cliente não informado'
    
    def get_advogado_responsavel_nome(self, obj):
        if obj.advogado_responsavel:
            return f"{obj.advogado_responsavel.first_name} {obj.advogado_responsavel.last_name}".strip() or obj.advogado_responsavel.username
        return None
    
    def get_prazos_pendentes(self, obj):
        return obj.prazos.filter(status='pendente').count()
    
    def get_proxima_audiencia(self, obj):
        from django.utils import timezone
        proxima = obj.audiencias.filter(
            status='agendada',
            data_hora__gte=timezone.now()
        ).order_by('data_hora').first()
        
        if proxima:
            return {
                'id': proxima.id,
                'tipo': proxima.get_tipo_display(),
                'data_hora': proxima.data_hora
            }
        return None


class ProcessoDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes do processo"""
    cliente_principal_detalhes = ClienteSerializer(source='cliente_principal', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    posicao_cliente_display = serializers.CharField(source='get_posicao_cliente_display', read_only=True)
    
    # Relacionados
    partes = ParteSerializer(many=True, read_only=True)
    movimentacoes = MovimentacaoSerializer(many=True, read_only=True)
    prazos = PrazoSerializer(many=True, read_only=True)
    audiencias = AudienciaSerializer(many=True, read_only=True)
    
    # Usuários
    advogado_responsavel_detalhes = UserSerializer(source='advogado_responsavel', read_only=True)
    advogados_equipe_detalhes = UserSerializer(source='advogados_equipe', many=True, read_only=True)
    usuario_cadastro_detalhes = UserSerializer(source='usuario_cadastro', read_only=True)
    
    class Meta:
        model = Processo
        fields = '__all__'
        read_only_fields = ['id', 'data_cadastro', 'ultima_atualizacao']


class ProcessoCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de processos"""
    
    class Meta:
        model = Processo
        fields = [
            'id',  # Adiciona o ID para retornar na resposta
            'cliente_principal', 'numero_processo', 'numero_antigo',
            'tipo', 'classe', 'assunto', 'assuntos_secundarios',
            'posicao_cliente', 'tribunal', 'comarca', 'vara', 'uf',
            'data_distribuicao', 'data_citacao', 'status', 'tipo_distribuicao',
            'valor_causa', 'advogado_responsavel', 'link_consulta',
            'processo_origem', 'resumo', 'estrategia_juridica', 'observacoes',
            'sigilo', 'ativo'
        ]
        read_only_fields = ['id', 'escritorio', 'usuario_cadastro']
    
    def create(self, validated_data):
        # O escritorio e usuario_cadastro são definidos no perform_create da view
        return super().create(validated_data)
