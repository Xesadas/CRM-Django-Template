"""
Funções auxiliares para o módulo CRM
"""

from datetime import timedelta
from django.utils import timezone
from decimal import Decimal, InvalidOperation


def calcular_horas_na_etapa(data_entrada):
    """
    Calcula quantas horas se passaram desde a entrada na etapa
    
    Args:
        data_entrada: DateTime da entrada na etapa
        
    Returns:
        float: Número de horas
    """
    if not data_entrada:
        return 0
    
    delta = timezone.now() - data_entrada
    return delta.total_seconds() / 3600


def formatar_brl(valor):
    """
    Formata um valor numérico para formato brasileiro (R$)
    
    Args:
        valor: Valor numérico
        
    Returns:
        str: Valor formatado (ex: "R$ 1.234,56")
    """
    try:
        valor_decimal = Decimal(str(valor))
        valor_str = f"{valor_decimal:,.2f}"
        # Trocar ponto por vírgula e vírgula por ponto
        valor_formatado = valor_str.replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"R$ {valor_formatado}"
    except (ValueError, TypeError, InvalidOperation):
        return "R$ 0,00"


def calcular_taxa_conversao(clientes_entrada, clientes_saida):
    """
    Calcula a taxa de conversão entre duas etapas
    
    Args:
        clientes_entrada: Número de clientes na etapa de entrada
        clientes_saida: Número de clientes que avançaram
        
    Returns:
        float: Taxa de conversão em porcentagem
    """
    if clientes_entrada == 0:
        return 0
    
    return (clientes_saida / clientes_entrada) * 100


def verificar_prazo_etapa(cliente, funil):
    """
    Verifica se um cliente está dentro do prazo da etapa
    
    Args:
        cliente: Instância de CRMCliente
        funil: Instância de Funil
        
    Returns:
        dict: {
            'dentro_prazo': bool,
            'horas_restantes': float (pode ser negativo se atrasado),
            'horas_na_etapa': float
        }
    """
    horas_na_etapa = calcular_horas_na_etapa(cliente.data_entrada_etapa)
    prazo_etapa = funil.prazos.get(cliente.etapa, 24)
    
    return {
        'dentro_prazo': horas_na_etapa <= prazo_etapa,
        'horas_restantes': prazo_etapa - horas_na_etapa,
        'horas_na_etapa': horas_na_etapa
    }


def gerar_estatisticas_funil(funil, usuario=None):
    """
    Gera estatísticas de um funil
    
    Args:
        funil: Instância de Funil
        usuario: User (opcional) - filtra por usuário
        
    Returns:
        dict: Estatísticas do funil
    """
    from .models import CRMCliente
    
    # Filtrar clientes
    clientes_query = CRMCliente.objects.filter(funil=funil)
    if usuario:
        clientes_query = clientes_query.filter(usuario=usuario)
    
    total_clientes = clientes_query.count()
    
    # Contar clientes por etapa
    clientes_por_etapa = {}
    for etapa in funil.etapas:
        count = clientes_query.filter(etapa=etapa).count()
        clientes_por_etapa[etapa] = count
    
    # Calcular clientes atrasados
    clientes_atrasados = 0
    for cliente in clientes_query:
        status = verificar_prazo_etapa(cliente, funil)
        if not status['dentro_prazo']:
            clientes_atrasados += 1
    
    return {
        'total_clientes': total_clientes,
        'clientes_por_etapa': clientes_por_etapa,
        'clientes_atrasados': clientes_atrasados,
        'taxa_atraso': (clientes_atrasados / total_clientes * 100) if total_clientes > 0 else 0
    }


def validar_cpf(cpf):
    """
    Valida um CPF brasileiro
    
    Args:
        cpf: String com CPF
        
    Returns:
        bool: True se válido
    """
    # Remove caracteres não numéricos
    cpf = ''.join(filter(str.isdigit, cpf))
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Validação dos dígitos verificadores
    for i in range(9, 11):
        soma = sum(int(cpf[num]) * ((i + 1) - num) for num in range(0, i))
        digito = ((soma * 10) % 11) % 10
        if int(cpf[i]) != digito:
            return False
    
    return True


