// Arquivo JavaScript para o Calendário de Tarefas

// Variáveis globais
var selectedDate = null;
var isProcessing = false;
var tarefasDoMes = {};
var filtroAtual = 'todas';

// Garantir que as funções estejam disponíveis globalmente
window.selectedDate = null;
window.isProcessing = false;
window.tarefasDoMes = {};
window.filtroAtual = 'todas';

// ============================================================================
// CONTEXT MENU
// ============================================================================

window.showContextMenu = function(event, day, mes, ano) {
    event.preventDefault();
    window.selectedDate = { day, mes, ano };
    selectedDate = window.selectedDate;
    
    const contextMenu = document.getElementById('contextMenu');
    contextMenu.style.display = 'block';
    
    let x = event.clientX;
    let y = event.clientY;
    
    const menuRect = contextMenu.getBoundingClientRect();
    const menuWidth = menuRect.width || 220;
    const menuHeight = menuRect.height || 150;
    
    if (x + menuWidth > window.innerWidth) {
        x = window.innerWidth - menuWidth - 10;
    }
    
    if (y + menuHeight > window.innerHeight) {
        y = window.innerHeight - menuHeight - 10;
    }
    
    if (x < 0) x = 10;
    if (y < 0) y = 10;
    
    contextMenu.style.left = x + 'px';
    contextMenu.style.top = y + 'px';
    
    setTimeout(() => {
        document.addEventListener('click', hideContextMenu);
    }, 100);
}

window.hideContextMenu = function() {
    const contextMenu = document.getElementById('contextMenu');
    contextMenu.style.display = 'none';
    document.removeEventListener('click', hideContextMenu);
}

// ============================================================================
// CARREGAR TAREFAS DO MÊS
// ============================================================================

