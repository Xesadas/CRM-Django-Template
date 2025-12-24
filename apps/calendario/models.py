from django.db import models
from django.conf import settings
from datetime import date

User = settings.AUTH_USER_MODEL

class CategoriaTarefa(models.Model):
    nome = models.CharField(max_length=100)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    cor = models.CharField(max_length=7, default='#000000')
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Categoria de Tarefa'
        verbose_name_plural = 'Categorias de Tarefa'
        unique_together = ['nome', 'usuario']
    
    def __str__(self):
        return self.nome

PRIORIDADE_CHOICES = [
    ('baixa', 'Baixa'),
    ('media', 'Média'),
    ('alta', 'Alta'),
]

STATUS_CHOICES = [
    ('pendente', 'Pendente'),
    ('em_andamento', 'Em Andamento'),
    ('concluida', 'Concluída'),
    ('cancelada', 'Cancelada'),
]

class Tarefa(models.Model):
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)
    data_vencimento = models.DateField()
    data_conclusao = models.DateField(null=True, blank=True)
    
    # Categorização
    categoria = models.ForeignKey(CategoriaTarefa, on_delete=models.SET_NULL, null=True, blank=True)
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default='media')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    
    # Recorrência
    recorrente = models.BooleanField(default=False)
    frequencia = models.CharField(max_length=20, choices=[
        ('diaria', 'Diária'),
        ('semanal', 'Semanal'),
        ('mensal', 'Mensal'),
        ('anual', 'Anual'),
    ], default='mensal')
    data_limite_recorrencia = models.DateField(null=True, blank=True)
    
    # Usuário
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    atribuido_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='tarefas_atribuidas')
    
    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.titulo} - {self.get_status_display()}"
    
    class Meta:
        ordering = ['data_vencimento', 'prioridade']
        verbose_name = 'Tarefa'
        verbose_name_plural = 'Tarefas'
    
    @property
    def esta_atrasada(self):
        if self.status == 'concluida':
            return False
        return self.data_vencimento < date.today()