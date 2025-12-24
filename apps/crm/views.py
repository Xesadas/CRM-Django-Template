from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q, Count, Sum
from datetime import datetime, timedelta
import json
from .models import *
from .forms import *


# ==================== DASHBOARD ====================
@login_required
def dashboard(request):
    """Dashboard principal com métricas e gráficos"""
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)
    
    # Métricas gerais
    total_clientes = Cliente.objects.filter(usuario=request.user).count()
    total_tarefas_pendentes = Tarefa.objects.filter(
        usuario=request.user, 
        status__in=['pendente', 'em_andamento']
    ).count()
    
    tarefas_vencidas = Tarefa.objects.filter(
        usuario=request.user,
        status__in=['pendente', 'em_andamento'],
        data_vencimento__lt=timezone.now()
    ).count()
    
    tarefas_hoje = Tarefa.objects.filter(
        usuario=request.user,
        status__in=['pendente', 'em_andamento'],
        data_vencimento__date=hoje
    )
    
    # Clientes por etapa
    clientes_por_etapa = {}
    funis = Funil.objects.filter(usuario=request.user, ativo=True)
    for funil in funis:
        for etapa in funil.etapas:
            count = Cliente.objects.filter(
                usuario=request.user,
                funil=funil,
                etapa=etapa
            ).count()
            if count > 0:
                clientes_por_etapa[f"{funil.nome} - {etapa}"] = count
    
    valor_pipeline = Cliente.objects.filter(
        usuario=request.user
    ).aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0
    
    atividades_recentes = Atividade.objects.filter(
        usuario=request.user
    ).select_related('cliente')[:10]
    
    clientes_atrasados = []
    for cliente in Cliente.objects.filter(usuario=request.user):
        if cliente.esta_atrasado():
            clientes_atrasados.append(cliente)
    
    conversoes_mes = Cliente.objects.filter(
        usuario=request.user,
        atualizado_em__gte=inicio_mes
    ).count()
    
    metas_ativas = Meta.objects.filter(
        usuario=request.user,
        data_inicio__lte=hoje,
        data_fim__gte=hoje
    )
    
    context = {
        'total_clientes': total_clientes,
        'total_tarefas_pendentes': total_tarefas_pendentes,
        'tarefas_vencidas': tarefas_vencidas,
        'tarefas_hoje': tarefas_hoje,
        'clientes_por_etapa': json.dumps(clientes_por_etapa),
        'valor_pipeline': valor_pipeline,
        'atividades_recentes': atividades_recentes,
        'clientes_atrasados': clientes_atrasados[:5],
        'conversoes_mes': conversoes_mes,
        'metas_ativas': metas_ativas,
    }
    
    return render(request, 'crm/dashboard.html', context)


# ==================== CRM DASHBOARD (Redirect) ====================
@login_required
def crm_dashboard(request):
    """Página inicial do CRM - redireciona para funil"""
    return redirect('crm:funil_vendas')


# ==================== FUNIL DE VENDAS ====================
@login_required
def funil_vendas(request):
    """View principal - Kanban board"""
    funis_usuario = Funil.objects.filter(usuario=request.user, ativo=True)
    funis_selecionados_ids = request.GET.getlist('funis_selecionados')
    
    if not funis_selecionados_ids and funis_usuario.exists():
        funis_selecionados_ids = [str(f.id) for f in funis_usuario]
    
    funis_para_exibir = []
    for funil in funis_usuario:
        if str(funil.id) in funis_selecionados_ids:
            clientes = Cliente.objects.filter(
                funil=funil,
                usuario=request.user
            ).select_related('funil').prefetch_related('tags')
            
            contagem = {}
            for etapa in funil.etapas:
                contagem[etapa] = clientes.filter(etapa=etapa).count()
            
            funil.dados_clientes = clientes
            funil.total_clientes = clientes.count()
            funil.contagem_por_etapa = contagem
            funis_para_exibir.append(funil)
    
    context = {
        'todos_funis': funis_usuario,
        'funis_selecionados_ids': funis_selecionados_ids,
        'funis_para_exibir': funis_para_exibir,
    }
    
    return render(request, 'crm/funil.html', context)


