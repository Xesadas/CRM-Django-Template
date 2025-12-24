import logging
from collections import defaultdict
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.utils import timezone
from datetime import datetime, date, timedelta
import calendar
import json
from .models import Tarefa, CategoriaTarefa

# Configurar logger
logger = logging.getLogger(__name__)

MESES_PORTUGUES = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

@login_required
def calendario_tarefas(request):
    """Calendário de tarefas"""
    
    logger.info("CALENDÁRIO DE TAREFAS: Iniciando processamento")
    
    hoje = timezone.now().date()
    ano = int(request.GET.get('ano', hoje.year))
    mes = int(request.GET.get('mes', hoje.month))
    
    # Navegação entre meses
    if request.GET.get('mes_anterior'):
        mes -= 1
        if mes < 1:
            mes = 12
            ano -= 1
    elif request.GET.get('proximo_mes'):
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1
    
    # Gerar calendário
    cal = calendar.monthcalendar(ano, mes)
    mes_nome = MESES_PORTUGUES[mes]
    
    logger.info(f"Consulta: {mes_nome}/{ano}")
    
    # Buscar tarefas do usuário para o mês
    tarefas = Tarefa.objects.filter(
        usuario=request.user,
        data_vencimento__year=ano,
        data_vencimento__month=mes
    ).select_related('categoria')
    
    # Organizar tarefas por dia
    tarefas_por_dia = {}
    
    for tarefa in tarefas:
        dia = tarefa.data_vencimento.day
        
        if dia not in tarefas_por_dia:
            tarefas_por_dia[dia] = []
        
        tarefas_por_dia[dia].append({
            'id': tarefa.id,
            'titulo': tarefa.titulo,
            'descricao': tarefa.descricao,
            'data_vencimento': tarefa.data_vencimento,
            'prioridade': tarefa.prioridade,
            'status': tarefa.status,
            'status_display': tarefa.get_status_display(),
            'esta_atrasada': tarefa.esta_atrasada,
            'categoria': tarefa.categoria.nome if tarefa.categoria else 'Sem Categoria',
            'cor_categoria': tarefa.categoria.cor if tarefa.categoria else '#6c757d',
        })
    
    # Contadores para o resumo
    total_tarefas = tarefas.count()
    tarefas_pendentes = tarefas.filter(status='pendente').count()
    tarefas_concluidas = tarefas.filter(status='concluida').count()
    tarefas_atrasadas = sum(1 for t in tarefas if t.esta_atrasada)
    
    context = {
        'cal': cal,
        'ano': ano,
        'mes': mes,
        'mes_nome': mes_nome,
        'hoje': hoje,
        'tarefas_por_dia': tarefas_por_dia,
        'total_tarefas': total_tarefas,
        'tarefas_pendentes': tarefas_pendentes,
        'tarefas_concluidas': tarefas_concluidas,
        'tarefas_atrasadas': tarefas_atrasadas,
    }
    
    return render(request, 'calendario/calendario.html', context)