window.carregarTarefasDoMes = function() {
    const urlParams = new URLSearchParams(window.location.search);
    const mes = urlParams.get('mes') || new Date().getMonth() + 1;
    const ano = urlParams.get('ano') || new Date().getFullYear();
    
    fetch(`/calendario/tarefas-mes/?mes=${mes}&ano=${ano}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.tarefasDoMes = data.tarefas_por_dia;
                window.renderizarTarefas(filtroAtual);
            } else {
                console.error('Erro ao carregar tarefas:', data.error);
                showToast('error', 'Erro!', 'Erro ao carregar tarefas do mês');
            }
        })
        .catch(error => {
            console.error('Erro na requisição:', error);
            showToast('error', 'Erro!', 'Erro na comunicação com o servidor');
        });
}

// ============================================================================
// FILTRAR TAREFAS
// ============================================================================

window.aplicarFiltro = function(filtro) {
    window.filtroAtual = filtro;
    
    // Atualizar estado dos botões
    document.querySelectorAll('.filter-btn').forEach(btn => {
        if (btn.dataset.filter === filtro) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    window.renderizarTarefas(filtro);
}

window.filtrarTarefas = function(tarefas, filtro) {
    return tarefas.filter(tarefa => {
        switch(filtro) {
            case 'todas':
                return true;
            case 'pendentes':
                return tarefa.status === 'pendente';
            case 'concluidas':
                return tarefa.status === 'concluida';
            case 'atrasadas':
                return tarefa.esta_atrasada;
            case 'alta':
                return tarefa.prioridade === 'alta';
            default:
                return true;
        }
    });
}

// ============================================================================
// RENDERIZAR TAREFAS
// ============================================================================

window.renderizarTarefas = function(filtro) {
    const container = document.getElementById('tarefasLista');
    
    if (!window.tarefasDoMes || Object.keys(window.tarefasDoMes).length === 0) {
        container.innerHTML = `
            <div class="no-tasks">
                <i class="fas fa-tasks"></i>
                <h5>Nenhuma tarefa encontrada</h5>
                <p class="text-muted">Clique com o botão direito em um dia do calendário para adicionar uma tarefa</p>
            </div>
        `;
        return;
    }
    
    const urlParams = new URLSearchParams(window.location.search);
    const mes = parseInt(urlParams.get('mes') || new Date().getMonth() + 1);
    const ano = parseInt(urlParams.get('ano') || new Date().getFullYear());
    
    let html = '';
    let totalTarefas = 0;
    
    // Ordenar dias em ordem decrescente
    const dias = Object.keys(window.tarefasDoMes)
        .map(Number)
        .sort((a, b) => b - a);
    
    for (const dia of dias) {
        const tarefasDia = window.tarefasDoMes[dia];
        const tarefasFiltradas = window.filtrarTarefas(tarefasDia, filtro);
        
        if (tarefasFiltradas.length === 0) continue;
        
        totalTarefas += tarefasFiltradas.length;
        
        html += `
            <div class="day-section has-tasks">
                <div class="day-header">
                    <h5>
                        <i class="fas fa-calendar-day"></i>
                        ${dia.toString().padStart(2, '0')}/${mes.toString().padStart(2, '0')}/${ano}
                    </h5>
                    <span class="badge bg-secondary">${tarefasFiltradas.length} tarefa(s)</span>
                </div>
                <div class="day-tasks-list">
        `;
        
        for (const tarefa of tarefasFiltradas) {
            const statusClass = tarefa.status === 'concluida' ? 'concluida' : 
                              tarefa.esta_atrasada ? 'atrasada' : 'pendente';
            const statusIcon = tarefa.status === 'concluida' ? 'check-circle' : 
                             tarefa.esta_atrasada ? 'exclamation-triangle' : 'clock';
            const statusColor = tarefa.status === 'concluida' ? 'success' : 
                              tarefa.esta_atrasada ? 'danger' : 'warning';
            const priorityClass = `priority-${tarefa.prioridade}`;
            
            html += `
                <div class="task-card ${statusClass} ${priorityClass}" 
                     data-tarefa-id="${tarefa.id}"
                     onclick="abrirDetalhesTarefa(${tarefa.id})">
                    <div class="task-info">
                        <h6>${tarefa.titulo}</h6>
                        ${tarefa.descricao ? `<p class="task-desc">${tarefa.descricao}</p>` : ''}
                        <div class="task-meta">
                            <span class="badge bg-${statusColor}">
                                <i class="fas fa-${statusIcon}"></i> ${tarefa.status_display}
                            </span>
                            <span class="badge ${priorityClass}">
                                <i class="fas fa-flag"></i> ${tarefa.prioridade_display}
                            </span>
                            ${tarefa.categoria !== 'Sem Categoria' ? `
                                <span class="badge" style="background-color: ${tarefa.cor_categoria}; color: white;">
                                    ${tarefa.categoria}
                                </span>
                            ` : ''}
                        </div>
                    </div>
                    <div class="task-actions">
                        <button class="btn btn-sm ${tarefa.status === 'concluida' ? 'btn-warning' : 'btn-success'}"
                                data-tarefa-id="${tarefa.id}"
                                data-status="${tarefa.status}"
                                onclick="alternarStatusTarefaLista(event, ${tarefa.id})">
                            <i class="fas fa-${tarefa.status === 'concluida' ? 'undo' : 'check'}"></i>
                            ${tarefa.status === 'concluida' ? 'Reabrir' : 'Concluir'}
                        </button>
                    </div>
                </div>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
    }
    
    if (totalTarefas === 0) {
        html = `
            <div class="no-tasks">
                <i class="fas fa-filter"></i>
                <h5>Nenhuma tarefa encontrada com o filtro atual</h5>
                <p class="text-muted">Tente mudar o filtro para ver mais tarefas</p>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// ============================================================================
// ALTERNAR STATUS NA LISTA
// ============================================================================

function alternarStatusTarefaLista(event, tarefaId) {
    event.stopPropagation();
    
    if (isProcessing) return;
    isProcessing = true;
    
    const button = event.target.closest('button');
    const originalHTML = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
    fetch(`/calendario/tarefa/${tarefaId}/alternar-status/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('success', 'Sucesso!', data.message);
            
            // Recarregar tarefas
            setTimeout(() => {
                carregarTarefasDoMes();
            }, 300);
        } else {
            throw new Error(data.error || 'Erro ao alterar status');
        }
    })
    .catch(error => {
        showToast('error', 'Erro!', error.message);
        button.innerHTML = originalHTML;
        button.disabled = false;
    })
    .finally(() => {
        isProcessing = false;
    });
}

// ============================================================================
// ABRIR DETALHES DA TAREFA
// ============================================================================