@login_required
@require_POST
def mover_cliente(request):
    """Move cliente entre etapas via drag & drop"""
    try:
        data = json.loads(request.body)
        cliente_id = data.get('cliente_id')
        nova_etapa = data.get('nova_etapa')
        novo_funil_id = data.get('novo_funil_id')
        
        cliente = get_object_or_404(Cliente, id=cliente_id, usuario=request.user)
        etapa_anterior = cliente.etapa
        
        if novo_funil_id:
            novo_funil = get_object_or_404(Funil, id=novo_funil_id, usuario=request.user)
            cliente.funil = novo_funil
        
        if nova_etapa not in cliente.funil.etapas:
            return JsonResponse({
                'success': False, 
                'error': f'Etapa "{nova_etapa}" não existe no funil'
            })
        
        cliente.etapa = nova_etapa
        cliente.data_entrada_etapa = timezone.now()
        cliente.save()
        
        # Registrar atividade
        Atividade.objects.create(
            tipo='nota',
            titulo=f'Cliente movido de {etapa_anterior} para {nova_etapa}',
            descricao=f'Cliente movido automaticamente via drag & drop',
            cliente=cliente,
            usuario=request.user
        )
        
        if request.headers.get('HX-Request'):
            from django.template.loader import render_to_string
            card_html = render_to_string('crm/partials/cliente_card.html', {
                'cliente': cliente,
                'funil': cliente.funil
            })
            return HttpResponse(card_html)
        
        return JsonResponse({
            'success': True,
            'message': f'Cliente movido para {nova_etapa}'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ==================== CLIENTES ====================
@login_required
def cadastro_cliente(request):
    """Cadastrar novo cliente"""
    if request.method == 'POST':
        form = ClienteForm(request.POST, user=request.user)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.usuario = request.user
            
            # Se não tiver etapa definida, usar primeira do funil
            if not cliente.etapa and cliente.funil:
                cliente.etapa = cliente.funil.etapas[0] if cliente.funil.etapas else "Nova"
            
            cliente.save()
            form.save_m2m()  # Salvar tags
            
            messages.success(request, f'Cliente {cliente.nome} cadastrado com sucesso!')
            return redirect('crm:funil_vendas')
    else:
        form = ClienteForm(user=request.user)
    
    return render(request, 'crm/cadastro_cliente.html', {'form': form})


@login_required
def cliente_detalhes(request, cliente_id):
    """Detalhes completos do cliente"""
    cliente = get_object_or_404(
        Cliente.objects.select_related('funil', 'usuario').prefetch_related('tags'),
        id=cliente_id,
        usuario=request.user
    )
    
    atividades = cliente.atividades.all().order_by('-data_atividade')
    tarefas = cliente.tarefas.filter(
        status__in=['pendente', 'em_andamento']
    ).order_by('data_vencimento')
    documentos = cliente.documentos.all().order_by('-criado_em')
    notas = cliente.notas.all()
    propostas = cliente.propostas.all().order_by('-criado_em')
    
    context = {
        'cliente': cliente,
        'atividades': atividades,
        'tarefas': tarefas,
        'documentos': documentos,
        'notas': notas,
        'propostas': propostas,
    }
    
    return render(request, 'crm/cliente/detalhes.html', context)


@login_required
def editar_cliente(request, cliente_id):
    """Editar cliente"""
    cliente = get_object_or_404(Cliente, id=cliente_id, usuario=request.user)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente atualizado com sucesso!')
            return redirect('crm:cliente_detalhes', cliente_id=cliente.id)
    else:
        form = ClienteForm(instance=cliente, user=request.user)
    
    funis = Funil.objects.filter(usuario=request.user)
    funis_json = {funil.id: funil.etapas for funil in funis}
    
    context = {
        'form': form,
        'cliente': cliente,
        'funis': funis,
        'etapas_funil': cliente.funil.etapas,
        'funis_json': json.dumps(funis_json),
    }
    
    return render(request, 'crm/editar_cliente.html', context)


@login_required
def excluir_cliente(request, cliente_id):
    """Excluir cliente"""
    cliente = get_object_or_404(Cliente, id=cliente_id, usuario=request.user)
    nome = cliente.nome
    cliente.delete()
    messages.success(request, f'Cliente {nome} excluído!')
    return redirect('crm:funil_vendas')


# ==================== TAREFAS ====================
# ==================== TAREFAS (KANBAN) ====================
@login_required
def tarefas_list(request):
    """Kanban board de tarefas"""
    # Filtros
    status_filtro = request.GET.getlist('status_filtro', ['pendente', 'em_andamento'])
    prioridade_filtro = request.GET.getlist('prioridade_filtro')
    
    # Tarefas base
    tarefas = Tarefa.objects.filter(usuario=request.user)
    
    # Aplicar filtros
    if status_filtro:
        tarefas = tarefas.filter(status__in=status_filtro)
    if prioridade_filtro:
        tarefas = tarefas.filter(prioridade__in=prioridade_filtro)
    
    # Cliente específico (se fornecido)
    cliente_id = request.GET.get('cliente_id')
    if cliente_id:
        cliente = get_object_or_404(Cliente, id=cliente_id, usuario=request.user)
        tarefas = tarefas.filter(cliente=cliente)
    
    # Organizar por colunas
    tarefas_pendentes = tarefas.filter(status='pendente').order_by('prioridade', 'data_vencimento')
    tarefas_em_andamento = tarefas.filter(status='em_andamento').order_by('prioridade', 'data_vencimento')
    tarefas_concluidas = tarefas.filter(status='concluida').order_by('-data_conclusao')[:50]
    
    # Estatísticas
    stats = {
        'total': tarefas.count(),
        'pendentes': tarefas_pendentes.count(),
        'em_andamento': tarefas_em_andamento.count(),
        'concluidas': tarefas_concluidas.count(),
        'vencidas': tarefas.filter(
            status__in=['pendente', 'em_andamento'],
            data_vencimento__lt=timezone.now()
        ).count(),
    }
    
    context = {
        'tarefas_pendentes': tarefas_pendentes,
        'tarefas_em_andamento': tarefas_em_andamento,
        'tarefas_concluidas': tarefas_concluidas,
        'stats': stats,
        'status_filtro': status_filtro,
        'prioridade_filtro': prioridade_filtro,
        'cliente_id': cliente_id,
    }
    
    return render(request, 'crm/tarefas/kanban.html', context)


@login_required
@require_POST
def mover_tarefa(request):
    """Move tarefa entre status via drag & drop"""
    try:
        data = json.loads(request.body)
        tarefa_id = data.get('tarefa_id')
        novo_status = data.get('novo_status')
        
        tarefa = get_object_or_404(Tarefa, id=tarefa_id, usuario=request.user)
        status_anterior = tarefa.status
        
        # Validar status
        if novo_status not in ['pendente', 'em_andamento', 'concluida', 'cancelada']:
            return JsonResponse({
                'success': False,
                'error': f'Status "{novo_status}" inválido'
            })
        
        tarefa.status = novo_status
        
        # Se concluída, registrar data
        if novo_status == 'concluida':
            tarefa.data_conclusao = timezone.now()
        
        tarefa.save()
        
        # Registrar atividade se vinculada a cliente
        if tarefa.cliente:
            Atividade.objects.create(
                tipo='nota',
                titulo=f'Tarefa movida de {status_anterior} para {novo_status}',
                descricao=f'Tarefa "{tarefa.titulo}" movida via drag & drop',
                cliente=tarefa.cliente,
                usuario=request.user
            )
        
        if request.headers.get('HX-Request'):
            from django.template.loader import render_to_string
            card_html = render_to_string('crm/tarefas/partials/tarefa_card.html', {
                'tarefa': tarefa,
            })
            return HttpResponse(card_html)
        
        return JsonResponse({
            'success': True,
            'message': f'Tarefa movida para {novo_status}'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def tarefa_criar(request):
    """Criar nova tarefa"""
    if request.method == 'POST':
        form = TarefaForm(request.POST, user=request.user)
        if form.is_valid():
            tarefa = form.save(commit=False)
            tarefa.usuario = request.user
            tarefa.save()
            form.save_m2m()
            
            messages.success(request, 'Tarefa criada com sucesso!')
            return redirect('crm:tarefas_list')
    else:
        form = TarefaForm(user=request.user)
    
    return render(request, 'crm/tarefas/criar.html', {'form': form})


@login_required
def tarefa_editar(request, tarefa_id):
    """Editar tarefa"""
    tarefa = get_object_or_404(Tarefa, id=tarefa_id, usuario=request.user)
    
    if request.method == 'POST':
        form = TarefaForm(request.POST, instance=tarefa, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tarefa atualizada!')
            return redirect('crm:tarefas_list')
    else:
        form = TarefaForm(instance=tarefa, user=request.user)
    
    return render(request, 'crm/tarefas/editar.html', {'form': form, 'tarefa': tarefa})


@login_required
@require_POST
def tarefa_concluir(request, tarefa_id):
    """Marcar tarefa como concluída"""
    tarefa = get_object_or_404(Tarefa, id=tarefa_id, usuario=request.user)
    tarefa.status = 'concluida'
    tarefa.data_conclusao = timezone.now()
    tarefa.save()
    
    messages.success(request, f'Tarefa "{tarefa.titulo}" concluída!')
    return redirect('crm:tarefas_list')


@login_required
def tarefa_excluir(request, tarefa_id):
    """Excluir tarefa"""
    tarefa = get_object_or_404(Tarefa, id=tarefa_id, usuario=request.user)
    titulo = tarefa.titulo
    tarefa.delete()
    messages.success(request, f'Tarefa "{titulo}" excluída!')
    return redirect('crm:tarefas_list')


# ==================== ATIVIDADES ====================
@login_required
def atividade_criar(request, cliente_id):
    """Criar nova atividade para cliente"""
    cliente = get_object_or_404(Cliente, id=cliente_id, usuario=request.user)
    
    if request.method == 'POST':
        form = AtividadeForm(request.POST)
        if form.is_valid():
            atividade = form.save(commit=False)
            atividade.cliente = cliente
            atividade.usuario = request.user
            atividade.save()
            
            cliente.ultimo_contato = timezone.now()
            cliente.save()
            
            messages.success(request, 'Atividade registrada!')
            return redirect('crm:cliente_detalhes', cliente_id=cliente.id)
    else:
        form = AtividadeForm()
    
    return render(request, 'crm/atividade/criar.html', {'form': form, 'cliente': cliente})


@login_required
def atividade_editar(request, atividade_id):
    """Editar atividade"""
    atividade = get_object_or_404(Atividade, id=atividade_id, usuario=request.user)
    
    if request.method == 'POST':
        form = AtividadeForm(request.POST, instance=atividade)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atividade atualizada!')
            return redirect('crm:cliente_detalhes', cliente_id=atividade.cliente.id)
    else:
        form = AtividadeForm(instance=atividade)
    
    return render(request, 'crm/atividade/editar.html', {'form': form, 'atividade': atividade})


# ==================== NOTAS ====================
@login_required
def nota_criar(request, cliente_id):
    """Criar nota para cliente"""
    cliente = get_object_or_404(Cliente, id=cliente_id, usuario=request.user)
    
    if request.method == 'POST':
        form = NotaForm(request.POST)
        if form.is_valid():
            nota = form.save(commit=False)
            nota.cliente = cliente
            nota.usuario = request.user
            nota.save()
            messages.success(request, 'Nota criada!')
            return redirect('crm:cliente_detalhes', cliente_id=cliente.id)
    else:
        form = NotaForm()
    
    return render(request, 'crm/nota/criar.html', {'form': form, 'cliente': cliente})


@login_required
def nota_editar(request, nota_id):
    """Editar nota"""
    nota = get_object_or_404(Nota, id=nota_id, usuario=request.user)
    
    if request.method == 'POST':
        form = NotaForm(request.POST, instance=nota)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nota atualizada!')
            return redirect('crm:cliente_detalhes', cliente_id=nota.cliente.id)
    else:
        form = NotaForm(instance=nota)
    
    return render(request, 'crm/nota/editar.html', {'form': form, 'nota': nota})


@login_required
def nota_excluir(request, nota_id):
    """Excluir nota"""
    nota = get_object_or_404(Nota, id=nota_id, usuario=request.user)
    cliente_id = nota.cliente.id
    nota.delete()
    messages.success(request, 'Nota excluída!')
    return redirect('crm:cliente_detalhes', cliente_id=cliente_id)


# ==================== DOCUMENTOS ====================
@login_required
def documento_upload(request, cliente_id):
    """Upload de documento"""
    cliente = get_object_or_404(Cliente, id=cliente_id, usuario=request.user)
    
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.cliente = cliente
            documento.usuario = request.user
            documento.tamanho = request.FILES['arquivo'].size
            documento.save()
            messages.success(request, 'Documento enviado!')
            return redirect('crm:cliente_detalhes', cliente_id=cliente.id)
    else:
        form = DocumentoForm()
    
    return render(request, 'crm/documento/upload.html', {'form': form, 'cliente': cliente})


@login_required
def documento_download(request, documento_id):
    """Download de documento"""
    documento = get_object_or_404(Documento, id=documento_id, cliente__usuario=request.user)
    response = HttpResponse(documento.arquivo, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{documento.nome}"'
    return response


@login_required
def documento_excluir(request, documento_id):
    """Excluir documento"""
    documento = get_object_or_404(Documento, id=documento_id, cliente__usuario=request.user)
    cliente_id = documento.cliente.id
    documento.delete()
    messages.success(request, 'Documento excluído!')
    return redirect('crm:cliente_detalhes', cliente_id=cliente_id)


# ==================== EMAILS ====================
@login_required
def email_criar(request, cliente_id):
    """Criar/enviar email para cliente"""
    cliente = get_object_or_404(Cliente, id=cliente_id, usuario=request.user)
    # Implementar lógica de envio de email
    messages.info(request, 'Funcionalidade de email em desenvolvimento')
    return redirect('crm:cliente_detalhes', cliente_id=cliente.id)


@login_required
def emails_list(request):
    """Lista de emails"""
    emails = Email.objects.filter(usuario=request.user).order_by('-criado_em')
    return render(request, 'crm/email/list.html', {'emails': emails})


# ==================== PROPOSTAS ====================
@login_required
def proposta_criar(request, cliente_id):
    """Criar proposta para cliente"""
    cliente = get_object_or_404(Cliente, id=cliente_id, usuario=request.user)
    produtos = Produto.objects.filter(usuario=request.user, ativo=True)
    
    context = {
        'cliente': cliente,
        'produtos': produtos,
    }
    
    return render(request, 'crm/proposta/criar.html', context)


@login_required
def proposta_detalhes(request, proposta_id):
    """Detalhes da proposta"""
    proposta = get_object_or_404(Proposta, id=proposta_id, usuario=request.user)
    return render(request, 'crm/proposta/detalhes.html', {'proposta': proposta})


@login_required
def proposta_pdf(request, proposta_id):
    """Gerar PDF da proposta"""
    proposta = get_object_or_404(Proposta, id=proposta_id, usuario=request.user)
    # Implementar geração de PDF
    messages.info(request, 'Geração de PDF em desenvolvimento')
    return redirect('crm:proposta_detalhes', proposta_id=proposta.id)


# ==================== PRODUTOS ====================
@login_required
def produtos_list(request):
    """Lista de produtos/serviços"""
    produtos = Produto.objects.filter(usuario=request.user, ativo=True).order_by('nome')
    return render(request, 'crm/produtos/list.html', {'produtos': produtos})


@login_required
def produto_criar(request):
    """Criar produto"""
    messages.info(request, 'Funcionalidade em desenvolvimento')
    return redirect('crm:produtos_list')


@login_required
def produto_editar(request, produto_id):
    """Editar produto"""
    messages.info(request, 'Funcionalidade em desenvolvimento')
    return redirect('crm:produtos_list')


# ==================== FUNIS ====================
@login_required
def gerenciar_funis(request):
    """Criar e gerenciar funis"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'criar':
            form = FunilForm(request.POST)
            if form.is_valid():
                funil = form.save(commit=False)
                funil.usuario = request.user
                funil.save()
                messages.success(request, f'Funil "{funil.nome}" criado!')
                return redirect('crm:gerenciar_funis')
        
        elif action == 'excluir':
            funil_id = request.POST.get('funil_id')
            funil = get_object_or_404(Funil, id=funil_id, usuario=request.user)
            nome = funil.nome
            funil.delete()
            messages.success(request, f'Funil "{nome}" excluído!')
            return redirect('crm:gerenciar_funis')
    
    funis = Funil.objects.filter(usuario=request.user)
    form = FunilForm()
    
    context = {
        'funis': funis,
        'form': form,
    }
    
    return render(request, 'crm/gerenciar_funis.html', context)


@login_required
def funil_criar(request):
    """Criar novo funil"""
    if request.method == 'POST':
        form = FunilForm(request.POST)
        if form.is_valid():
            funil = form.save(commit=False)
            funil.usuario = request.user
            funil.save()
            messages.success(request, f'Funil "{funil.nome}" criado!')
            return redirect('crm:gerenciar_funis')
    else:
        form = FunilForm()
    
    return render(request, 'crm/funil/criar.html', {'form': form})


@login_required
def funil_editar(request, funil_id):
    """Editar funil"""
    funil = get_object_or_404(Funil, id=funil_id, usuario=request.user)
    
    if request.method == 'POST':
        form = FunilForm(request.POST, instance=funil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Funil atualizado!')
            return redirect('crm:gerenciar_funis')
    else:
        form = FunilForm(instance=funil)
    
    return render(request, 'crm/funil/editar.html', {'form': form, 'funil': funil})


@login_required
def funil_excluir(request, funil_id):
    """Excluir funil"""
    funil = get_object_or_404(Funil, id=funil_id, usuario=request.user)
    nome = funil.nome
    funil.delete()
    messages.success(request, f'Funil "{nome}" excluído!')
    return redirect('crm:gerenciar_funis')


# ==================== METAS ====================
@login_required
def metas_list(request):
    """Lista de metas"""
    metas = Meta.objects.filter(usuario=request.user).order_by('-data_inicio')
    return render(request, 'crm/metas/list.html', {'metas': metas})


@login_required
def meta_criar(request):
    """Criar meta"""
    messages.info(request, 'Funcionalidade em desenvolvimento')
    return redirect('crm:metas_list')


@login_required
def meta_editar(request, meta_id):
    """Editar meta"""
    messages.info(request, 'Funcionalidade em desenvolvimento')
    return redirect('crm:metas_list')


# ==================== TAGS ====================
@login_required
def tags_list(request):
    """Lista de tags"""
    tags = Tag.objects.filter(usuario=request.user).order_by('nome')
    return render(request, 'crm/tags/list.html', {'tags': tags})


@login_required
def tag_criar(request):
    """Criar tag"""
    messages.info(request, 'Funcionalidade em desenvolvimento')
    return redirect('crm:tags_list')


# ==================== RELATÓRIOS ====================
@login_required
def relatorios(request):
    """Relatórios e análises"""
    periodo = request.GET.get('periodo', '30')
    data_inicio = timezone.now() - timedelta(days=int(periodo))
    
    # Métricas básicas
    context = {
        'periodo': periodo,
    }
    
    return render(request, 'crm/relatorios.html', context)


@login_required
def relatorio_vendas(request):
    """Relatório de vendas"""
    messages.info(request, 'Funcionalidade em desenvolvimento')
    return redirect('crm:relatorios')


@login_required
def relatorio_atividades(request):
    """Relatório de atividades"""
    messages.info(request, 'Funcionalidade em desenvolvimento')
    return redirect('crm:relatorios')


@login_required
def relatorio_funil(request):
    """Relatório de funil"""
    messages.info(request, 'Funcionalidade em desenvolvimento')
    return redirect('crm:relatorios')


@login_required
def relatorio_exportar(request):
    """Exportar relatórios"""
    messages.info(request, 'Funcionalidade em desenvolvimento')
    return redirect('crm:relatorios')


# ==================== CALENDÁRIO ====================
@login_required
def calendario(request):
    """Visualização de calendário"""
    mes = int(request.GET.get('mes', timezone.now().month))
    ano = int(request.GET.get('ano', timezone.now().year))
    
    context = {
        'mes': mes,
        'ano': ano,
    }
    
    return render(request, 'crm/calendario.html', context)


# ==================== BUSCA ====================
@login_required
def busca_global(request):
    """Busca global no CRM"""
    query = request.GET.get('q', '')
    
    if not query:
        return redirect('crm:dashboard')
    
    clientes = Cliente.objects.filter(
        usuario=request.user
    ).filter(
        Q(nome__icontains=query) |
        Q(email__icontains=query) |
        Q(telefone__icontains=query) |
        Q(empresa__icontains=query)
    )[:10]
    
    tarefas = Tarefa.objects.filter(
        usuario=request.user
    ).filter(
        Q(titulo__icontains=query) |
        Q(descricao__icontains=query)
    )[:10]
    
    context = {
        'query': query,
        'clientes': clientes,
        'tarefas': tarefas,
    }
    
    return render(request, 'crm/busca.html', context)


# ==================== ADMIN ====================
@login_required
def admin_crm(request):
    """Painel administrativo do CRM"""
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado. Apenas administradores.')
        return redirect('crm:dashboard')
    
    return render(request, 'crm/admin.html', {})


# ==================== API ENDPOINTS ====================
@login_required
def api_cliente_info(request, cliente_id):
    """API: Informações do cliente"""
    cliente = get_object_or_404(Cliente, id=cliente_id, usuario=request.user)
    data = {
        'id': cliente.id,
        'nome': cliente.nome,
        'email': cliente.email,
        'telefone': cliente.telefone,
        'empresa': cliente.empresa,
        'valor_estimado': float(cliente.valor_estimado),
    }
    return JsonResponse(data)


@login_required
def api_tarefas_stats(request):
    """API: Estatísticas de tarefas"""
    tarefas = Tarefa.objects.filter(usuario=request.user)
    data = {
        'pendentes': tarefas.filter(status='pendente').count(),
        'em_andamento': tarefas.filter(status='em_andamento').count(),
        'concluidas': tarefas.filter(status='concluida').count(),
    }
    return JsonResponse(data)


@login_required
def api_pipeline_stats(request):
    """API: Estatísticas do pipeline"""
    clientes = Cliente.objects.filter(usuario=request.user)
    data = {
        'total': clientes.count(),
        'valor_total': float(clientes.aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0),
    }
    return JsonResponse(data)