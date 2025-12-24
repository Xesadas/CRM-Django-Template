from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Funil(models.Model):
    """Funil de vendas com etapas personalizáveis"""
    nome = models.CharField(max_length=100)
    etapas = models.JSONField(default=list, help_text="Lista de etapas do funil")
    prazos = models.JSONField(default=dict, help_text="Prazos em horas para cada etapa")
    taxas_conversao = models.JSONField(default=dict, help_text="Taxas de conversão esperadas")
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='funis')
    cor = models.CharField(max_length=7, default='#007bff', help_text="Cor do funil em hexadecimal")
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Funil de Vendas"
        verbose_name_plural = "Funis de Vendas"
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def get_etapas_display(self):
        return " → ".join(self.etapas)

    def get_prazo_etapa(self, etapa):
        return self.prazos.get(etapa, 24)


class Tag(models.Model):
    """Tags para organização"""
    nome = models.CharField(max_length=50)
    cor = models.CharField(max_length=7, default='#6c757d')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        unique_together = ['nome', 'usuario']

    def __str__(self):
        return self.nome


class Cliente(models.Model):
    """Cliente no funil de vendas"""
    TIPO_PESSOA_CHOICES = [
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    ]
    
    ORIGEM_CHOICES = [
        ('indicacao', 'Indicação'),
        ('site', 'Site'),
        ('redes_sociais', 'Redes Sociais'),
        ('email', 'Email Marketing'),
        ('evento', 'Evento'),
        ('telefonema', 'Telefonema'),
        ('outros', 'Outros'),
    ]

    # Dados básicos
    nome = models.CharField(max_length=200)
    tipo_pessoa = models.CharField(max_length=2, choices=TIPO_PESSOA_CHOICES, default='PF')
    cpf_cnpj = models.CharField(max_length=18, blank=True, null=True)
    
    # Contato
    telefone = models.CharField(max_length=20, blank=True, null=True)
    telefone_alternativo = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    email_alternativo = models.EmailField(blank=True, null=True)
    
    # Endereço
    endereco = models.CharField(max_length=200, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    cep = models.CharField(max_length=9, blank=True, null=True)
    
    # Informações comerciais
    empresa = models.CharField(max_length=200, blank=True, null=True)
    cargo = models.CharField(max_length=100, blank=True, null=True)
    setor = models.CharField(max_length=100, blank=True, null=True)
    valor_estimado = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        verbose_name="Valor Estimado do Negócio"
    )
    origem = models.CharField(max_length=20, choices=ORIGEM_CHOICES, default='outros')
    
    # Redes sociais
    linkedin = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    
    # Controle de funil
    funil = models.ForeignKey(Funil, on_delete=models.CASCADE, related_name='clientes')
    etapa = models.CharField(max_length=100)
    data_entrada_etapa = models.DateTimeField(default=timezone.now)
    probabilidade = models.IntegerField(
        default=50, 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Probabilidade de conversão (%)"
    )
    
    # Relacionamentos
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clientes')
    tags = models.ManyToManyField(Tag, blank=True, related_name='clientes')
    
    # Observações
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    ultimo_contato = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['-data_entrada_etapa']
        indexes = [
            models.Index(fields=['usuario', 'funil', 'etapa']),
            models.Index(fields=['data_entrada_etapa']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.nome} - {self.etapa}"

    def horas_na_etapa(self):
        delta = timezone.now() - self.data_entrada_etapa
        return delta.total_seconds() / 3600

    def esta_atrasado(self):
        prazo = self.funil.get_prazo_etapa(self.etapa)
        if prazo == 0:
            return False
        return self.horas_na_etapa() > prazo

    def horas_atraso(self):
        if not self.esta_atrasado():
            return 0
        prazo = self.funil.get_prazo_etapa(self.etapa)
        return self.horas_na_etapa() - prazo


class Tarefa(models.Model):
    """Tarefas do CRM"""
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]
    
    TIPO_CHOICES = [
        ('ligacao', 'Ligação'),
        ('email', 'Email'),
        ('reuniao', 'Reunião'),
        ('proposta', 'Enviar Proposta'),
        ('followup', 'Follow-up'),
        ('negociacao', 'Negociação'),
        ('visita', 'Visita'),
        ('apresentacao', 'Apresentação'),
        ('outros', 'Outros'),
    ]

    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='outros')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='media')
    
    # Relacionamentos
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='tarefas', null=True, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tarefas')
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tarefas_responsavel')
    tags = models.ManyToManyField(Tag, blank=True, related_name='tarefas')
    
    # Datas
    data_vencimento = models.DateTimeField()
    data_conclusao = models.DateTimeField(null=True, blank=True)
    lembrete = models.DateTimeField(null=True, blank=True, help_text="Data/hora para lembrete")
    
    # Controles
    tempo_estimado = models.IntegerField(null=True, blank=True, help_text="Tempo estimado em minutos")
    tempo_gasto = models.IntegerField(null=True, blank=True, help_text="Tempo gasto em minutos")
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tarefa"
        verbose_name_plural = "Tarefas"
        ordering = ['data_vencimento', '-prioridade']
        indexes = [
            models.Index(fields=['usuario', 'status']),
            models.Index(fields=['data_vencimento']),
            models.Index(fields=['cliente']),
        ]

    def __str__(self):
        return f"{self.titulo} - {self.get_status_display()}"

    def esta_vencida(self):
        return self.status != 'concluida' and timezone.now() > self.data_vencimento

    def dias_ate_vencimento(self):
        delta = self.data_vencimento - timezone.now()
        return delta.days


