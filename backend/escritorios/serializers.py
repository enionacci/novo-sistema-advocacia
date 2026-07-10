# escritorios/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Escritorio, PerfilUsuario, Convite, Papel, Permissao


class PermissaoSerializer(serializers.ModelSerializer):
    """Serializer para Permissões"""
    class Meta:
        model = Permissao
        fields = ['id', 'nome', 'codename']


class ConviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Convite
        fields = ['id', 'email', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']

class AcceptInvitationSerializer(serializers.Serializer):
    """Serializer para aceitar um convite e criar um novo usuário."""
    token = serializers.UUIDField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

class InvitationDetailSerializer(serializers.ModelSerializer):
    escritorio_nome = serializers.CharField(source='escritorio.nome', read_only=True)

    class Meta:
        model = Convite
        fields = ['email', 'escritorio_nome']

class UserSerializerForPerfil(serializers.ModelSerializer):
    """Serializer simplificado para o User, usado dentro do Perfil."""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class PerfilUsuarioSerializer(serializers.ModelSerializer):
    """Serializer para o Perfil do Usuário, incluindo dados do usuário."""
    user = UserSerializerForPerfil(read_only=True)
    papeis = serializers.StringRelatedField(many=True, read_only=True)
    papel_principal = serializers.SerializerMethodField()
    permissoes = serializers.SerializerMethodField()
    
    class Meta:
        model = PerfilUsuario
        fields = ['id', 'user', 'papeis', 'papel_principal', 'permissoes']
    
    def get_papel_principal(self, obj):
        """Retorna o nome do primeiro papel (papel principal)"""
        primeiro_papel = obj.papeis.first()
        return primeiro_papel.nome if primeiro_papel else None
    
    def get_permissoes(self, obj):
        """Retorna todas as permissões do usuário (de todos os papéis)"""
        # Coleta todas as permissões de todos os papéis
        permissoes_set = set()
        for papel in obj.papeis.all():
            for permissao in papel.permissoes.all():
                permissoes_set.add(permissao)
        
        # Serializa as permissões únicas
        return PermissaoSerializer(permissoes_set, many=True).data


class UserWithProfileSerializer(serializers.ModelSerializer):
    """
    Serializer customizado para o endpoint /users/me/ do Djoser
    Inclui o perfil com permissões
    """
    perfil = PerfilUsuarioSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_superuser', 'perfil']
        read_only_fields = ['id', 'is_superuser']


class PermissaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permissao
        fields = ['id', 'nome', 'codename']

class PapelSerializer(serializers.ModelSerializer):
    permissoes = serializers.PrimaryKeyRelatedField(queryset=Permissao.objects.all(), many=True)

    class Meta:
        model = Papel
        fields = ['id', 'nome', 'permissoes']
        read_only_fields = ['escritorio']

class PerfilUsuarioPapelUpdateSerializer(serializers.ModelSerializer):
    papeis = serializers.PrimaryKeyRelatedField(queryset=Papel.objects.all(), many=True)

    class Meta:
        model = PerfilUsuario
        fields = ['papeis']

class EscritorioSerializer(serializers.ModelSerializer):
    """Serializer para o Escritório, incluindo a lista de membros."""
    membros = PerfilUsuarioSerializer(many=True, read_only=True)
    # Campo para receber a chave de API, mas nunca enviá-la de volta.
    openai_api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    # Campo logo com URL completa (leitura)
    logo_url = serializers.SerializerMethodField()
    # Campo para receber o upload do logo (escrita)
    logo = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Escritorio
        fields = [
            'id', 'nome', 'data_criacao', 'membros', 'openai_api_key',
            'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep',
            'logo', 'logo_url'
        ]
        read_only_fields = ['data_criacao', 'membros']

    def get_logo_url(self, obj):
        """Retorna a URL completa do logo se existir."""
        if obj.logo:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None

    def update(self, instance, validated_data):
        """Trata o upload do logo separadamente."""
        logo_file = validated_data.pop('logo', None)
        if logo_file:
            # Remove logo antigo se existir
            if instance.logo:
                instance.logo.delete(save=False)
            instance.logo = logo_file
        return super().update(instance, validated_data)
