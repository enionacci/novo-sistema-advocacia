"""
Models para o Sistema de Gerenciamento de Documentos

- Categoria: Tipos de documentos (RG, CPF, Contratos, etc)
- Tag: Tags personalizadas para organização
- Documento: Arquivo digital vinculado a um cliente
"""

import os
import hashlib
import unicodedata
import re
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from clientes.models import Cliente
from escritorios.models import Escritorio

User = get_user_model()


def sanitize_filename(filename):
    """
    Remove acentos e caracteres especiais do nome do arquivo
    Mantém apenas letras, números, pontos, hífens e underscores
    """
    # Separar nome e extensão
    name, ext = os.path.splitext(filename)
    
    # Remover acentos (NFD = Normalization Form Canonical Decomposition)
    name = unicodedata.normalize('NFD', name)
    name = name.encode('ascii', 'ignore').decode('utf-8')
    
    # Substituir espaços por underscores
    name = name.replace(' ', '_')
    
    # Remover caracteres especiais, mantendo apenas alfanuméricos, - e _
    name = re.sub(r'[^a-zA-Z0-9_-]', '', name)
    
    # Evitar nomes vazios
    if not name:
        name = 'documento'
    
    # Retornar com extensão
    return f"{name}{ext}"


class Categoria(models.Model):
    """
    Categorias de documentos para organização
    Ex: Identificação, Contratos, Procurações, Processos
    """
    escritorio = models.ForeignKey(
        Escritorio,
        on_delete=models.CASCADE,
        related_name='categorias_documentos',
        verbose_name='Escritório'
    )
    nome = models.CharField(
        max_length=100,
        verbose_name='Nome da Categoria'
    )
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    icone = models.CharField(
        max_length=50,
        default='description',
        verbose_name='Ícone Material-UI',
        help_text='Nome do ícone do Material-UI (ex: description, article, folder)'
    )
    cor = models.CharField(
        max_length=20,
        default='primary',
        verbose_name='Cor',
        help_text='Cor do Material-UI (primary, secondary, success, error, warning, info)'
    )
    ordem = models.IntegerField(
        default=0,
        verbose_name='Ordem de Exibição'
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Criação'
    )

    class Meta:
        ordering = ['ordem', 'nome']
        verbose_name = 'Categoria de Documento'
        verbose_name_plural = 'Categorias de Documentos'
        unique_together = ['escritorio', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.escritorio.nome})"


class Tag(models.Model):
    """
    Tags personalizadas para marcação de documentos
    """
    escritorio = models.ForeignKey(
        Escritorio,
        on_delete=models.CASCADE,
        related_name='tags_documentos',
        verbose_name='Escritório'
    )
    nome = models.CharField(
        max_length=50,
        verbose_name='Nome da Tag'
    )
    cor = models.CharField(
        max_length=7,
        default='#1976d2',
        verbose_name='Cor Hex',
        help_text='Cor em formato hexadecimal (#RRGGBB)'
    )
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Criação'
    )

    class Meta:
        ordering = ['nome']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        unique_together = ['escritorio', 'nome']

    def __str__(self):
        return self.nome


def documento_upload_path(instance, filename):
    """
    Define o caminho de upload dos documentos
    Organiza por: escritorio/cliente/ano/mes/filename
    Remove acentos e caracteres especiais do nome do arquivo
    """
    import datetime
    
    # Limpa o nome do arquivo
    filename = sanitize_filename(filename)
    
    now = datetime.datetime.now()
    return os.path.join(
        'documentos',
        f'escritorio_{instance.escritorio.id}',
        f'cliente_{instance.cliente.id}',
        str(now.year),
        str(now.month).zfill(2),
        filename
    )


