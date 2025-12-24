from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Funil de Vendas
    path('funil/', views.funil_vendas, name='funil_vendas'),
    path('mover-cliente/', views.mover_cliente, name='mover_cliente'),
    
    # Clientes
    path('cadastro/', views.cadastro_cliente, name='cadastro_cliente'),
    path('cliente/<int:cliente_id>/', views.cliente_detalhes, name='cliente_detalhes'),
    path('editar-cliente/<int:cliente_id>/', views.editar_cliente, name='editar_cliente'),
    path('excluir-cliente/<int:cliente_id>/', views.excluir_cliente, name='excluir_cliente'),
    
    # Tarefas
    path('tarefas/', views.tarefas_list, name='tarefas_list'),
    path('tarefas/criar/', views.tarefa_criar, name='tarefa_criar'),
    path('tarefas/<int:tarefa_id>/concluir/', views.tarefa_concluir, name='tarefa_concluir'),
    path('tarefas/<int:tarefa_id>/editar/', views.tarefa_editar, name='tarefa_editar'),
    path('tarefas/<int:tarefa_id>/excluir/', views.tarefa_excluir, name='tarefa_excluir'),
    path('tarefas/mover/', views.mover_tarefa, name='mover_tarefa'),
    
    # Atividades
    path('cliente/<int:cliente_id>/atividade/', views.atividade_criar, name='atividade_criar'),
    path('atividade/<int:atividade_id>/editar/', views.atividade_editar, name='atividade_editar'),
    
    # Notas
    path('cliente/<int:cliente_id>/nota/', views.nota_criar, name='nota_criar'),
    path('nota/<int:nota_id>/editar/', views.nota_editar, name='nota_editar'),
    path('nota/<int:nota_id>/excluir/', views.nota_excluir, name='nota_excluir'),
    
    # Documentos
    path('cliente/<int:cliente_id>/documento/', views.documento_upload, name='documento_upload'),
    path('documento/<int:documento_id>/download/', views.documento_download, name='documento_download'),
    path('documento/<int:documento_id>/excluir/', views.documento_excluir, name='documento_excluir'),
    
    # Emails
    path('cliente/<int:cliente_id>/email/', views.email_criar, name='email_criar'),
    path('emails/', views.emails_list, name='emails_list'),
    
    # Propostas
    path('cliente/<int:cliente_id>/proposta/', views.proposta_criar, name='proposta_criar'),
    path('proposta/<int:proposta_id>/', views.proposta_detalhes, name='proposta_detalhes'),
    path('proposta/<int:proposta_id>/pdf/', views.proposta_pdf, name='proposta_pdf'),
    
    # Produtos
    path('produtos/', views.produtos_list, name='produtos_list'),
    path('produtos/criar/', views.produto_criar, name='produto_criar'),
    path('produtos/<int:produto_id>/editar/', views.produto_editar, name='produto_editar'),
    
    # Funis
    path('funis/', views.gerenciar_funis, name='gerenciar_funis'),
    path('funis/criar/', views.funil_criar, name='funil_criar'),
    path('funis/<int:funil_id>/editar/', views.funil_editar, name='funil_editar'),
    path('funis/<int:funil_id>/excluir/', views.funil_excluir, name='funil_excluir'),
    
    # Metas
    path('metas/', views.metas_list, name='metas_list'),
    path('metas/criar/', views.meta_criar, name='meta_criar'),
    path('metas/<int:meta_id>/editar/', views.meta_editar, name='meta_editar'),
    
    # Tags
    path('tags/', views.tags_list, name='tags_list'),
    path('tags/criar/', views.tag_criar, name='tag_criar'),
    
    # Relatórios
    path('relatorios/', views.relatorios, name='relatorios'),
    path('relatorios/vendas/', views.relatorio_vendas, name='relatorio_vendas'),
    path('relatorios/atividades/', views.relatorio_atividades, name='relatorio_atividades'),
    path('relatorios/funil/', views.relatorio_funil, name='relatorio_funil'),
    path('relatorios/exportar/', views.relatorio_exportar, name='relatorio_exportar'),
    
    # Calendário
    path('calendario/', views.calendario, name='calendario'),
    
    # Busca
    path('busca/', views.busca_global, name='busca_global'),
    
    # Admin
    path('admin/', views.admin_crm, name='admin_crm'),
    
    # API endpoints (para AJAX)
    path('api/cliente/<int:cliente_id>/info/', views.api_cliente_info, name='api_cliente_info'),
    path('api/tarefas/stats/', views.api_tarefas_stats, name='api_tarefas_stats'),
    path('api/pipeline/stats/', views.api_pipeline_stats, name='api_pipeline_stats'),
]