window.abrirDetalhesTarefa = function(tarefaId) {
    fetch(`/calendario/editar-tarefa/${tarefaId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tarefa = data.tarefa;
                
                const modalHTML = `
                    <div class="modal fade" id="detalhesTarefaModal" tabindex="-1">
                        <div class="modal-dialog">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">Detalhes da Tarefa</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <div class="mb-3">
                                        <h6>${tarefa.titulo}</h6>
                                        ${tarefa.descricao ? `<p>${tarefa.descricao}</p>` : '<p class="text-muted">Sem descrição</p>'}
                                        
                                        <div class="row mt-3">
                                            <div class="col-md-6">
                                                <div class="mb-2">
                                                    <small class="text-muted">Data de Vencimento:</small>
                                                    <div><strong>${tarefa.data_vencimento}</strong></div>
                                                </div>
                                            </div>
                                            <div class="col-md-6">
                                                <div class="mb-2">
                                                    <small class="text-muted">Prioridade:</small>
                                                    <div><span class="badge priority-${tarefa.prioridade}">${tarefa.prioridade_display}</span></div>
                                                </div>
                                            </div>
                                            <div class="col-md-6">
                                                <div class="mb-2">
                                                    <small class="text-muted">Status:</small>
                                                    <div><span class="badge bg-${tarefa.status === 'concluida' ? 'success' : 'warning'}">${tarefa.status_display}</span></div>
                                                </div>
                                            </div>
                                            <div class="col-md-6">
                                                <div class="mb-2">
                                                    <small class="text-muted">Categoria:</small>
                                                    <div>${tarefa.categoria || 'Sem categoria'}</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                                    <button type="button" class="btn btn-dark" onclick="editarTarefa(${tarefa.id})">
                                        <i class="fas fa-edit"></i> Editar
                                    </button>
                                    <button type="button" class="btn btn-outline-danger" onclick="confirmarExclusaoTarefa(${tarefa.id})">
                                        <i class="fas fa-trash"></i> Excluir
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                const modalContainer = document.createElement('div');
                modalContainer.innerHTML = modalHTML;
                document.body.appendChild(modalContainer);
                
                const modal = new bootstrap.Modal(document.getElementById('detalhesTarefaModal'));
                modal.show();
                
                modalContainer.addEventListener('hidden.bs.modal', function () {
                    modalContainer.remove();
                });
            }
        })
        .catch(error => {
            console.error('Erro ao carregar detalhes:', error);
            showToast('error', 'Erro!', 'Erro ao carregar detalhes da tarefa');
        });
}

// ============================================================================
// FUNÇÃO PARA CONFIRMAR EXCLUSÃO DE TAREFA
// ============================================================================