class Documento(models.Model):
    """
    Documento digital vinculado a um cliente
    """
    # Relacionamentos
    escritorio = models.ForeignKey(
        Escritorio,
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name='Escritório'
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name='Cliente',
        null=True,
        blank=True
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos',
        verbose_name='Categoria'
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='documentos',
        verbose_name='Tags'
    )

    # Informações do Arquivo
    arquivo = models.FileField(
        upload_to=documento_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'txt', 'xlsx', 'xls']
            )
        ],
        verbose_name='Arquivo',
        null=True,
        blank=True
    )
    titulo = models.CharField(
        max_length=255,
        verbose_name='Título do Documento'
    )
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    
    # Metadados do Arquivo
    nome_original = models.CharField(
        max_length=255,
        verbose_name='Nome Original do Arquivo'
    )
    tipo_arquivo = models.CharField(
        max_length=10,
        verbose_name='Tipo/Extensão'
    )
    tamanho = models.BigIntegerField(
        verbose_name='Tamanho em Bytes'
    )
    hash_md5 = models.CharField(
        max_length=32,
        blank=True,
        verbose_name='Hash MD5',
        help_text='Para detectar duplicatas'
    )

    # Datas
    data_upload = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Upload'
    )
    data_documento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data do Documento',
        help_text='Data real do documento físico/assinatura'
    )
    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Atualização'
    )

    # Controles
    confidencial = models.BooleanField(
        default=False,
        verbose_name='Confidencial',
        help_text='Requer permissão especial para visualizar'
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    
    # Versionamento
    versao = models.IntegerField(
        default=1,
        verbose_name='Versão'
    )
    documento_pai = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versoes',
        verbose_name='Documento Original',
        help_text='Referência à versão anterior'
    )

    # Auditoria
    usuario_upload = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documentos_enviados',
        verbose_name='Usuário que fez Upload'
    )
    visualizacoes = models.IntegerField(
        default=0,
        verbose_name='Número de Visualizações'
    )
    downloads = models.IntegerField(
        default=0,
        verbose_name='Número de Downloads'
    )

    # Texto extraído (para busca futura - OCR)
    texto_extraido = models.TextField(
        blank=True,
        verbose_name='Texto Extraído (OCR)',
        help_text='Texto extraído do documento para busca'
    )

    class Meta:
        ordering = ['-data_upload']
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        indexes = [
            models.Index(fields=['escritorio', 'cliente', '-data_upload']),
            models.Index(fields=['escritorio', 'categoria', '-data_upload']),
            models.Index(fields=['hash_md5']),
        ]

    def __str__(self):
        if self.cliente:
            return f"{self.titulo} - {self.cliente.nome_completo}"
        return f"{self.titulo}"

    def save(self, *args, **kwargs):
        """
        Calcula o hash MD5 do arquivo no primeiro save
        E comprime PDFs maiores que 5MB
        """
        # Importação local para evitar dependência circular
        from .utils import compress_pdf

        # Verifica se é um update parcial (ex: apenas visualizacoes, ativo, etc)
        update_fields = kwargs.get('update_fields', None)
        should_process_file = (
            update_fields is None or 
            'arquivo' in update_fields or
            'nome_original' in update_fields or
            'tipo_arquivo' in update_fields or
            'tamanho' in update_fields or
            'hash_md5' in update_fields
        )
        
        # Só processa o arquivo se necessário
        if should_process_file and self.arquivo:
            # Se não tem hash, assumimos que é um arquivo novo ou alterado que precisa ser processado
            if not self.hash_md5:
                # Verifica se é PDF e maior que 5MB (5 * 1024 * 1024 bytes)
                try:
                    is_pdf = self.arquivo.name.lower().endswith('.pdf')
                    is_large = self.arquivo.size > (5 * 1024 * 1024)
                    
                    if is_pdf and is_large:
                        # Comprime o arquivo
                        compressed_file = compress_pdf(self.arquivo)
                        
                        # Atualiza o arquivo com a versão comprimida
                        self.arquivo = compressed_file
                except Exception as e:
                    print(f"Erro ao tentar comprimir PDF no save: {e}")

                # Calcula o hash MD5 (do arquivo original ou comprimido)
                md5_hash = hashlib.md5()
                for chunk in self.arquivo.chunks():
                    md5_hash.update(chunk)
                self.hash_md5 = md5_hash.hexdigest()
            
            # Extrai tipo e tamanho do arquivo (sempre atualiza para garantir consistência)
            try:
                self.nome_original = os.path.basename(self.arquivo.name)
                self.tipo_arquivo = os.path.splitext(self.arquivo.name)[1].lower().replace('.', '')
                self.tamanho = self.arquivo.size
            except (FileNotFoundError, OSError):
                # Se o arquivo físico não existir, mantém os valores existentes
                pass

        super().save(*args, **kwargs)

    def get_tamanho_formatado(self):
        """
        Retorna o tamanho do arquivo formatado (KB, MB, GB)
        """
        size = self.tamanho
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def incrementar_visualizacoes(self):
        """
        Incrementa o contador de visualizações
        """
        self.visualizacoes += 1
        self.save(update_fields=['visualizacoes'])

    def incrementar_downloads(self):
        """
        Incrementa o contador de downloads
        """
        self.downloads += 1
        self.save(update_fields=['downloads'])