@login_required
@require_GET
def dia_detalhes(request):
    """Retorna detalhes das tarefas para um dia específico"""
    try:
        dia = int(request.GET.get('dia'))
        mes = int(request.GET.get('mes'))
        ano = int(request.GET.get('ano'))
        
        data_referencia = date(ano, mes, dia)
        
        tarefas = Tarefa.objects.filter(
            usuario=request.user,
            data_vencimento__year=ano,
            data_vencimento__month=mes,
            data_vencimento__day=dia
        ).select_related('categoria')
        
        tarefas_data = []
        
        for tarefa in tarefas:
            tarefas_data.append({
                'id': tarefa.id,
                'titulo': tarefa.titulo,
                'descricao': tarefa.descricao,
                'data_vencimento': tarefa.data_vencimento.strftime('%d/%m/%Y'),
                'prioridade': tarefa.prioridade,
                'prioridade_display': tarefa.get_prioridade_display(),
                'status': tarefa.status,
                'status_display': tarefa.get_status_display(),
                'esta_atrasada': tarefa.esta_atrasada,
                'categoria': tarefa.categoria.nome if tarefa.categoria else 'Sem Categoria',
                'cor_categoria': tarefa.categoria.cor if tarefa.categoria else '#6c757d',
            })
        
        return JsonResponse({'tarefas': tarefas_data})
        
    except Exception as e:
        logger.error(f"ERRO em dia_detalhes: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_POST
def alternar_status_tarefa(request, tarefa_id):
    """Alterna o status de uma tarefa entre concluída e pendente"""
    try:
        tarefa = Tarefa.objects.get(id=tarefa_id, usuario=request.user)
        
        if tarefa.status == 'concluida':
            tarefa.status = 'pendente'
            tarefa.data_conclusao = None
        else:
            tarefa.status = 'concluida'
            tarefa.data_conclusao = timezone.now().date()
        
        tarefa.save()
        
        return JsonResponse({
            'success': True,
            'status': tarefa.status,
            'status_display': tarefa.get_status_display(),
            'message': f'Tarefa marcada como {tarefa.get_status_display()}'
        })
        
    except Tarefa.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Tarefa não encontrada'})
    except Exception as e:
        logger.error(f"ERRO em alternar_status_tarefa: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def criar_tarefa(request):
    """Cria uma nova tarefa"""
    try:
        titulo = request.POST.get('titulo', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        data_vencimento = request.POST.get('data_vencimento', '')
        prioridade = request.POST.get('prioridade', 'media')
        categoria_id = request.POST.get('categoria', None)
        
        if not titulo or not data_vencimento:
            raise ValueError("Título e data de vencimento são obrigatórios")
        
        # Converter data
        data_obj = datetime.strptime(data_vencimento, '%Y-%m-%d').date()
        
        # Obter categoria se fornecida
        categoria = None
        if categoria_id:
            categoria = CategoriaTarefa.objects.get(id=categoria_id, usuario=request.user)
        
        # Criar tarefa
        tarefa = Tarefa.objects.create(
            usuario=request.user,
            titulo=titulo,
            descricao=descricao,
            data_vencimento=data_obj,
            prioridade=prioridade,
            categoria=categoria,
            status='pendente'
        )
        
        logger.info(f"Tarefa criada: {tarefa.titulo}")
        
        return JsonResponse({
            'success': True,
            'message': 'Tarefa criada com sucesso!',
            'tarefa_id': tarefa.id
        })
        
    except ValueError as ve:
        return JsonResponse({'success': False, 'error': str(ve)})
    except Exception as e:
        logger.error(f"ERRO em criar_tarefa: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_GET
def listar_categorias(request):
    """Lista categorias do usuário"""
    try:
        categorias = CategoriaTarefa.objects.filter(
            usuario=request.user
        ).values('id', 'nome', 'cor')
        
        return JsonResponse({
            'categorias': list(categorias)
        })
        
    except Exception as e:
        logger.error(f"ERRO em listar_categorias: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_POST
def criar_categoria(request):
    """Cria nova categoria de tarefa"""
    try:
        nome = request.POST.get('nome', '').strip()
        cor = request.POST.get('cor', '#000000')
        
        if not nome:
            raise ValueError("Nome da categoria é obrigatório")
        
        categoria = CategoriaTarefa.objects.create(
            usuario=request.user,
            nome=nome,
            cor=cor
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Categoria criada com sucesso!',
            'categoria': {
                'id': categoria.id,
                'nome': categoria.nome,
                'cor': categoria.cor
            }
        })
        
    except Exception as e:
        logger.error(f"ERRO em criar_categoria: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_POST
def excluir_tarefa(request, tarefa_id):
    """Exclui uma tarefa"""
    try:
        tarefa = Tarefa.objects.get(id=tarefa_id, usuario=request.user)
        tarefa.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Tarefa excluída com sucesso'
        })
        
    except Tarefa.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Tarefa não encontrada'
        }, status=404)
    except Exception as e:
        logger.error(f"ERRO em excluir_tarefa: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=500)

@login_required
@require_GET
def tarefas_mes(request):
    """Retorna todas as tarefas do mês organizadas por dia"""
    try:
        mes = int(request.GET.get('mes', datetime.now().month))
        ano = int(request.GET.get('ano', datetime.now().year))
        
        tarefas = Tarefa.objects.filter(
            usuario=request.user,
            data_vencimento__year=ano,
            data_vencimento__month=mes
        ).select_related('categoria')
        
        # Organizar por dia
        tarefas_por_dia = defaultdict(list)
        
        for tarefa in tarefas:
            dia = tarefa.data_vencimento.day
            
            tarefas_por_dia[dia].append({
                'id': tarefa.id,
                'titulo': tarefa.titulo,
                'descricao': tarefa.descricao,
                'data_vencimento': tarefa.data_vencimento.strftime('%d/%m/%Y'),
                'prioridade': tarefa.prioridade,
                'prioridade_display': tarefa.get_prioridade_display(),
                'status': tarefa.status,
                'status_display': tarefa.get_status_display(),
                'esta_atrasada': tarefa.esta_atrasada,
                'categoria': tarefa.categoria.nome if tarefa.categoria else 'Sem Categoria',
                'cor_categoria': tarefa.categoria.cor if tarefa.categoria else '#6c757d',
            })
        
        return JsonResponse({
            'success': True,
            'tarefas_por_dia': dict(tarefas_por_dia),
            'mes': mes,
            'ano': ano
        })
        
    except Exception as e:
        logger.error(f"ERRO em tarefas_mes: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_http_methods(["GET", "POST"])
def editar_tarefa(request, tarefa_id):
    """Edita uma tarefa existente"""
    try:
        tarefa = Tarefa.objects.get(id=tarefa_id, usuario=request.user)
        
        if request.method == 'GET':
            return JsonResponse({
                'success': True,
                'tarefa': {
                    'id': tarefa.id,
                    'titulo': tarefa.titulo,
                    'descricao': tarefa.descricao,
                    'data_vencimento': tarefa.data_vencimento.strftime('%Y-%m-%d'),
                    'prioridade': tarefa.prioridade,
                    'status': tarefa.status,
                    'categoria_id': tarefa.categoria.id if tarefa.categoria else None,
                }
            })
            
        elif request.method == 'POST':
            # Atualizar tarefa
            tarefa.titulo = request.POST.get('titulo', tarefa.titulo)
            tarefa.descricao = request.POST.get('descricao', tarefa.descricao)
            tarefa.prioridade = request.POST.get('prioridade', tarefa.prioridade)
            tarefa.status = request.POST.get('status', tarefa.status)
            
            # Data de vencimento
            nova_data = request.POST.get('data_vencimento', None)
            if nova_data:
                tarefa.data_vencimento = datetime.strptime(nova_data, '%Y-%m-%d').date()
            
            # Categoria
            categoria_id = request.POST.get('categoria_id', None)
            if categoria_id:
                tarefa.categoria = CategoriaTarefa.objects.get(id=categoria_id, usuario=request.user)
            else:
                tarefa.categoria = None
            
            tarefa.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Tarefa atualizada com sucesso!'
            })
                
    except Tarefa.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Tarefa não encontrada'
        }, status=404)
    except Exception as e:
        logger.error(f"ERRO em editar_tarefa: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Erro ao editar tarefa: {str(e)}'
        }, status=500)