window.confirmarExclusaoTarefa = function(tarefaId) {
    if (!confirm('Deseja realmente excluir esta tarefa?\n\nEsta ação não pode ser desfeita!')) {
        return;
    }
    
    fetch(`/calendario/tarefa/${tarefaId}/excluir/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('success', 'Sucesso!', data.message);
            
            const modal = bootstrap.Modal.getInstance(document.getElementById('detalhesTarefaModal'));
            if (modal) modal.hide();
            
            setTimeout(() => {
                window.carregarTarefasDoMes();
            }, 300);
        } else {
            showToast('error', 'Erro!', data.error || 'Erro ao excluir tarefa');
        }
    })
    .catch(error => {
        showToast('error', 'Erro!', 'Erro na comunicação com o servidor');
        console.error('Error:', error);
    });
}

// ============================================================================
// TAREFAS (Funções do modal principal)
// ============================================================================

window.showTaskModal = function() {
    if (window.selectedDate) {
        const { day, mes, ano } = window.selectedDate;
        const data = `${ano}-${mes.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
        document.getElementById('data_vencimento_modal').value = data;
        
        window.carregarCategorias();
        
        const modal = new bootstrap.Modal(document.getElementById('taskModal'));
        modal.show();
    }
    hideContextMenu();
}

window.viewDayDetails = function() {
    if (window.selectedDate) {
        const { day, mes, ano } = window.selectedDate;
        
        const modal = new bootstrap.Modal(document.getElementById('dayModal'));
        document.querySelector('#dayModal .modal-title').textContent = `Tarefas do Dia ${day}/${mes}/${ano}`;
        
        fetch(`/calendario/dia-detalhes/?dia=${day}&mes=${mes}&ano=${ano}`)
            .then(response => response.json())
            .then(data => {
                const dayDetails = document.getElementById('dayDetails');
                let html = '';

                if (data.tarefas && data.tarefas.length > 0) {
                    html += '<div class="list-group">';
                    data.tarefas.forEach(t => {
                        const statusClass = t.status === 'concluida' ? 'success' : 
                                          t.esta_atrasada ? 'danger' : 'warning';
                        const statusText = t.status_display;
                        const priorityClass = `priority-${t.prioridade}`;
                        
                        html += `<div class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h6 class="mb-1">${t.titulo}</h6>
                                    ${t.descricao ? `<small class="text-muted">${t.descricao}</small><br>` : ''}
                                    <small class="badge ${priorityClass} me-1">${t.prioridade_display}</small>
                                    <small class="text-muted">${t.categoria} - ${t.data_vencimento}</small>
                                </div>
                                <div class="text-end">
                                    <span class="badge bg-${statusClass} mb-2 status-badge-${t.id}">${statusText}</span>
                                    <br>
                                    <div class="btn-group btn-group-sm">
                                        <button class="btn btn-${t.status === 'concluida' ? 'warning' : 'success'} btn-toggle-tarefa" 
                                                data-tarefa-id="${t.id}"
                                                data-status="${t.status}">
                                            <i class="fas fa-${t.status === 'concluida' ? 'undo' : 'check'}"></i>
                                        </button>
                                        <button class="btn btn-dark btn-editar-tarefa" 
                                                onclick="editarTarefa(${t.id})">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>`;
                    });
                    html += '</div>';
                } else {
                    html = '<div class="alert alert-info">Nenhuma tarefa neste dia</div>';
                }

                dayDetails.innerHTML = html;
                
                // Adicionar event listeners aos botões
                document.querySelectorAll('.btn-toggle-tarefa').forEach(btn => {
                    btn.addEventListener('click', function() {
                        alternarStatusTarefa(this.dataset.tarefaId, this);
                    });
                });
            });
        
        modal.show();
    }
    hideContextMenu();
}

function alternarStatusTarefa(tarefaId, buttonElement) {
    if (isProcessing) {
        return;
    }
    
    isProcessing = true;
    
    buttonElement.disabled = true;
    buttonElement.classList.add('btn-loading');
    const originalHTML = buttonElement.innerHTML;
    buttonElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
    fetch(`/calendario/tarefa/${tarefaId}/alternar-status/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('success', 'Sucesso!', data.message);
            
            atualizarTarefaNaInterface(tarefaId, buttonElement);
            
            setTimeout(() => {
                carregarTarefasDoMes();
            }, 500);
        } else {
            throw new Error(data.error || 'Erro ao alterar status');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        showToast('error', 'Erro!', error.message || 'Erro na comunicação com o servidor');
        
        buttonElement.innerHTML = originalHTML;
        buttonElement.disabled = false;
        buttonElement.classList.remove('btn-loading');
    })
    .finally(() => {
        isProcessing = false;
    });
}

function atualizarTarefaNaInterface(tarefaId, buttonElement) {
    const wasCompleted = buttonElement.dataset.status === 'concluida';
    const nowCompleted = !wasCompleted;
    
    buttonElement.dataset.status = nowCompleted ? 'concluida' : 'pendente';
    
    const statusBadge = document.querySelector(`.status-badge-${tarefaId}`);
    if (statusBadge) {
        statusBadge.className = `badge bg-${nowCompleted ? 'success' : 'warning'} mb-2 status-badge-${tarefaId}`;
        statusBadge.textContent = nowCompleted ? 'Concluída' : 'Pendente';
    }
    
    const btnClass = nowCompleted ? 'btn-warning' : 'btn-success';
    const btnText = nowCompleted ? 'Reabrir' : 'Concluir';
    const iconClass = nowCompleted ? 'undo' : 'check';
    
    buttonElement.className = `btn btn-sm ${btnClass} btn-toggle-tarefa`;
    buttonElement.innerHTML = `<i class="fas fa-${iconClass}"></i>`;
    buttonElement.disabled = false;
    buttonElement.classList.remove('btn-loading');
}

// ============================================================================
// CATEGORIAS
// ============================================================================

window.carregarCategorias = function() {
    fetch('/calendario/categorias/')
        .then(response => response.json())
        .then(data => {
            const categoriasLista = document.getElementById('categoriasLista');
            const categoriaSelect = document.getElementById('categoriaSelect');
            
            categoriasLista.innerHTML = '';
            if (categoriaSelect) {
                // Limpar opções exceto a primeira
                while (categoriaSelect.options.length > 1) {
                    categoriaSelect.remove(1);
                }
            }
            
            if (data.categorias && data.categorias.length > 0) {
                data.categorias.forEach(categoria => {
                    // Adicionar à lista no modal
                    const item = document.createElement('button');
                    item.type = 'button';
                    item.className = 'list-group-item list-group-item-action';
                    item.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center">
                            <span>${categoria.nome}</span>
                            <span class="badge" style="background-color: ${categoria.cor}">&nbsp;&nbsp;</span>
                        </div>
                    `;
                    item.onclick = () => {
                        if (categoriaSelect) {
                            categoriaSelect.value = categoria.id;
                        }
                        bootstrap.Modal.getInstance(document.getElementById('categoriasModal')).hide();
                    };
                    categoriasLista.appendChild(item);
                    
                    // Adicionar ao select no modal de tarefa
                    if (categoriaSelect) {
                        const option = document.createElement('option');
                        option.value = categoria.id;
                        option.textContent = categoria.nome;
                        categoriaSelect.appendChild(option);
                    }
                });
            } else {
                categoriasLista.innerHTML = '<div class="text-muted text-center p-2">Nenhuma categoria cadastrada</div>';
            }
        })
        .catch(error => {
            console.error('Erro ao carregar categorias:', error);
            showToast('error', 'Erro!', 'Erro ao carregar categorias');
        });
}