class Atividade(models.Model):
    """Registro de atividades e interações com clientes"""
    TIPO_CHOICES = [
        ('ligacao', 'Ligação'),
        ('email', 'Email'),
        ('reuniao', 'Reunião'),
        ('proposta', 'Proposta Enviada'),
        ('contrato', 'Contrato'),
        ('visita', 'Visita'),
        ('nota', 'Nota'),
        ('whatsapp', 'WhatsApp'),
        ('outros', 'Outros'),
    ]
    
    RESULTADO_CHOICES = [
        ('sucesso', 'Sucesso'),
        ('sem_resposta', 'Sem Resposta'),
        ('agendar_novo', 'Agendar Novo Contato'),
        ('negativo', 'Negativo'),
        ('outros', 'Outros'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='nota')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    resultado = models.CharField(max_length=20, choices=RESULTADO_CHOICES, null=True, blank=True)
    
    # Relacionamentos
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='atividades')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='atividades')
    tarefa = models.ForeignKey(Tarefa, on_delete=models.SET_NULL, null=True, blank=True, related_name='atividades')
    
    # Duração (para ligações/reuniões)
    duracao_minutos = models.IntegerField(null=True, blank=True)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    data_atividade = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Atividade"
        verbose_name_plural = "Atividades"
        ordering = ['-data_atividade']
        indexes = [
            models.Index(fields=['cliente', '-data_atividade']),
            models.Index(fields=['usuario', '-data_atividade']),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.cliente.nome}"


