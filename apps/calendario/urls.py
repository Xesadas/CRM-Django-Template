from django.urls import path
from . import views

app_name = 'calendario'

urlpatterns = [
    path('', views.calendario_tarefas, name='calendario'),
    path('dia-detalhes/', views.dia_detalhes, name='dia_detalhes'),
    path('tarefas-mes/', views.tarefas_mes, name='tarefas_mes'),
    
    path('tarefa/criar/', views.criar_tarefa, name='criar_tarefa'),
    path('tarefa/<int:tarefa_id>/editar/', views.editar_tarefa, name='editar_tarefa'),
    path('tarefa/<int:tarefa_id>/alternar-status/', views.alternar_status_tarefa, name='alternar_status_tarefa'),
    path('tarefa/<int:tarefa_id>/excluir/', views.excluir_tarefa, name='excluir_tarefa'),
    
    path('categorias/', views.listar_categorias, name='listar_categorias'),
    path('criar-categoria/', views.criar_categoria, name='criar_categoria'),
]