from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Cliente, Funil, Tarefa, Atividade, Documento, 
    Email, Nota, Meta, Produto, Proposta, Tag
)


class ClienteForm(forms.ModelForm):
    """Formulário para cadastro e edição de clientes"""
    
    class Meta:
        model = Cliente
        fields = [
            'nome', 'tipo_pessoa', 'cpf_cnpj', 'telefone', 'telefone_alternativo',
            'email', 'email_alternativo', 'endereco', 'cidade', 'estado', 'cep',
            'empresa', 'cargo', 'setor', 'valor_estimado', 'origem',
            'linkedin', 'facebook', 'instagram', 'funil', 'etapa',
            'probabilidade', 'tags', 'observacoes'
        ]
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo ou razão social'
            }),
            'tipo_pessoa': forms.Select(attrs={'class': 'form-select'}),
            'cpf_cnpj': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '000.000.000-00 ou 00.000.000/0000-00'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(00) 00000-0000'
            }),
            'telefone_alternativo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(00) 00000-0000'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            }),
            'email_alternativo': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            }),
            'endereco': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rua, número, complemento'
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cidade'
            }),
            'estado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'UF',
                'maxlength': '2'
            }),
            'cep': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '00000-000'
            }),
            'empresa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da empresa'
            }),
            'cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cargo do contato'
            }),
            'setor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Setor de atuação'
            }),
            'valor_estimado': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'origem': forms.Select(attrs={'class': 'form-select'}),
            'linkedin': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/...'
            }),
            'facebook': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://facebook.com/...'
            }),
            'instagram': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://instagram.com/...'
            }),
            'funil': forms.Select(attrs={'class': 'form-select'}),
            'etapa': forms.Select(attrs={'class': 'form-select'}),
            'probabilidade': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100'
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Observações adicionais sobre o cliente...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar funis e tags do usuário
        if self.user:
            self.fields['funil'].queryset = Funil.objects.filter(
                usuario=self.user, 
                ativo=True
            )
            self.fields['tags'].queryset = Tag.objects.filter(usuario=self.user)

    def clean_cpf_cnpj(self):
        cpf_cnpj = self.cleaned_data.get('cpf_cnpj')
        if cpf_cnpj:
            # Remover formatação
            cpf_cnpj = ''.join(filter(str.isdigit, cpf_cnpj))
            # Adicionar validação aqui se necessário
        return cpf_cnpj


class TarefaForm(forms.ModelForm):
    """Formulário para tarefas"""
    
    class Meta:
        model = Tarefa
        fields = [
            'titulo', 'descricao', 'tipo', 'status', 'prioridade',
            'cliente', 'responsavel', 'data_vencimento', 'lembrete',
            'tempo_estimado', 'tags'
        ]
        
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título da tarefa'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Descrição detalhada...'
            }),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'prioridade': forms.Select(attrs={'class': 'form-select'}),
            'cliente': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Selecione um cliente (opcional)'
            }),
            'responsavel': forms.Select(attrs={'class': 'form-select'}),
            'data_vencimento': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'lembrete': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'tempo_estimado': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Tempo em minutos'
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['cliente'].queryset = Cliente.objects.filter(usuario=self.user)
            self.fields['tags'].queryset = Tag.objects.filter(usuario=self.user)
            
            # Define o usuário como responsável padrão
            self.fields['responsavel'].initial = self.user


class AtividadeForm(forms.ModelForm):
    """Formulário para registro de atividades"""
    
    class Meta:
        model = Atividade
        fields = [
            'tipo', 'titulo', 'descricao', 'resultado',
            'duracao_minutos', 'data_atividade'
        ]
        
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título da atividade'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Descreva o que foi realizado...'
            }),
            'resultado': forms.Select(attrs={'class': 'form-select'}),
            'duracao_minutos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Duração em minutos'
            }),
            'data_atividade': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }


class FunilForm(forms.ModelForm):
    """Formulário para funis"""
    
    etapas_texto = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': '5',
            'placeholder': 'Digite uma etapa por linha, ex:\nContato Inicial\nQualificação\nProposta\nNegociação\nFechamento'
        }),
        help_text='Digite uma etapa por linha'
    )
    
    class Meta:
        model = Funil
        fields = ['nome', 'cor']
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do funil'
            }),
            'cor': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance.pk:
            # Se está editando, preencher etapas
            self.fields['etapas_texto'].initial = '\n'.join(self.instance.etapas)

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Processar etapas
        etapas_texto = self.cleaned_data.get('etapas_texto', '')
        etapas = [e.strip() for e in etapas_texto.split('\n') if e.strip()]
        instance.etapas = etapas
        
        # Criar prazos padrão se não existirem
        if not instance.prazos:
            instance.prazos = {etapa: 24 for etapa in etapas}
        
        # Criar taxas padrão se não existirem
        if not instance.taxas_conversao:
            instance.taxas_conversao = {etapa: 50 for etapa in etapas[:-1]}
        
        if commit:
            instance.save()
        
        return instance


class NotaForm(forms.ModelForm):
    """Formulário para notas"""
    
    class Meta:
        model = Nota
        fields = ['titulo', 'conteudo', 'fixada']
        
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título da nota (opcional)'
            }),
            'conteudo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '5',
                'placeholder': 'Conteúdo da nota...'
            }),
            'fixada': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class DocumentoForm(forms.ModelForm):
    """Formulário para upload de documentos"""
    
    class Meta:
        model = Documento
        fields = ['nome', 'tipo', 'arquivo', 'descricao']
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do documento'
            }),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'arquivo': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Descrição do documento...'
            }),
        }


class EmailForm(forms.ModelForm):
    """Formulário para emails"""
    
    class Meta:
        model = Email
        fields = ['assunto', 'corpo', 'destinatario']
        
        widgets = {
            'assunto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Assunto do email'
            }),
            'corpo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '10',
                'placeholder': 'Corpo do email...'
            }),
            'destinatario': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            }),
        }


class MetaForm(forms.ModelForm):
    """Formulário para metas"""
    
    class Meta:
        model = Meta
        fields = [
            'nome', 'descricao', 'periodo', 'valor_alvo',
            'data_inicio', 'data_fim'
        ]
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da meta'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Descrição da meta...'
            }),
            'periodo': forms.Select(attrs={'class': 'form-select'}),
            'valor_alvo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'data_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'data_fim': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        
        if data_inicio and data_fim:
            if data_fim <= data_inicio:
                raise ValidationError('A data final deve ser posterior à data inicial.')
        
        return cleaned_data


class ProdutoForm(forms.ModelForm):
    """Formulário para produtos/serviços"""
    
    class Meta:
        model = Produto
        fields = [
            'nome', 'descricao', 'codigo', 'preco', 'custo',
            'categoria', 'ativo'
        ]
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do produto/serviço'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Descrição...'
            }),
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código único do produto'
            }),
            'preco': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'custo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'categoria': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Categoria'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class TagForm(forms.ModelForm):
    """Formulário para tags"""
    
    class Meta:
        model = Tag
        fields = ['nome', 'cor']
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da tag'
            }),
            'cor': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
        }


class BuscaForm(forms.Form):
    """Formulário de busca global"""
    
    q = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '🔍 Buscar clientes, tarefas, atividades...',
            'autocomplete': 'off'
        })
    )


class FiltroRelatorioForm(forms.Form):
    """Formulário para filtros de relatórios"""
    
    PERIODO_CHOICES = [
        ('7', 'Últimos 7 dias'),
        ('30', 'Últimos 30 dias'),
        ('90', 'Últimos 90 dias'),
        ('365', 'Último ano'),
        ('custom', 'Período personalizado'),
    ]
    
    periodo = forms.ChoiceField(
        choices=PERIODO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='30'
    )
    
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    funil = forms.ModelChoiceField(
        queryset=Funil.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-placeholder': 'Todos os funis'
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['funil'].queryset = Funil.objects.filter(
                usuario=user,
                ativo=True
            )