class DocumentoAnaliseIA(models.Model):
    """
    Armazena análises de documentos realizadas por IA (GPT)
    Após OCR, o texto pode ser analisado por IA para diferentes propósitos
    """
    
    TIPO_ANALISE_CHOICES = [
        ('resumo', 'Resumo Executivo'),
        ('extracao_dados', 'Extração de Dados'),
        ('juridico', 'Análise Jurídica'),
        ('contrato', 'Análise de Contrato'),
        ('risco', 'Análise de Risco'),
        ('personalizado', 'Análise Personalizada'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('processando', 'Processando'),
        ('concluido', 'Concluído'),
        ('erro', 'Erro'),
    ]
    
    escritorio = models.ForeignKey(
        Escritorio,
        on_delete=models.CASCADE,
        related_name='analises_ia',
        verbose_name='Escritório'
    )
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='analises_ia',
        verbose_name='Documento'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='analises_solicitadas',
        verbose_name='Usuário que solicitou'
    )
    tipo_analise = models.CharField(
        max_length=20,
        choices=TIPO_ANALISE_CHOICES,
        verbose_name='Tipo de Análise'
    )
    prompt_personalizado = models.TextField(
        blank=True,
        null=True,
        verbose_name='Prompt Personalizado',
        help_text='Instruções específicas para a IA (apenas para análise personalizada)'
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name='Status'
    )
    
    # Resultado da análise
    resultado = models.TextField(
        blank=True,
        verbose_name='Resultado da Análise'
    )
    dados_estruturados = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Dados Estruturados',
        help_text='Dados extraídos em formato JSON (para extração de dados)'
    )
    
    # Metadados
    data_solicitacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data da Solicitação'
    )
    data_conclusao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data da Conclusão'
    )
    tempo_processamento = models.DurationField(
        null=True,
        blank=True,
        verbose_name='Tempo de Processamento'
    )
    mensagem_erro = models.TextField(
        blank=True,
        verbose_name='Mensagem de Erro'
    )
    
    # Custo e tokens (OpenAI)
    tokens_usados = models.IntegerField(
        default=0,
        verbose_name='Tokens Utilizados'
    )
    custo_estimado = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
        verbose_name='Custo Estimado (USD)'
    )
    modelo_ia = models.CharField(
        max_length=50,
        default='gpt-4',
        verbose_name='Modelo de IA Utilizado'
    )
    
    class Meta:
        verbose_name = 'Análise de IA'
        verbose_name_plural = 'Análises de IA'
        ordering = ['-data_solicitacao']
        indexes = [
            models.Index(fields=['escritorio', '-data_solicitacao']),
            models.Index(fields=['documento', '-data_solicitacao']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_analise_display()} - {self.documento.titulo} ({self.status})"


class DocumentoAnonimizacao(models.Model):
    """
    Controle de anonimização de documentos com possibilidade de reversão
    """
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('processando', 'Processando'),
        ('concluido', 'Concluído'),
        ('erro', 'Erro'),
        ('revertido', 'Revertido'),
    ]
    
    escritorio = models.ForeignKey(
        Escritorio,
        on_delete=models.CASCADE,
        related_name='anonimizacoes',
        verbose_name='Escritório'
    )
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='anonimizacoes',
        verbose_name='Documento'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='anonimizacoes_solicitadas',
        verbose_name='Usuário que solicitou'
    )
    
    # Controle de status
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name='Status'
    )
    
    # Textos
    texto_original = models.TextField(
        verbose_name='Texto Original',
        help_text='Backup do texto antes da anonimização'
    )
    texto_anonimizado = models.TextField(
        blank=True,
        verbose_name='Texto Anonimizado'
    )
    
    # Configurações da anonimização
    anonimizar_nomes = models.BooleanField(
        default=True,
        verbose_name='Anonimizar Nomes'
    )
    anonimizar_cpf = models.BooleanField(
        default=True,
        verbose_name='Anonimizar CPF'
    )
    anonimizar_rg = models.BooleanField(
        default=True,
        verbose_name='Anonimizar RG'
    )
    anonimizar_enderecos = models.BooleanField(
        default=True,
        verbose_name='Anonimizar Endereços'
    )
    anonimizar_telefones = models.BooleanField(
        default=True,
        verbose_name='Anonimizar Telefones'
    )
    anonimizar_emails = models.BooleanField(
        default=True,
        verbose_name='Anonimizar E-mails'
    )
    
    # Metadados
    data_solicitacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data da Solicitação'
    )
    data_conclusao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data da Conclusão'
    )
    data_reversao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data da Reversão'
    )
    mensagem_erro = models.TextField(
        blank=True,
        verbose_name='Mensagem de Erro'
    )
    
    class Meta:
        verbose_name = 'Anonimização de Documento'
        verbose_name_plural = 'Anonimizações de Documentos'
        ordering = ['-data_solicitacao']
        indexes = [
            models.Index(fields=['escritorio', '-data_solicitacao']),
            models.Index(fields=['documento', '-data_solicitacao']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Anonimização - {self.documento.titulo} ({self.status})"


class AnonimizacaoItem(models.Model):
    """
    Armazena cada substituição feita na anonimização para permitir reversão
    """
    TIPO_DADO_CHOICES = [
        ('nome', 'Nome'),
        ('cpf', 'CPF'),
        ('rg', 'RG'),
        ('endereco', 'Endereço'),
        ('telefone', 'Telefone'),
        ('email', 'E-mail'),
        ('outro', 'Outro'),
    ]
    
    anonimizacao = models.ForeignKey(
        DocumentoAnonimizacao,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Anonimização'
    )
    
    # Dados da substituição
    tipo_dado = models.CharField(
        max_length=20,
        choices=TIPO_DADO_CHOICES,
        verbose_name='Tipo de Dado'
    )
    valor_original = models.TextField(
        verbose_name='Valor Original',
        help_text='Valor real encontrado no documento'
    )
    valor_anonimizado = models.CharField(
        max_length=100,
        verbose_name='Valor Anonimizado',
        help_text='Placeholder usado na substituição (ex: NOME1, CPF1)'
    )
    
    anonimizado_manualmente = models.BooleanField(
        default=False,
        verbose_name='Anonimizado Manualmente',
        help_text='Indica se foi anonimizado manualmente pelo usuário'
    )

    # Metadados para localização
    posicao_inicio = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Posição Início',
        help_text='Posição do caractere no texto original'
    )
    posicao_fim = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Posição Fim'
    )
    contexto = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Contexto',
        help_text='Trecho do texto ao redor para validação'
    )
    
    # Auditoria
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Criação'
    )
    
    class Meta:
        verbose_name = 'Item de Anonimização'
        verbose_name_plural = 'Itens de Anonimização'
        ordering = ['posicao_inicio']
        unique_together = ['anonimizacao', 'valor_anonimizado']
    
    def __str__(self):
        return f"{self.get_tipo_dado_display()}: {self.valor_anonimizado}"
