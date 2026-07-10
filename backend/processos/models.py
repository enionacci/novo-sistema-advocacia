"""
Models para o Sistema de Gerenciamento de Processos Judiciais

- Processo: Processo judicial principal
- Parte: Partes envolvidas (autor, réu, etc.) - PODE SER CLIENTE DO ESCRITÓRIO
- Movimentacao: Andamentos do processo (timeline)
- Prazo: Controle de prazos processuais
- Audiencia: Audiências agendadas
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from clientes.models import Cliente
from escritorios.models import Escritorio

User = get_user_model()


class Processo(models.Model):
    """Processo judicial vinculado a um ou mais clientes"""
    
    TIPO_CHOICES = [
        ('civel', 'Cível'),
        ('trabalhista', 'Trabalhista'),
        ('criminal', 'Criminal'),
        ('familia', 'Família'),
        ('tributario', 'Tributário'),
        ('previdenciario', 'Previdenciário'),
        ('consumidor', 'Consumidor'),
        ('administrativo', 'Administrativo'),
    ]
    
    STATUS_CHOICES = [
        ('andamento', 'Em Andamento'),
        ('suspenso', 'Suspenso'),
        ('arquivado', 'Arquivado'),
        ('sentenciado', 'Sentenciado'),
        ('transito_julgado', 'Trânsito em Julgado'),
        ('recurso', 'Em Recurso'),
        ('execucao', 'Em Execução'),
    ]
    
    POSICAO_CHOICES = [
        ('autor', 'Autor/Requerente'),
        ('reu', 'Réu/Requerido'),
        ('ambos', 'Ambos (Litisconsórcio)'),
    ]
    
    # Relacionamentos
    escritorio = models.ForeignKey(
        Escritorio,
        on_delete=models.CASCADE,
        related_name='processos',
        verbose_name='Escritório'
    )
    cliente_principal = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='processos_principal',
        verbose_name='Cliente Principal',
        help_text='Cliente principal representado pelo escritório'
    )
    
    # Identificação do Processo
    numero_processo = models.CharField(
        max_length=25,
        unique=True,
        verbose_name='Número do Processo',
        help_text='Formato CNJ: 0000000-00.0000.0.00.0000',
        validators=[
            RegexValidator(
                regex=r'^\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}$',
                message='Formato inválido. Use: 0000000-00.0000.0.00.0000'
            )
        ]
    )
    numero_antigo = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Número Antigo'
    )
    
    # Classificação
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        blank=True,
        null=True,
        verbose_name='Tipo/Área',
        help_text='Será preenchido automaticamente pela API do tribunal'
    )
    classe = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Classe',
        help_text='Ex: Procedimento Comum Cível, Ação Trabalhista, etc.'
    )
    assunto = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Assunto Principal',
        help_text='Será preenchido automaticamente pela API do tribunal'
    )
    assuntos_secundarios = models.TextField(
        blank=True,
        null=True,
        verbose_name='Outros Assuntos'
    )
    
    # Posição do Cliente
    posicao_cliente = models.CharField(
        max_length=20,
        choices=POSICAO_CHOICES,
        blank=True,
        null=True,
        verbose_name='Posição do Cliente',
        help_text='Seu cliente é autor, réu ou ambos?'
    )
    
    # Tribunal e Vara
    tribunal = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Tribunal/Foro',
        help_text='Ex: TJSP, TRT-2, Foro de Salto - Será preenchido pela API'
    )
    comarca = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Comarca'
    )
    vara = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Vara'
    )
    uf = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        verbose_name='UF',
        help_text='Será preenchido automaticamente pela API'
    )
    
    # Datas Importantes
    data_distribuicao = models.DateField(
        blank=True,
        null=True,
        verbose_name='Data de Distribuição',
        help_text='Será preenchida automaticamente pela API'
    )
    data_citacao = models.DateField(
        blank=True,
        null=True,
        verbose_name='Data de Citação'
    )
    data_audiencia = models.DateField(
        blank=True,
        null=True,
        verbose_name='Próxima Audiência'
    )
    data_sentenca = models.DateField(
        blank=True,
        null=True,
        verbose_name='Data da Sentença'
    )
    data_transito_julgado = models.DateField(
        blank=True,
        null=True,
        verbose_name='Trânsito em Julgado'
    )
    
    # Controle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='andamento',
        verbose_name='Status'
    )
    tipo_distribuicao = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Tipo de Distribuição',
        help_text='Livre, Prevento, etc.'
    )
    
    # Valores
    valor_causa = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Valor da Causa'
    )
    valor_condenacao = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Valor da Condenação'
    )
    valor_acordo = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Valor do Acordo'
    )
    
    # Advogados
    advogado_responsavel = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processos_responsavel',
        verbose_name='Advogado Responsável'
    )
    advogados_equipe = models.ManyToManyField(
        User,
        related_name='processos_equipe',
        blank=True,
        verbose_name='Equipe'
    )
    
    # Links e Referências
    link_consulta = models.URLField(
        blank=True,
        null=True,
        verbose_name='Link para Consulta',
        help_text='Link do e-SAJ ou outro sistema'
    )
    processo_origem = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processos_derivados',
        verbose_name='Processo de Origem'
    )
    
    # Observações e Estratégia
    resumo = models.TextField(
        blank=True,
        null=True,
        verbose_name='Resumo do Caso'
    )
    estrategia_juridica = models.TextField(
        blank=True,
        null=True,
        verbose_name='Estratégia Jurídica'
    )
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observações'
    )
    
    # Alertas
    prazo_proximo = models.DateField(
        blank=True,
        null=True,
        verbose_name='Próximo Prazo'
    )
    alerta_prazo = models.BooleanField(
        default=False,
        verbose_name='Alertar sobre Prazo'
    )
    
    # Auditoria
    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Cadastro'
    )
    ultima_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Atualização'
    )
    usuario_cadastro = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processos_cadastrados',
        verbose_name='Cadastrado por'
    )
    
    # Flags
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    sigilo = models.BooleanField(
        default=False,
        verbose_name='Segredo de Justiça'
    )
    
    class Meta:
        ordering = ['-data_distribuicao']
        verbose_name = 'Processo'
        verbose_name_plural = 'Processos'
        indexes = [
            models.Index(fields=['escritorio', 'cliente_principal', '-data_distribuicao']),
            models.Index(fields=['numero_processo']),
            models.Index(fields=['status']),
            models.Index(fields=['advogado_responsavel', 'status']),
        ]
    
    def __str__(self):
        return f"{self.numero_processo} - {self.cliente_principal.nome_completo}"
    
    def get_partes_autoras(self):
        """Retorna todas as partes autoras do processo"""
        return self.partes.filter(tipo_parte='autor')
    
    def get_partes_reus(self):
        """Retorna todos os réus do processo"""
        return self.partes.filter(tipo_parte='reu')
    
    def get_clientes_vinculados(self):
        """Retorna todos os clientes do escritório envolvidos no processo"""
        return Cliente.objects.filter(partes_processos__processo=self).distinct()


class Parte(models.Model):
    """
    Partes envolvidas no processo
    PODE SER VINCULADA A UM CLIENTE DO ESCRITÓRIO (autor ou réu)
    """
    
    TIPO_PARTE_CHOICES = [
        ('autor', 'Autor/Requerente'),
        ('reu', 'Réu/Requerido'),
        ('terceiro', 'Terceiro Interessado'),
        ('assistente', 'Assistente'),
        ('ministerio_publico', 'Ministério Público'),
    ]
    
    TIPO_PESSOA_CHOICES = [
        ('fisica', 'Pessoa Física'),
        ('juridica', 'Pessoa Jurídica'),
    ]
    
    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        related_name='partes',
        verbose_name='Processo'
    )
    
    # Tipo
    tipo_parte = models.CharField(
        max_length=30,
        choices=TIPO_PARTE_CHOICES,
        verbose_name='Tipo de Parte'
    )
    tipo_pessoa = models.CharField(
        max_length=10,
        choices=TIPO_PESSOA_CHOICES,
        verbose_name='Tipo de Pessoa'
    )
    
    # Vinculação com Cliente (PODE SER AUTOR OU RÉU!)
    cliente_vinculado = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='partes_processos',
        verbose_name='Cliente do Escritório',
        help_text='Se esta parte for um cliente cadastrado no sistema'
    )
    
    # Dados da Parte (preenchidos automaticamente se for cliente, ou manualmente)
    nome = models.CharField(
        max_length=255,
        verbose_name='Nome/Razão Social'
    )
    cpf_cnpj = models.CharField(
        max_length=18,
        blank=True,
        null=True,
        verbose_name='CPF/CNPJ'
    )
    
    # Endereço
    logradouro = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Logradouro'
    )
    numero = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Número'
    )
    complemento = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Complemento'
    )
    bairro = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Bairro'
    )
    cidade = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Cidade'
    )
    estado = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        verbose_name='Estado (UF)'
    )
    cep = models.CharField(
        max_length=9,
        blank=True,
        null=True,
        verbose_name='CEP'
    )
    
    # Representação
    advogado_nome = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Nome do Advogado'
    )
    advogado_oab = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='OAB'
    )
    
    # Flag para indicar se é representado pelo escritório
    representado_escritorio = models.BooleanField(
        default=False,
        verbose_name='Representado pelo Escritório',
        help_text='Marque se esta parte é representada pelo seu escritório'
    )
    
    class Meta:
        verbose_name = 'Parte do Processo'
        verbose_name_plural = 'Partes do Processo'
        ordering = ['tipo_parte', 'nome']
    
    def __str__(self):
        representacao = " (Cliente)" if self.cliente_vinculado else ""
        return f"{self.nome} ({self.get_tipo_parte_display()}){representacao}"
    
    def save(self, *args, **kwargs):
        """
        Se cliente_vinculado está definido, importa dados automaticamente
        """
        if self.cliente_vinculado and not self.nome:
            # Importa dados do cliente
            self.nome = self.cliente_vinculado.nome_completo or self.cliente_vinculado.razao_social
            self.cpf_cnpj = self.cliente_vinculado.cpf or self.cliente_vinculado.cnpj
            self.tipo_pessoa = 'fisica' if self.cliente_vinculado.cpf else 'juridica'
            
            # Importa endereço
            self.logradouro = self.cliente_vinculado.logradouro
            self.numero = self.cliente_vinculado.numero
            self.complemento = self.cliente_vinculado.complemento
            self.bairro = self.cliente_vinculado.bairro
            self.cidade = self.cliente_vinculado.cidade
            self.estado = self.cliente_vinculado.estado
            self.cep = self.cliente_vinculado.cep
            
            # Marca como representado pelo escritório
            self.representado_escritorio = True
        
        super().save(*args, **kwargs)


class Movimentacao(models.Model):
    """Movimentações/Andamentos do processo (baseado no e-SAJ)"""
    
    TIPO_CHOICES = [
        ('peticao', 'Petição'),
        ('despacho', 'Despacho'),
        ('decisao', 'Decisão'),
        ('sentenca', 'Sentença'),
        ('acordao', 'Acórdão'),
        ('certidao', 'Certidão'),
        ('audiencia', 'Audiência'),
        ('intimacao', 'Intimação'),
        ('juntada', 'Juntada'),
        ('outro', 'Outro'),
    ]
    
    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        related_name='movimentacoes',
        verbose_name='Processo'
    )
    
    # Dados da Movimentação
    data_movimentacao = models.DateTimeField(
        verbose_name='Data da Movimentação'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name='Tipo'
    )
    descricao = models.TextField(
        verbose_name='Descrição'
    )
    
    # Documentos
    documento = models.ForeignKey(
        'documentos.Documento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes',
        verbose_name='Documento Vinculado'
    )
    numero_protocolo = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Número do Protocolo'
    )
    
    # Prazos
    gera_prazo = models.BooleanField(
        default=False,
        verbose_name='Gera Prazo'
    )
    prazo_dias = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Prazo (dias)'
    )
    data_limite = models.DateField(
        blank=True,
        null=True,
        verbose_name='Data Limite'
    )
    
    # Auditoria
    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Cadastrado em'
    )
    cadastrado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Cadastrado por'
    )
    
    # Flags
    importante = models.BooleanField(
        default=False,
        verbose_name='Marcar como Importante'
    )
    lido = models.BooleanField(
        default=False,
        verbose_name='Lido'
    )
    
    # Análise com IA
    analisada_ia = models.BooleanField(
        default=False,
        verbose_name='Analisada por IA',
        help_text='Indica se esta movimentação foi analisada pela IA'
    )
    data_analise_ia = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Data da Análise IA',
        help_text='Quando a análise foi realizada'
    )
    resultado_analise_ia = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Resultado da Análise IA',
        help_text='Resultado completo da análise (prazos, audiências, etc.)'
    )
    analisada_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes_analisadas',
        verbose_name='Analisada por'
    )
    
    class Meta:
        ordering = ['-data_movimentacao']
        verbose_name = 'Movimentação'
        verbose_name_plural = 'Movimentações'
        indexes = [
            models.Index(fields=['processo', '-data_movimentacao']),
            models.Index(fields=['tipo', '-data_movimentacao']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.data_movimentacao.strftime('%d/%m/%Y')}"


class Prazo(models.Model):
    """Controle de prazos processuais"""
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('cumprido', 'Cumprido'),
        ('vencido', 'Vencido'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        related_name='prazos',
        verbose_name='Processo'
    )
    movimentacao = models.ForeignKey(
        Movimentacao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prazos_gerados',
        verbose_name='Movimentação Origem'
    )
    
    # Prazo
    descricao = models.CharField(
        max_length=255,
        verbose_name='Descrição do Prazo'
    )
    data_inicio = models.DateField(
        verbose_name='Data de Início'
    )
    data_limite = models.DateField(
        verbose_name='Data Limite'
    )
    prazo_dias = models.IntegerField(
        verbose_name='Prazo (dias)'
    )
    
    # Controle
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name='Status'
    )
    prioridade = models.CharField(
        max_length=10,
        choices=PRIORIDADE_CHOICES,
        default='media',
        verbose_name='Prioridade'
    )
    
    # Responsável
    responsavel = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='prazos_responsavel',
        verbose_name='Responsável'
    )
    
    # Cumprimento
    data_cumprimento = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Cumprido em'
    )
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observações'
    )
    
    # Alertas
    alertar_dias_antes = models.IntegerField(
        default=3,
        verbose_name='Alertar X dias antes'
    )
    alerta_enviado = models.BooleanField(
        default=False,
        verbose_name='Alerta Enviado'
    )
    
    class Meta:
        ordering = ['data_limite', 'prioridade']
        verbose_name = 'Prazo'
        verbose_name_plural = 'Prazos'
        indexes = [
            models.Index(fields=['processo', 'status', 'data_limite']),
            models.Index(fields=['responsavel', 'status', 'data_limite']),
        ]
    
    def __str__(self):
        return f"{self.descricao} - Limite: {self.data_limite.strftime('%d/%m/%Y')}"


class Audiencia(models.Model):
    """Audiências do processo"""
    
    TIPO_CHOICES = [
        ('conciliacao', 'Conciliação'),
        ('instrucao', 'Instrução e Julgamento'),
        ('inicial', 'Audiência Inicial'),
        ('una', 'Audiência Una'),
        ('justificacao', 'Justificação'),
        ('outras', 'Outras'),
    ]
    
    STATUS_CHOICES = [
        ('agendada', 'Agendada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
        ('adiada', 'Adiada'),
    ]
    
    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        related_name='audiencias',
        verbose_name='Processo'
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de Audiência'
    )
    data_hora = models.DateTimeField(
        verbose_name='Data e Hora'
    )
    local = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Local'
    )
    link_virtual = models.URLField(
        blank=True,
        null=True,
        verbose_name='Link (Audiência Virtual)'
    )
    
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='agendada',
        verbose_name='Status'
    )
    
    # Pauta
    pauta = models.TextField(
        blank=True,
        null=True,
        verbose_name='Pauta/Objetivo'
    )
    resultado = models.TextField(
        blank=True,
        null=True,
        verbose_name='Resultado/Ata'
    )
    
    # Documentos
    ata = models.ForeignKey(
        'documentos.Documento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audiencias_ata',
        verbose_name='Ata da Audiência'
    )
    
    # Alertas
    alertar = models.BooleanField(
        default=True,
        verbose_name='Enviar Alerta'
    )
    
    # Auditoria
    data_cadastro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Cadastro'
    )
    cadastrado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Cadastrado por'
    )
    
    class Meta:
        ordering = ['data_hora']
        verbose_name = 'Audiência'
        verbose_name_plural = 'Audiências'
        indexes = [
            models.Index(fields=['processo', 'status', 'data_hora']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"