class Documento(models.Model):
    """Documentos anexados aos clientes"""
    TIPO_CHOICES = [
        ('proposta', 'Proposta'),
        ('contrato', 'Contrato'),
        ('apresentacao', 'Apresentação'),
        ('orcamento', 'Orçamento'),
        ('documento', 'Documento'),
        ('outros', 'Outros'),
    ]

    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='documento')
    arquivo = models.FileField(upload_to='documentos/%Y/%m/')
    descricao = models.TextField(blank=True, null=True)
    
    # Relacionamentos
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='documentos')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documentos')
    
    # Metadados
    tamanho = models.IntegerField(help_text="Tamanho em bytes")
    
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ['-criado_em']

    def __str__(self):
        return self.nome

    def tamanho_formatado(self):
        """Retorna tamanho formatado"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.tamanho < 1024.0:
                return f"{self.tamanho:.1f} {unit}"
            self.tamanho /= 1024.0
        return f"{self.tamanho:.1f} TB"


class Email(models.Model):
    """Emails enviados/recebidos"""
    TIPO_CHOICES = [
        ('enviado', 'Enviado'),
        ('recebido', 'Recebido'),
        ('rascunho', 'Rascunho'),
    ]

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='enviado')
    assunto = models.CharField(max_length=200)
    corpo = models.TextField()
    destinatario = models.EmailField()
    remetente = models.EmailField()
    
    # Relacionamentos
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='emails')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usuario_emails')
    
    # Status
    lido = models.BooleanField(default=False)
    respondido = models.BooleanField(default=False)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    enviado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Email"
        verbose_name_plural = "Emails"
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.assunto} - {self.destinatario}"


class Nota(models.Model):
    """Notas rápidas sobre clientes"""
    titulo = models.CharField(max_length=200, blank=True, null=True)
    conteudo = models.TextField()
    
    # Relacionamentos
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='notas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notas')
    
    # Controles
    fixada = models.BooleanField(default=False)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nota"
        verbose_name_plural = "Notas"
        ordering = ['-fixada', '-criado_em']

    def __str__(self):
        return self.titulo or f"Nota {self.id}"


class Meta(models.Model):
    """Metas de vendas"""
    PERIODO_CHOICES = [
        ('diario', 'Diário'),
        ('semanal', 'Semanal'),
        ('mensal', 'Mensal'),
        ('trimestral', 'Trimestral'),
        ('anual', 'Anual'),
    ]

    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    periodo = models.CharField(max_length=20, choices=PERIODO_CHOICES, default='mensal')
    valor_alvo = models.DecimalField(max_digits=15, decimal_places=2)
    valor_atual = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Relacionamentos
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='metas')
    
    # Datas
    data_inicio = models.DateField()
    data_fim = models.DateField()
    
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Meta"
        verbose_name_plural = "Metas"
        ordering = ['-data_inicio']

    def __str__(self):
        return f"{self.nome} - {self.periodo}"

    def percentual_atingido(self):
        if self.valor_alvo == 0:
            return 0
        return (self.valor_atual / self.valor_alvo) * 100


class Produto(models.Model):
    """Produtos/Serviços oferecidos"""
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    codigo = models.CharField(max_length=50, unique=True)
    preco = models.DecimalField(max_digits=15, decimal_places=2)
    custo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    categoria = models.CharField(max_length=100, blank=True, null=True)
    
    # Controles
    ativo = models.BooleanField(default=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='produtos')
    
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"

    def margem(self):
        if self.preco == 0:
            return 0
        return ((self.preco - self.custo) / self.preco) * 100


class Proposta(models.Model):
    """Propostas comerciais"""
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('enviada', 'Enviada'),
        ('visualizada', 'Visualizada'),
        ('aceita', 'Aceita'),
        ('rejeitada', 'Rejeitada'),
        ('expirada', 'Expirada'),
    ]

    numero = models.CharField(max_length=50, unique=True)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
    
    # Valores
    valor_total = models.DecimalField(max_digits=15, decimal_places=2)
    desconto = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Relacionamentos
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='propostas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='propostas')
    produtos = models.ManyToManyField(Produto, through='ItemProposta')
    
    # Datas
    data_validade = models.DateField()
    data_aceite = models.DateTimeField(null=True, blank=True)
    
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Proposta"
        verbose_name_plural = "Propostas"
        ordering = ['-criado_em']

    def __str__(self):
        return f"Proposta {self.numero} - {self.cliente.nome}"

    def valor_final(self):
        return self.valor_total - self.desconto


class ItemProposta(models.Model):
    """Itens de uma proposta"""
    proposta = models.ForeignKey(Proposta, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=15, decimal_places=2)
    desconto = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Item da Proposta"
        verbose_name_plural = "Itens da Proposta"

    def subtotal(self):
        return (self.quantidade * self.preco_unitario) - self.desconto