def validar_cnpj(cnpj):
    """
    Valida um CNPJ brasileiro
    
    Args:
        cnpj: String com CNPJ
        
    Returns:
        bool: True se válido
    """
    # Remove caracteres não numéricos
    cnpj = ''.join(filter(str.isdigit, cnpj))
    
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cnpj == cnpj[0] * 14:
        return False
    
    # Validação dos dígitos verificadores
    def calcular_digito(cnpj, posicoes):
        soma = sum(int(cnpj[i]) * posicoes[i] for i in range(len(posicoes)))
        digito = 11 - (soma % 11)
        return 0 if digito > 9 else digito
    
    posicoes_primeiro = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    posicoes_segundo = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    primeiro_digito = calcular_digito(cnpj, posicoes_primeiro)
    segundo_digito = calcular_digito(cnpj, posicoes_segundo)
    
    return int(cnpj[12]) == primeiro_digito and int(cnpj[13]) == segundo_digito


def formatar_telefone(telefone):
    """
    Formata um telefone brasileiro
    
    Args:
        telefone: String com telefone
        
    Returns:
        str: Telefone formatado
    """
    # Remove caracteres não numéricos
    telefone = ''.join(filter(str.isdigit, telefone))
    
    if len(telefone) == 11:
        # Celular: (00) 00000-0000
        return f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"
    elif len(telefone) == 10:
        # Fixo: (00) 0000-0000
        return f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"
    else:
        return telefone


def gerar_relatorio_usuario(usuario):
    """
    Gera relatório completo de um usuário
    
    Args:
        usuario: User
        
    Returns:
        dict: Relatório com métricas
    """
    from .models import CRMCliente, ClienteAtivo, ClientePerdido
    
    clientes_crm = CRMCliente.objects.filter(usuario=usuario)
    clientes_ativos = ClienteAtivo.objects.filter(usuario=usuario)
    clientes_perdidos = ClientePerdido.objects.filter(usuario=usuario)
    
    total_atendidos = clientes_crm.count() + clientes_ativos.count() + clientes_perdidos.count()
    
    return {
        'usuario': usuario,
        'clientes_em_funil': clientes_crm.count(),
        'clientes_ativos': clientes_ativos.count(),
        'clientes_perdidos': clientes_perdidos.count(),
        'total_atendidos': total_atendidos,
        'taxa_conversao': (clientes_ativos.count() / total_atendidos * 100) if total_atendidos > 0 else 0,
        'taxa_perda': (clientes_perdidos.count() / total_atendidos * 100) if total_atendidos > 0 else 0
    }


def exportar_funil_csv(funil, usuario=None):
    """
    Exporta dados do funil para CSV
    
    Args:
        funil: Instância de Funil
        usuario: User (opcional) - filtra por usuário
        
    Returns:
        str: Conteúdo CSV
    """
    import csv
    from io import StringIO
    from .models import CRMCliente
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Cabeçalho
    writer.writerow([
        'Nome', 'Telefone', 'Empresa', 'Ramo', 
        'TPV Médio', 'Etapa', 'Horas na Etapa', 
        'Data Entrada', 'Observações'
    ])
    
    # Filtrar clientes
    clientes_query = CRMCliente.objects.filter(funil=funil)
    if usuario:
        clientes_query = clientes_query.filter(usuario=usuario)
    
    # Adicionar linhas
    for cliente in clientes_query:
        horas = calcular_horas_na_etapa(cliente.data_entrada_etapa)
        writer.writerow([
            cliente.nome,
            cliente.telefone or '',
            cliente.empresa or '',
            cliente.ramo_atividade or '',
            f"{cliente.tpv_medio:.2f}",
            cliente.etapa,
            f"{horas:.1f}",
            cliente.data_entrada_etapa.strftime('%d/%m/%Y %H:%M'),
            cliente.obs_livre or ''
        ])
    
    return output.getvalue()


def calcular_tempo_medio_funil(funil, usuario=None):
    """
    Calcula o tempo médio que clientes levam em cada etapa
    
    Args:
        funil: Instância de Funil
        usuario: User (opcional)
        
    Returns:
        dict: Tempo médio por etapa em horas
    """
    from .models import CRMCliente
    from django.db.models import Avg
    
    clientes_query = CRMCliente.objects.filter(funil=funil)
    if usuario:
        clientes_query = clientes_query.filter(usuario=usuario)
    
    tempos_por_etapa = {}
    
    for etapa in funil.etapas:
        clientes_etapa = clientes_query.filter(etapa=etapa)
        if clientes_etapa.exists():
            tempo_total = sum(
                calcular_horas_na_etapa(c.data_entrada_etapa) 
                for c in clientes_etapa
            )
            tempos_por_etapa[etapa] = tempo_total / clientes_etapa.count()
        else:
            tempos_por_etapa[etapa] = 0
    
    return tempos_por_etapa