window.showCategoriasModal = function() {
    window.carregarCategorias();
    const modal = new bootstrap.Modal(document.getElementById('categoriasModal'));
    modal.show();
}

window.showNovaCategoriaModal = function() {
    const modal = new bootstrap.Modal(document.getElementById('novaCategoriaModal'));
    modal.show();
}

// ============================================================================
// FORMULÁRIOS
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Carregar tarefas do mês ao iniciar
    window.carregarTarefasDoMes();
    
    // Formulário de Nova Tarefa
    const formTarefa = document.getElementById('novaTarefaForm');
    if (formTarefa) {
        formTarefa.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitBtn = this.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.classList.add('btn-loading');
            
            const formData = new FormData(this);
            
            fetch('/calendario/tarefa/criar/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    bootstrap.Modal.getInstance(document.getElementById('taskModal')).hide();
                    showToast('success', 'Sucesso!', data.message);
                    formTarefa.reset();
                    setTimeout(() => {
                        carregarTarefasDoMes();
                    }, 300);
                } else {
                    showToast('error', 'Erro!', data.error || 'Erro ao criar tarefa');
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('btn-loading');
                }
            })
            .catch(error => {
                showToast('error', 'Erro!', 'Erro na comunicação com o servidor');
                console.error('Error:', error);
                submitBtn.disabled = false;
                submitBtn.classList.remove('btn-loading');
            });
        });
    }

    // Formulário de Nova Categoria
    const formCategoria = document.getElementById('novaCategoriaForm');
    if (formCategoria) {
        formCategoria.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            fetch('/calendario/criar-categoria/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    bootstrap.Modal.getInstance(document.getElementById('novaCategoriaModal')).hide();
                    showToast('success', 'Sucesso!', 'Categoria criada com sucesso!');
                    window.carregarCategorias();
                } else {
                    showToast('error', 'Erro!', data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('error', 'Erro!', 'Erro na comunicação com o servidor');
            });
        });
    }
});

// ============================================================================
// EDITAR TAREFA
// ============================================================================

