from django.contrib import admin
from .models import Tarefa, CategoriaTarefa

@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data_vencimento', 'prioridade', 'status', 'usuario')
    list_filter = ('data_vencimento', 'prioridade', 'status')
    search_fields = ('titulo', 'descricao')
    date_hierarchy = 'data_vencimento'
    
    fieldsets = (
        ('Informações da Tarefa', {
            'fields': ('titulo', 'descricao', 'data_vencimento')
        }),
        ('Categorização', {
            'fields': ('prioridade', 'status', 'categoria')
        }),
        ('Usuário', {
            'fields': ('usuario', 'atribuido_a')
        }),
    )

@admin.register(CategoriaTarefa)
class CategoriaTarefaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'usuario', 'cor')
    list_filter = ('usuario',)
    search_fields = ('nome',)