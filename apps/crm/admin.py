from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Funil, Cliente, Tarefa, Atividade, Documento,
    Email, Nota, Meta, Produto, Proposta, ItemProposta, Tag
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cor_display', 'usuario', 'criado_em']
    list_filter = ['usuario', 'criado_em']
    search_fields = ['nome']
    readonly_fields = ['criado_em']
    
    def cor_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; border-radius: 3px; color: white;">{}</span>',
            obj.cor, obj.cor
        )
    cor_display.short_description = 'Cor'


@admin.register(Funil)
class FunilAdmin(admin.ModelAdmin):
    list_display = ['nome', 'usuario', 'qtd_etapas', 'cor_display', 'ativo', 'criado_em']
    list_filter = ['usuario', 'ativo', 'criado_em']
    search_fields = ['nome']
    readonly_fields = ['criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'usuario', 'cor', 'ativo')
        }),
        ('Configuração do Funil', {
            'fields': ('etapas', 'prazos', 'taxas_conversao')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def qtd_etapas(self, obj):
        return len(obj.etapas) if obj.etapas else 0
    qtd_etapas.short_description = 'Nº Etapas'
    
    def cor_display(self, obj):
        return format_html(
            '<div style="background-color: {}; width: 30px; height: 15px; border-radius: 3px;"></div>',
            obj.cor
        )
    cor_display.short_description = 'Cor'


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 'tipo_pessoa', 'empresa', 'telefone', 'email',
        'funil', 'etapa', 'valor_estimado', 'probabilidade',
        'status_prazo', 'usuario', 'criado_em'
    ]
    list_filter = [
        'tipo_pessoa', 'funil', 'etapa', 'origem',
        'usuario', 'criado_em'
    ]
    search_fields = [
        'nome', 'email', 'telefone', 'empresa',
        'cpf_cnpj'
    ]
    readonly_fields = [
        'criado_em', 'atualizado_em',
        'data_entrada_etapa', 'ultimo_contato',
        'tempo_na_etapa_display'
    ]
    filter_horizontal = ['tags']
    
    fieldsets = (
        ('Dados Básicos', {
            'fields': (
                'nome', 'tipo_pessoa', 'cpf_cnpj',
                'origem'
            )
        }),
        ('Contato', {
            'fields': (
                'telefone', 'telefone_alternativo',
                'email', 'email_alternativo'
            )
        }),
        ('Endereço', {
            'fields': (
                'endereco', 'cidade', 'estado', 'cep'
            ),
            'classes': ('collapse',)
        }),
        ('Informações Empresariais', {
            'fields': (
                'empresa', 'cargo', 'setor'
            )
        }),
        ('Redes Sociais', {
            'fields': (
                'linkedin', 'facebook', 'instagram'
            ),
            'classes': ('collapse',)
        }),
        ('Informações Comerciais', {
            'fields': (
                'valor_estimado', 'probabilidade',
                'observacoes'
            )
        }),
        ('Controle de Funil', {
            'fields': (
                'funil', 'etapa', 'data_entrada_etapa',
                'tempo_na_etapa_display', 'usuario'
            )
        }),
        ('Organização', {
            'fields': ('tags',)
        }),
        ('Timestamps', {
            'fields': (
                'criado_em', 'atualizado_em', 'ultimo_contato'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def status_prazo(self, obj):
        if obj.esta_atrasado():
            return format_html(
                '<span style="color: red;">⚠️ Atrasado {:.0f}h</span>',
                obj.horas_atraso()
            )
        return format_html('<span style="color: green;">✓ No prazo</span>')
    status_prazo.short_description = 'Status Prazo'
    
    def tempo_na_etapa_display(self, obj):
        return f"{obj.horas_na_etapa():.1f} horas"
    tempo_na_etapa_display.short_description = 'Tempo na Etapa'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(usuario=request.user)


@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display = [
        'titulo', 'tipo', 'status', 'prioridade',
        'cliente_link', 'responsavel', 'data_vencimento',
        'status_vencimento', 'usuario'
    ]
    list_filter = [
        'status', 'prioridade', 'tipo',
        'responsavel', 'criado_em'
    ]
    search_fields = ['titulo', 'descricao', 'cliente__nome']
    readonly_fields = ['criado_em', 'atualizado_em', 'data_conclusao']
    filter_horizontal = ['tags']
    date_hierarchy = 'data_vencimento'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': (
                'titulo', 'descricao', 'tipo',
                'status', 'prioridade'
            )
        }),
        ('Relacionamentos', {
            'fields': (
                'cliente', 'usuario', 'responsavel', 'tags'
            )
        }),
        ('Prazos', {
            'fields': (
                'data_vencimento', 'lembrete',
                'data_conclusao'
            )
        }),
        ('Controle de Tempo', {
            'fields': (
                'tempo_estimado', 'tempo_gasto'
            )
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def cliente_link(self, obj):
        if obj.cliente:
            url = reverse('admin:crm_cliente_change', args=[obj.cliente.id])
            return format_html('<a href="{}">{}</a>', url, obj.cliente.nome)
        return '-'
    cliente_link.short_description = 'Cliente'
    
    def status_vencimento(self, obj):
        if obj.status == 'concluida':
            return format_html('<span style="color: green;">✓ Concluída</span>')
        elif obj.esta_vencida():
            return format_html('<span style="color: red;">⚠️ Vencida</span>')
        elif obj.dias_ate_vencimento() <= 1:
            return format_html('<span style="color: orange;">⚡ Urgente</span>')
        return format_html('<span style="color: blue;">⏰ No prazo</span>')
    status_vencimento.short_description = 'Status'


@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = [
        'titulo', 'tipo', 'cliente_link', 'resultado',
        'duracao_minutos', 'usuario', 'data_atividade'
    ]
    list_filter = [
        'tipo', 'resultado', 'usuario',
        'data_atividade', 'criado_em'
    ]
    search_fields = ['titulo', 'descricao', 'cliente__nome']
    readonly_fields = ['criado_em']
    date_hierarchy = 'data_atividade'
    
    fieldsets = (
        ('Informações', {
            'fields': (
                'tipo', 'titulo', 'descricao', 'resultado'
            )
        }),
        ('Relacionamentos', {
            'fields': ('cliente', 'usuario', 'tarefa')
        }),
        ('Tempo', {
            'fields': ('duracao_minutos', 'data_atividade')
        }),
        ('Metadata', {
            'fields': ('criado_em',),
            'classes': ('collapse',)
        }),
    )
    
    def cliente_link(self, obj):
        url = reverse('admin:crm_cliente_change', args=[obj.cliente.id])
        return format_html('<a href="{}">{}</a>', url, obj.cliente.nome)
    cliente_link.short_description = 'Cliente'


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 'tipo', 'cliente_link', 'tamanho_formatado',
        'usuario', 'criado_em'
    ]
    list_filter = ['tipo', 'usuario', 'criado_em']
    search_fields = ['nome', 'descricao', 'cliente__nome']
    readonly_fields = ['criado_em', 'tamanho']
    
    fieldsets = (
        ('Informações', {
            'fields': ('nome', 'tipo', 'descricao')
        }),
        ('Arquivo', {
            'fields': ('arquivo', 'tamanho')
        }),
        ('Relacionamentos', {
            'fields': ('cliente', 'usuario')
        }),
        ('Metadata', {
            'fields': ('criado_em',),
            'classes': ('collapse',)
        }),
    )
    
    def cliente_link(self, obj):
        url = reverse('admin:crm_cliente_change', args=[obj.cliente.id])
        return format_html('<a href="{}">{}</a>', url, obj.cliente.nome)
    cliente_link.short_description = 'Cliente'


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = [
        'assunto', 'tipo', 'destinatario',
        'cliente_link', 'status_leitura', 'criado_em'
    ]
    list_filter = ['tipo', 'lido', 'respondido', 'criado_em']
    search_fields = [
        'assunto', 'corpo', 'destinatario',
        'remetente', 'cliente__nome'
    ]
    readonly_fields = ['criado_em', 'enviado_em']
    
    fieldsets = (
        ('Email', {
            'fields': (
                'tipo', 'assunto', 'corpo',
                'destinatario', 'remetente'
            )
        }),
        ('Status', {
            'fields': ('lido', 'respondido')
        }),
        ('Relacionamentos', {
            'fields': ('cliente', 'usuario')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'enviado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def cliente_link(self, obj):
        url = reverse('admin:crm_cliente_change', args=[obj.cliente.id])
        return format_html('<a href="{}">{}</a>', url, obj.cliente.nome)
    cliente_link.short_description = 'Cliente'
    
    def status_leitura(self, obj):
        if obj.lido:
            return format_html('<span style="color: green;">✓ Lido</span>')
        return format_html('<span style="color: gray;">○ Não lido</span>')
    status_leitura.short_description = 'Status'


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = [
        'titulo_display', 'cliente_link', 'fixada',
        'usuario', 'criado_em'
    ]
    list_filter = ['fixada', 'usuario', 'criado_em']
    search_fields = ['titulo', 'conteudo', 'cliente__nome']
    readonly_fields = ['criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Nota', {
            'fields': ('titulo', 'conteudo', 'fixada')
        }),
        ('Relacionamentos', {
            'fields': ('cliente', 'usuario')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def titulo_display(self, obj):
        return obj.titulo or f"Nota #{obj.id}"
    titulo_display.short_description = 'Título'
    
    def cliente_link(self, obj):
        url = reverse('admin:crm_cliente_change', args=[obj.cliente.id])
        return format_html('<a href="{}">{}</a>', url, obj.cliente.nome)
    cliente_link.short_description = 'Cliente'


@admin.register(Meta)
class MetaAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 'periodo', 'progresso_display',
        'valor_alvo', 'valor_atual',
        'percentual_atingido_display', 'usuario'
    ]
    list_filter = ['periodo', 'usuario', 'data_inicio']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['criado_em']
    date_hierarchy = 'data_inicio'
    
    fieldsets = (
        ('Informações', {
            'fields': ('nome', 'descricao', 'periodo')
        }),
        ('Valores', {
            'fields': ('valor_alvo', 'valor_atual')
        }),
        ('Período', {
            'fields': ('data_inicio', 'data_fim')
        }),
        ('Relacionamentos', {
            'fields': ('usuario',)
        }),
        ('Metadata', {
            'fields': ('criado_em',),
            'classes': ('collapse',)
        }),
    )
    
    def progresso_display(self, obj):
        percentual = obj.percentual_atingido()
        if percentual >= 100:
            color = 'green'
        elif percentual >= 75:
            color = 'blue'
        elif percentual >= 50:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<div style="width: 100px; background-color: #eee; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px;"></div>'
            '</div>',
            min(percentual, 100), color
        )
    progresso_display.short_description = 'Progresso'
    
    def percentual_atingido_display(self, obj):
        return f"{obj.percentual_atingido():.1f}%"
    percentual_atingido_display.short_description = '% Atingido'


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 'codigo', 'preco', 'custo',
        'margem_display', 'categoria', 'ativo'
    ]
    list_filter = ['ativo', 'categoria', 'usuario']
    search_fields = ['nome', 'codigo', 'descricao']
    readonly_fields = ['criado_em']
    
    fieldsets = (
        ('Informações', {
            'fields': ('nome', 'descricao', 'codigo', 'categoria')
        }),
        ('Valores', {
            'fields': ('preco', 'custo')
        }),
        ('Controle', {
            'fields': ('ativo', 'usuario')
        }),
        ('Metadata', {
            'fields': ('criado_em',),
            'classes': ('collapse',)
        }),
    )
    
    def margem_display(self, obj):
        margem = obj.margem()
        if margem >= 50:
            color = 'green'
        elif margem >= 30:
            color = 'blue'
        elif margem >= 10:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, margem
        )
    margem_display.short_description = 'Margem'


class ItemPropostaInline(admin.TabularInline):
    model = ItemProposta
    extra = 1
    fields = ['produto', 'quantidade', 'preco_unitario', 'desconto', 'subtotal_display']
    readonly_fields = ['subtotal_display']
    
    def subtotal_display(self, obj):
        if obj.pk:
            return f"R$ {obj.subtotal():.2f}"
        return "-"
    subtotal_display.short_description = 'Subtotal'


@admin.register(Proposta)
class PropostaAdmin(admin.ModelAdmin):
    list_display = [
        'numero', 'titulo', 'cliente_link', 'status',
        'valor_total', 'desconto', 'valor_final_display',
        'data_validade', 'usuario'
    ]
    list_filter = ['status', 'usuario', 'criado_em']
    search_fields = ['numero', 'titulo', 'cliente__nome']
    readonly_fields = ['criado_em', 'data_aceite']
    inlines = [ItemPropostaInline]
    date_hierarchy = 'criado_em'
    
    fieldsets = (
        ('Informações', {
            'fields': ('numero', 'titulo', 'descricao', 'status')
        }),
        ('Valores', {
            'fields': ('valor_total', 'desconto')
        }),
        ('Relacionamentos', {
            'fields': ('cliente', 'usuario')
        }),
        ('Datas', {
            'fields': ('data_validade', 'data_aceite')
        }),
        ('Metadata', {
            'fields': ('criado_em',),
            'classes': ('collapse',)
        }),
    )
    
    def cliente_link(self, obj):
        url = reverse('admin:crm_cliente_change', args=[obj.cliente.id])
        return format_html('<a href="{}">{}</a>', url, obj.cliente.nome)
    cliente_link.short_description = 'Cliente'
    
    def valor_final_display(self, obj):
        return f"R$ {obj.valor_final():.2f}"
    valor_final_display.short_description = 'Valor Final'


# Customização do Admin Site
admin.site.site_header = "CRM Avançado - Administração"
admin.site.site_title = "CRM Admin"
admin.site.index_title = "Painel de Controle"