window.editarTarefa = function(tarefaId) {
    fetch(`/calendario/editar-tarefa/${tarefaId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tarefa = data.tarefa;
                
                const modalHTML = `
                    <div class="modal fade" id="editarTarefaModal" tabindex="-1">
                        <div class="modal-dialog modal-lg">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">Editar Tarefa</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                <form id="editarTarefaForm" data-tarefa-id="${tarefaId}">
                                    <div class="modal-body">
                                        <div class="row">
                                            <div class="col-md-8">
                                                <div class="mb-3">
                                                    <label class="form-label">Título *</label>
                                                    <input type="text" class="form-control" name="titulo" 
                                                           value="${tarefa.titulo}" required>
                                                </div>
                                            </div>
                                            <div class="col-md-4">
                                                <div class="mb-3">
                                                    <label class="form-label">Prioridade *</label>
                                                    <select class="form-select" name="prioridade" required>
                                                        <option value="baixa" ${tarefa.prioridade === 'baixa' ? 'selected' : ''}>Baixa</option>
                                                        <option value="media" ${tarefa.prioridade === 'media' ? 'selected' : ''}>Média</option>
                                                        <option value="alta" ${tarefa.prioridade === 'alta' ? 'selected' : ''}>Alta</option>
                                                    </select>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label class="form-label">Descrição</label>
                                            <textarea class="form-control" name="descricao" rows="3">${tarefa.descricao || ''}</textarea>
                                        </div>
                                        
                                        <div class="row">
                                            <div class="col-md-6">
                                                <div class="mb-3">
                                                    <label class="form-label">Data de Vencimento *</label>
                                                    <input type="date" class="form-control" name="data_vencimento" 
                                                           value="${tarefa.data_vencimento}" required>
                                                </div>
                                            </div>
                                            <div class="col-md-6">
                                                <div class="mb-3">
                                                    <label class="form-label">Status</label>
                                                    <select class="form-select" name="status">
                                                        <option value="pendente" ${tarefa.status === 'pendente' ? 'selected' : ''}>Pendente</option>
                                                        <option value="em_andamento" ${tarefa.status === 'em_andamento' ? 'selected' : ''}>Em Andamento</option>
                                                        <option value="concluida" ${tarefa.status === 'concluida' ? 'selected' : ''}>Concluída</option>
                                                        <option value="cancelada" ${tarefa.status === 'cancelada' ? 'selected' : ''}>Cancelada</option>
                                                    </select>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label class="form-label">Categoria</label>
                                            <select class="form-select" name="categoria_id" id="categoriaEditar">
                                                <option value="">Sem Categoria</option>
                                                <!-- Categorias serão carregadas via AJAX -->
                                            </select>
                                        </div>
                                    </div>
                                    <div class="modal-footer">
                                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                                        <button type="submit" class="btn btn-dark">
                                            <i class="fas fa-save"></i> Salvar Alterações
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                `;
                
                const modalContainer = document.createElement('div');
                modalContainer.innerHTML = modalHTML;
                document.body.appendChild(modalContainer);
                
                const modal = new bootstrap.Modal(document.getElementById('editarTarefaModal'));
                modal.show();
                
                // Carregar categorias para o select
                fetch('/calendario/categorias/')
                    .then(response => response.json())
                    .then(data => {
                        if (data.categorias) {
                            const select = document.getElementById('categoriaEditar');
                            data.categorias.forEach(categoria => {
                                const option = document.createElement('option');
                                option.value = categoria.id;
                                option.textContent = categoria.nome;
                                if (categoria.id === tarefa.categoria_id) {
                                    option.selected = true;
                                }
                                select.appendChild(option);
                            });
                        }
                    });
                
                const detalhesModal = document.getElementById('detalhesTarefaModal');
                if (detalhesModal) {
                    const bsDetalhesModal = bootstrap.Modal.getInstance(detalhesModal);
                    if (bsDetalhesModal) bsDetalhesModal.hide();
                }
                
                // Form submit handler
                const form = document.getElementById('editarTarefaForm');
                form.addEventListener('submit', function(e) {
                    e.preventDefault();
                    
                    const submitBtn = this.querySelector('button[type="submit"]');
                    const originalHTML = submitBtn.innerHTML;
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
                    
                    const formData = new FormData(this);
                    
                    fetch(`/calendario/editar-tarefa/${tarefaId}/`, {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken'),
                            'X-Requested-With': 'XMLHttpRequest',
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showToast('success', 'Sucesso!', data.message);
                            modal.hide();
                            
                            setTimeout(() => {
                                window.carregarTarefasDoMes();
                            }, 300);
                        } else {
                            showToast('error', 'Erro!', data.error || 'Erro ao salvar alterações');
                            submitBtn.disabled = false;
                            submitBtn.innerHTML = originalHTML;
                        }
                    })
                    .catch(error => {
                        showToast('error', 'Erro!', 'Erro na comunicação com o servidor');
                        console.error('Error:', error);
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalHTML;
                    });
                });
                
                modalContainer.addEventListener('hidden.bs.modal', function() {
                    modalContainer.remove();
                });
            }
        })
        .catch(error => {
            console.error('Erro ao carregar dados da tarefa:', error);
            showToast('error', 'Erro!', 'Erro ao carregar dados para edição');
        });
}

// ============================================================================
// UTILITÁRIOS
// ============================================================================

function showToast(type, title, message) {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${title}</strong><br>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    container.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function () {
        this.remove();
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}