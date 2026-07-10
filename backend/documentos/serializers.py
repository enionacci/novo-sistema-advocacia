"""
Serializers para API de Documentos
"""

from rest_framework import serializers
from .models import Categoria, Tag, Documento, DocumentoAnaliseIA
from django.contrib.auth import get_user_model

User = get_user_model()


class CategoriaSerializer(serializers.ModelSerializer):
    """
    Serializer para Categorias de Documentos
    """
    total_documentos = serializers.SerializerMethodField()

    class Meta:
        model = Categoria
        fields = [
            'id', 'nome', 'descricao', 'icone', 'cor',
            'ordem', 'ativo', 'data_criacao', 'total_documentos'
        ]
        read_only_fields = ['data_criacao']

    def get_total_documentos(self, obj):
        """Retorna o total de documentos desta categoria"""
        return obj.documentos.filter(ativo=True).count()

    def create(self, validated_data):
        """Adiciona o escritório automaticamente"""
        user = self.context['request'].user
        validated_data['escritorio'] = user.perfil.escritorio
        return super().create(validated_data)


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer para Tags
    """
    total_documentos = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'nome', 'cor', 'data_criacao', 'total_documentos']
        read_only_fields = ['data_criacao']

    def get_total_documentos(self, obj):
        """Retorna o total de documentos com esta tag"""
        return obj.documentos.filter(ativo=True).count()

    def create(self, validated_data):
        """Adiciona o escritório automaticamente"""
        user = self.context['request'].user
        validated_data['escritorio'] = user.perfil.escritorio
        return super().create(validated_data)


class DocumentoListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de documentos
    """
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    categoria_icone = serializers.CharField(source='categoria.icone', read_only=True)
    categoria_cor = serializers.CharField(source='categoria.cor', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome_completo', read_only=True)
    usuario_nome = serializers.SerializerMethodField()
    tags_list = TagSerializer(source='tags', many=True, read_only=True)
    tamanho_formatado = serializers.CharField(source='get_tamanho_formatado', read_only=True)
    arquivo_url = serializers.SerializerMethodField()

    class Meta:
        model = Documento
        fields = [
            'id', 'titulo', 'descricao', 'nome_original', 'tipo_arquivo',
            'tamanho', 'tamanho_formatado', 'data_upload', 'data_documento',
            'categoria', 'categoria_nome', 'categoria_icone', 'categoria_cor',
            'cliente', 'cliente_nome', 'tags_list', 'confidencial',
            'versao', 'visualizacoes', 'downloads', 'usuario_nome',
            'arquivo_url', 'ativo', 'texto_extraido'
        ]

    def get_usuario_nome(self, obj):
        """Retorna o nome do usuário que fez upload"""
        if obj.usuario_upload:
            return obj.usuario_upload.email or obj.usuario_upload.username
        return 'Sistema'

    def get_arquivo_url(self, obj):
        """Retorna a URL do endpoint de download com inline=true"""
        if obj.id:
            request = self.context.get('request')
            if request:
                # Constrói a URL para o endpoint de download
                from django.urls import reverse
                url = reverse('documento-download', kwargs={'pk': obj.id})
                absolute_url = request.build_absolute_uri(url)
                
                # Adiciona parâmetro inline
                final_url = f"{absolute_url}?inline=true"
                
                # Força HTTPS em produção
                if final_url.startswith('http://') and 'easypanel' in final_url:
                    final_url = final_url.replace('http://', 'https://')
                return final_url
        return None


class DocumentoDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para detalhes do documento
    """
    categoria_dados = CategoriaSerializer(source='categoria', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome_completo', read_only=True)
    usuario_nome = serializers.SerializerMethodField()
    tags_list = TagSerializer(source='tags', many=True, read_only=True)
    tamanho_formatado = serializers.CharField(source='get_tamanho_formatado', read_only=True)
    arquivo_url = serializers.SerializerMethodField()
    versoes_anteriores = serializers.SerializerMethodField()

    class Meta:
        model = Documento
        fields = [
            'id', 'titulo', 'descricao', 'nome_original', 'tipo_arquivo',
            'tamanho', 'tamanho_formatado', 'hash_md5', 'data_upload',
            'data_documento', 'data_atualizacao', 'categoria', 'categoria_dados',
            'cliente', 'cliente_nome', 'tags', 'tags_list', 'confidencial',
            'ativo', 'versao', 'documento_pai', 'visualizacoes', 'downloads',
            'usuario_nome', 'texto_extraido', 'arquivo_url', 'versoes_anteriores'
        ]
        read_only_fields = [
            'hash_md5', 'data_upload', 'data_atualizacao', 'visualizacoes',
            'downloads', 'nome_original', 'tipo_arquivo', 'tamanho'
        ]

    def get_usuario_nome(self, obj):
        """Retorna o nome do usuário que fez upload"""
        if obj.usuario_upload:
            return obj.usuario_upload.email or obj.usuario_upload.username
        return 'Sistema'

    def get_arquivo_url(self, obj):
        """Retorna a URL do arquivo com HTTPS se necessário"""
        if obj.arquivo:
            request = self.context.get('request')
            if request:
                url = request.build_absolute_uri(obj.arquivo.url)
                # Força HTTPS em produção
                if url.startswith('http://') and 'easypanel' in url:
                    url = url.replace('http://', 'https://')
                return url
        return None

    def get_versoes_anteriores(self, obj):
        """Retorna versões anteriores deste documento"""
        if obj.versoes.exists():
            return DocumentoListSerializer(
                obj.versoes.all(),
                many=True,
                context=self.context
            ).data
        return []


class DocumentoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de documentos (upload)
    """
    tags_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Documento
        fields = [
            'titulo', 'descricao', 'categoria', 'cliente', 'arquivo',
            'data_documento', 'confidencial', 'tags_ids'
        ]

    def create(self, validated_data):
        """
        Cria o documento e associa tags
        """
        tags_ids = validated_data.pop('tags_ids', [])
        user = self.context['request'].user
        
        # Adiciona escritório e usuário
        validated_data['escritorio'] = user.perfil.escritorio
        validated_data['usuario_upload'] = user
        
        # Cria o documento
        documento = Documento.objects.create(**validated_data)
        
        # Adiciona tags
        if tags_ids:
            tags = Tag.objects.filter(
                id__in=tags_ids,
                escritorio=user.perfil.escritorio
            )
            documento.tags.set(tags)
        
        return documento


class DocumentoUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização de metadados do documento
    """
    tags_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Documento
        fields = [
            'titulo', 'descricao', 'categoria', 'data_documento',
            'confidencial', 'ativo', 'tags_ids', 'texto_extraido'
        ]

    def update(self, instance, validated_data):
        """
        Atualiza o documento e suas tags
        """
        tags_ids = validated_data.pop('tags_ids', None)
        
        # Atualiza campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Atualiza tags se fornecidas
        if tags_ids is not None:
            user = self.context['request'].user
            tags = Tag.objects.filter(
                id__in=tags_ids,
                escritorio=user.perfil.escritorio
            )
            instance.tags.set(tags)
        
        return instance


class DocumentoAnaliseIAListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de análises de IA
    """
    documento_titulo = serializers.CharField(source='documento.titulo', read_only=True)
    usuario_nome = serializers.SerializerMethodField()
    tipo_analise_display = serializers.CharField(source='get_tipo_analise_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DocumentoAnaliseIA
        fields = [
            'id', 'documento', 'documento_titulo', 'tipo_analise',
            'tipo_analise_display', 'status', 'status_display',
            'data_solicitacao', 'data_conclusao', 'tempo_processamento',
            'usuario_nome', 'tokens_usados', 'custo_estimado', 'modelo_ia'
        ]
    
    def get_usuario_nome(self, obj):
        """Retorna o nome do usuário que solicitou"""
        if obj.usuario:
            return obj.usuario.email or obj.usuario.username
        return 'Sistema'


class DocumentoAnaliseIADetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para detalhes da análise de IA
    """
    documento_dados = DocumentoListSerializer(source='documento', read_only=True)
    usuario_nome = serializers.SerializerMethodField()
    tipo_analise_display = serializers.CharField(source='get_tipo_analise_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DocumentoAnaliseIA
        fields = [
            'id', 'documento', 'documento_dados', 'usuario', 'usuario_nome',
            'tipo_analise', 'tipo_analise_display', 'prompt_personalizado',
            'status', 'status_display', 'resultado', 'dados_estruturados',
            'data_solicitacao', 'data_conclusao', 'tempo_processamento',
            'mensagem_erro', 'tokens_usados', 'custo_estimado', 'modelo_ia'
        ]
        read_only_fields = [
            'data_solicitacao', 'data_conclusao', 'tempo_processamento',
            'mensagem_erro', 'tokens_usados', 'custo_estimado'
        ]
    
    def get_usuario_nome(self, obj):
        """Retorna o nome do usuário que solicitou"""
        if obj.usuario:
            return obj.usuario.email or obj.usuario.username
        return 'Sistema'


class DocumentoAnaliseIACreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de análises de IA
    """
    class Meta:
        model = DocumentoAnaliseIA
        fields = [
            'documento', 'tipo_analise', 'prompt_personalizado'
        ]
    
    def validate(self, data):
        """Validações customizadas"""
        # Se for análise personalizada, prompt é obrigatório
        if data.get('tipo_analise') == 'personalizado' and not data.get('prompt_personalizado'):
            raise serializers.ValidationError({
                'prompt_personalizado': 'Prompt personalizado é obrigatório para análise personalizada'
            })
        
        return data
    
    def create(self, validated_data):
        """
        Cria a análise de IA
        """
        user = self.context['request'].user
        
        # Adiciona escritório e usuário
        validated_data['escritorio'] = user.perfil.escritorio
        validated_data['usuario'] = user
        validated_data['status'] = 'pendente'
        
        # Cria a análise
        analise = DocumentoAnaliseIA.objects.create(**validated_data)
        
        return analise