def notificar_prazo_vencido(cliente):
    """
    Envia notificação quando prazo é vencido (placeholder para futuras implementações)
    
    Args:
        cliente: Instância de CRMCliente
    """
    # TODO: Implementar envio de email ou notificação push
    print(f"ALERTA: Cliente {cliente.nome} está com prazo vencido na etapa {cliente.etapa}")


def buscar_clientes_atrasados(usuario=None):
    """
    Busca todos os clientes que estão com prazo vencido
    
    Args:
        usuario: User (opcional) - filtra por usuário
        
    Returns:
        list: Lista de clientes atrasados com informações
    """
    from .models import CRMCliente
    
    clientes_query = CRMCliente.objects.all()
    if usuario:
        clientes_query = clientes_query.filter(usuario=usuario)
    
    clientes_atrasados = []
    
    for cliente in clientes_query:
        status = verificar_prazo_etapa(cliente, cliente.funil)
        if not status['dentro_prazo']:
            clientes_atrasados.append({
                'cliente': cliente,
                'horas_atraso': abs(status['horas_restantes']),
                'horas_na_etapa': status['horas_na_etapa']
            })
    
    return clientes_atrasados


def sugerir_proxima_acao(cliente):
    """
    Sugere próxima ação com base no status do cliente
    
    Args:
        cliente: Instância de CRMCliente
        
    Returns:
        dict: Sugestão de ação
    """
    funil = cliente.funil
    status = verificar_prazo_etapa(cliente, funil)
    
    # Cliente está na última etapa
    if cliente.etapa == funil.etapas[-1]:
        return {
            'prioridade': 'ALTA',
            'acao': 'Registrar como cliente ativo',
            'descricao': 'Cliente chegou na última etapa do funil'
        }
    
    # Cliente está atrasado
    if not status['dentro_prazo']:
        horas_atraso = abs(status['horas_restantes'])
        if horas_atraso > 72:  # Mais de 3 dias
            return {
                'prioridade': 'CRÍTICA',
                'acao': 'Contato urgente ou marcar como perdido',
                'descricao': f'Cliente atrasado há {horas_atraso:.0f} horas'
            }
        else:
            return {
                'prioridade': 'ALTA',
                'acao': 'Entrar em contato',
                'descricao': f'Cliente atrasado há {horas_atraso:.0f} horas'
            }
    
    # Cliente está dentro do prazo
    horas_restantes = status['horas_restantes']
    if horas_restantes < 12:  # Menos de 12h para vencer
        return {
            'prioridade': 'MÉDIA',
            'acao': 'Acompanhar progresso',
            'descricao': f'Prazo vence em {horas_restantes:.0f} horas'
        }
    
    return {
        'prioridade': 'BAIXA',
        'acao': 'Acompanhamento normal',
        'descricao': f'{horas_restantes:.0f} horas restantes no prazo'
    }


def gerar_score_cliente(cliente):
    """
    Gera um score para priorização do cliente
    
    Args:
        cliente: Instância de CRMCliente
        
    Returns:
        int: Score de 0 a 100
    """
    score = 50  # Base
    
    # Valor do TPV
    if cliente.tpv_medio > 50000:
        score += 20
    elif cliente.tpv_medio > 20000:
        score += 10
    
    # Status do prazo
    status = verificar_prazo_etapa(cliente, cliente.funil)
    if not status['dentro_prazo']:
        horas_atraso = abs(status['horas_restantes'])
        if horas_atraso > 72:
            score += 30
        else:
            score += 15
    
    # Posição no funil (mais avançado = maior score)
    try:
        posicao = cliente.funil.etapas.index(cliente.etapa)
        total_etapas = len(cliente.funil.etapas)
        score += int((posicao / total_etapas) * 20)
    except (ValueError, ZeroDivisionError):
        pass
    
    return min(score, 100)  # Máximo 100


def limpar_dados_telefone(telefone):
    """
    Remove formatação de telefone
    
    Args:
        telefone: String com telefone formatado
        
    Returns:
        str: Apenas números
    """
    return ''.join(filter(str.isdigit, telefone)) if telefone else ''


def limpar_dados_cpf_cnpj(documento):
    """
    Remove formatação de CPF/CNPJ
    
    Args:
        documento: String com documento formatado
        
    Returns:
        str: Apenas números
    """
    return ''.join(filter(str.isdigit, documento)) if documento else ''