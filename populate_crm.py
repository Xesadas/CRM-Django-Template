"""
Script para popular o banco de dados do CRM com dados fictícios.
Uso: python manage.py shell < populate_crm.py
Ou: exec(open('populate_crm.py').read())
"""

import os
import sys
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Configura o ambiente Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backends.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from apps.crm.models import *

# Listas de dados fictícios
NOMES = [
    'João Silva', 'Maria Santos', 'Pedro Oliveira', 'Ana Costa', 'Carlos Souza',
    'Juliana Pereira', 'Fernando Lima', 'Patrícia Rocha', 'Ricardo Alves', 'Camila Martins',
    'Lucas Ribeiro', 'Amanda Carvalho', 'Rafael Ferreira', 'Isabela Gomes', 'Marcos Santos',
    'Tatiane Mendes', 'Eduardo Costa', 'Cristina Oliveira', 'Roberto Silva', 'Vanessa Lima'
]

EMPRESAS = [
    'Tech Solutions Ltda', 'Inova Digital SA', 'Global Comércio', 'SoftTech Systems',
    'AgroBrasil', 'ConstruFort', 'HealthCare Medical', 'EduMax Educação',
    'Logística Express', 'Alimentos Naturais', 'AutoPeças Center', 'Imobiliária Horizonte',
    'Moda Fashion', 'Consultoria Avançada', 'Energia Sustentável'
]

SETORES = [
    'Tecnologia', 'Saúde', 'Educação', 'Construção Civil', 'Varejo',
    'Indústria', 'Serviços', 'Agronegócio', 'Financeiro', 'Imobiliário'
]

PRODUTOS = [
    {'nome': 'Sistema ERP Empresarial', 'descricao': 'Sistema completo de gestão empresarial', 'preco': '15000.00', 'custo': '5000.00'},
    {'nome': 'Consultoria em Marketing Digital', 'descricao': 'Planejamento e execução de campanhas digitais', 'preco': '8000.00', 'custo': '2000.00'},
    {'nome': 'Site Institucional', 'descricao': 'Desenvolvimento de website responsivo', 'preco': '5000.00', 'custo': '1500.00'},
    {'nome': 'Treinamento em Vendas', 'descricao': 'Curso presencial de técnicas de vendas', 'preco': '3000.00', 'custo': '800.00'},
    {'nome': 'Suporte Técnico Mensal', 'descricao': 'Pacote de suporte técnico 24/7', 'preco': '1200.00', 'custo': '400.00'},
    {'nome': 'Software Contábil', 'descricao': 'Sistema para gestão contábil', 'preco': '9000.00', 'custo': '3000.00'},
    {'nome': 'App Mobile Corporativo', 'descricao': 'Desenvolvimento de aplicativo mobile', 'preco': '25000.00', 'custo': '8000.00'},
]

# Etapas padrão dos funis
ETAPAS_PADRAO = [
    ['Contato Inicial', 'Qualificação', 'Apresentação', 'Proposta', 'Negociação', 'Fechamento'],
    ['Lead', 'MQL', 'SQL', 'Proposta', 'Negociação', 'Fechado'],
    ['Novo', 'Em Contato', 'Reunião Agendada', 'Proposta Enviada', 'Aguardando Resposta', 'Concluído']
]

def criar_usuario_teste():
    """Cria usuário de teste se não existir"""
    try:
        user = User.objects.get(username='teste')
        print("Usuário 'teste' já existe.")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='teste',
            password='teste123',
            email='teste@empresa.com',
            first_name='Usuário',
            last_name='Teste'
        )
        print(f"Usuário 'teste' criado com sucesso.")
    
    # Criar segundo usuário para testes
    try:
        user2 = User.objects.get(username='vendedor')
        print("Usuário 'vendedor' já existe.")
    except User.DoesNotExist:
        user2 = User.objects.create_user(
            username='vendedor',
            password='vendedor123',
            email='vendedor@empresa.com',
            first_name='Carlos',
            last_name='Vendedor'
        )
        print(f"Usuário 'vendedor' criado com sucesso.")
    
    return user, user2

def criar_funis(user):
    """Cria funis de vendas"""
    cores = ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8']
    nomes_funis = ['Funil de Vendas Padrão', 'Funil Enterprise', 'Funil B2B']
    
    funis = []
    for i, nome in enumerate(nomes_funis):
        funil, created = Funil.objects.get_or_create(
            nome=nome,
            usuario=user,
            defaults={
                'etapas': ETAPAS_PADRAO[i % len(ETAPAS_PADRAO)],
                'prazos': {etapa: random.randint(24, 168) for etapa in ETAPAS_PADRAO[i % len(ETAPAS_PADRAO)]},
                'taxas_conversao': {etapa: random.randint(30, 80) for etapa in ETAPAS_PADRAO[i % len(ETAPAS_PADRAO)][:-1]},
                'cor': cores[i % len(cores)],
                'ativo': True
            }
        )
        
        if created:
            print(f"Funil '{nome}' criado.")
        else:
            print(f"Funil '{nome}' já existe.")
        
        funis.append(funil)
    
    return funis

def criar_tags(user):
    """Cria tags para organização"""
    tags_data = [
        {'nome': 'VIP', 'cor': '#dc3545'},
        {'nome': 'Potencial Alto', 'cor': '#28a745'},
        {'nome': 'Reagendar', 'cor': '#ffc107'},
        {'nome': 'Frio', 'cor': '#6c757d'},
        {'nome': 'Quente', 'cor': '#dc3545'},
        {'nome': 'Retornar', 'cor': '#17a2b8'},
        {'nome': 'Proposta Enviada', 'cor': '#007bff'},
    ]
    
    tags = []
    for tag_data in tags_data:
        tag, created = Tag.objects.get_or_create(
            nome=tag_data['nome'],
            usuario=user,
            defaults={'cor': tag_data['cor']}
        )
        
        if created:
            print(f"Tag '{tag_data['nome']}' criada.")
        else:
            print(f"Tag '{tag_data['nome']}' já existe.")
        
        tags.append(tag)
    
    return tags

def criar_clientes(user, funis, tags):
    """Cria clientes fictícios"""
    clientes = []
    
    for i in range(20):  # Criar 20 clientes
        funil = random.choice(funis)
        etapa = random.choice(funil.etapas)
        
        # Data de entrada aleatória (últimos 30 dias)
        data_entrada = timezone.now() - timedelta(days=random.randint(0, 30))
        
        cliente = Cliente.objects.create(
            nome=random.choice(NOMES),
            tipo_pessoa=random.choice(['PF', 'PJ']),
            cpf_cnpj=f"{random.randint(10000000000, 99999999999)}" if random.choice([True, False]) else f"{random.randint(10000000000000, 99999999999999)}",
            telefone=f"({random.randint(11, 99)}) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
            email=f"cliente{i}@empresa.com",
            empresa=random.choice(EMPRESAS),
            setor=random.choice(SETORES),
            valor_estimado=Decimal(random.randint(5000, 100000)),
            origem=random.choice(['indicacao', 'site', 'redes_sociais', 'email', 'evento']),
            funil=funil,
            etapa=etapa,
            data_entrada_etapa=data_entrada,
            probabilidade=random.randint(10, 90),
            usuario=user
        )
        
        # Adicionar tags aleatórias
        num_tags = random.randint(1, 3)
        tags_cliente = random.sample(tags, num_tags)
        cliente.tags.set(tags_cliente)
        
        clientes.append(cliente)
        print(f"Cliente '{cliente.nome}' criado na etapa '{etapa}'.")
    
    return clientes

def criar_produtos(user):
    """Cria produtos/serviços"""
    produtos_criados = []
    
    for produto_data in PRODUTOS:
        codigo = f"PROD{random.randint(1000, 9999)}"
        produto, created = Produto.objects.get_or_create(
            nome=produto_data['nome'],
            usuario=user,
            defaults={
                'descricao': produto_data['descricao'],
                'codigo': codigo,
                'preco': Decimal(produto_data['preco']),
                'custo': Decimal(produto_data['custo']),
                'categoria': random.choice(['Software', 'Consultoria', 'Serviço', 'Treinamento']),
                'ativo': True
            }
        )
        
        if created:
            print(f"Produto '{produto.nome}' criado.")
        else:
            print(f"Produto '{produto.nome}' já existe.")
        
        produtos_criados.append(produto)
    
    return produtos_criados

def criar_tarefas(user, clientes, tags):
    """Cria tarefas fictícias"""
    tipos_tarefa = ['ligacao', 'email', 'reuniao', 'proposta', 'followup', 'negociacao', 'visita']
    status_tarefa = ['pendente', 'em_andamento', 'concluida']
    prioridades = ['baixa', 'media', 'alta', 'urgente']
    
    for i in range(30):  # Criar 30 tarefas
        cliente = random.choice(clientes) if random.choice([True, False]) else None
        
        # Data de vencimento aleatória (próximos 7 dias)
        data_vencimento = timezone.now() + timedelta(days=random.randint(1, 7))
        
        tarefa = Tarefa.objects.create(
            titulo=f"Tarefa {i+1}: {random.choice(['Contatar', 'Enviar proposta', 'Agendar reunião', 'Follow-up'])}",
            descricao=f"Descrição da tarefa {i+1}. Ações necessárias: {random.choice(['Ligar para cliente', 'Enviar email com proposta', 'Preparar apresentação'])}",
            tipo=random.choice(tipos_tarefa),
            status=random.choice(status_tarefa),
            prioridade=random.choice(prioridades),
            cliente=cliente,
            usuario=user,
            responsavel=user,
            data_vencimento=data_vencimento,
            tempo_estimado=random.randint(30, 180)
        )
        
        # Adicionar tags aleatórias
        num_tags = random.randint(1, 2)
        tags_tarefa = random.sample(tags, min(num_tags, len(tags)))
        tarefa.tags.set(tags_tarefa)
        
        print(f"Tarefa '{tarefa.titulo}' criada.")
    
    print("30 tarefas criadas.")

def criar_atividades(user, clientes):
    """Cria registros de atividades"""
    tipos_atividade = ['ligacao', 'email', 'reuniao', 'proposta', 'visita', 'nota', 'whatsapp']
    resultados = ['sucesso', 'sem_resposta', 'agendar_novo', 'negativo', 'outros']
    
    for cliente in clientes:
        # Criar 1-3 atividades por cliente
        num_atividades = random.randint(1, 3)
        
        for i in range(num_atividades):
            # Data aleatória nos últimos 15 dias
            data_atividade = timezone.now() - timedelta(days=random.randint(1, 15))
            
            atividade = Atividade.objects.create(
                tipo=random.choice(tipos_atividade),
                titulo=f"{random.choice(['Ligação', 'Reunião', 'Email'])} com {cliente.nome}",
                descricao=f"Descrição da atividade: {random.choice(['Cliente demonstrou interesse', 'Agendada próxima reunião', 'Enviada proposta comercial', 'Discutido projeto detalhado'])}",
                resultado=random.choice(resultados),
                cliente=cliente,
                usuario=user,
                duracao_minutos=random.randint(15, 120),
                data_atividade=data_atividade
            )
            
            # Atualizar último contato do cliente
            if not cliente.ultimo_contato or data_atividade > cliente.ultimo_contato:
                cliente.ultimo_contato = data_atividade
                cliente.save()
    
    print("Atividades criadas para todos os clientes.")

def criar_notas(user, clientes):
    """Cria notas para clientes"""
    for cliente in clientes:
        # Criar 0-2 notas por cliente
        num_notas = random.randint(0, 2)
        
        for i in range(num_notas):
            nota = Nota.objects.create(
                titulo=random.choice(['Observação importante', 'Informação adicional', 'Detalhe do contato']),
                conteudo=f"Nota sobre {cliente.nome}: {random.choice(['Cliente solicitou orçamento detalhado', 'Demonstrou preocupação com prazo', 'Solicitou demonstração do produto', 'Foi muito receptivo na reunião'])}",
                cliente=cliente,
                usuario=user,
                fixada=random.choice([True, False])
            )
    
    print("Notas criadas para clientes.")

def criar_metas(user):
    """Cria metas de vendas"""
    periodos = ['mensal', 'trimestral', 'anual']
    
    for i in range(3):
        data_inicio = timezone.now().replace(day=1).date()
        if i == 0:  # Mensal
            data_fim = data_inicio + timedelta(days=30)
            valor_alvo = Decimal(50000)
            # Calcular valor atual como até 80% do valor alvo
            valor_atual = Decimal(random.randint(10000, int(valor_alvo * Decimal('0.8'))))
        elif i == 1:  # Trimestral
            data_fim = data_inicio + timedelta(days=90)
            valor_alvo = Decimal(150000)
            valor_atual = Decimal(random.randint(30000, int(valor_alvo * Decimal('0.8'))))
        else:  # Anual
            data_fim = data_inicio + timedelta(days=365)
            valor_alvo = Decimal(600000)
            valor_atual = Decimal(random.randint(100000, int(valor_alvo * Decimal('0.8'))))
        
        meta = Meta.objects.create(
            nome=f"Meta de Vendas {['Mensal', 'Trimestral', 'Anual'][i]}",
            descricao=f"Meta de vendas para o período {['mensal', 'trimestral', 'anual'][i]}",
            periodo=periodos[i],
            valor_alvo=valor_alvo,
            valor_atual=valor_atual,
            usuario=user,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        print(f"Meta '{meta.nome}' criada.")

def criar_propostas(user, clientes, produtos):
    """Cria propostas comerciais"""
    status_proposta = ['rascunho', 'enviada', 'visualizada', 'aceita', 'rejeitada']
    
    for i in range(15):  # Criar 15 propostas
        cliente = random.choice(clientes)
        data_validade = timezone.now() + timedelta(days=random.randint(15, 60))
        
        proposta = Proposta.objects.create(
            numero=f"PROP{2024}{random.randint(1000, 9999)}",
            titulo=f"Proposta Comercial - {cliente.empresa}",
            descricao=f"Proposta comercial para {cliente.nome} da empresa {cliente.empresa}",
            status=random.choice(status_proposta),
            valor_total=Decimal(0),  # Será atualizado com os itens
            cliente=cliente,
            usuario=user,
            data_validade=data_validade.date()
        )
        
        # Adicionar itens à proposta
        valor_total = Decimal(0)
        num_itens = random.randint(1, 4)
        produtos_selecionados = random.sample(produtos, min(num_itens, len(produtos)))
        
        for produto in produtos_selecionados:
            quantidade = random.randint(1, 3)
            # Usar fator de variação em Decimal
            fator_variacao = Decimal(random.randint(90, 110)) / Decimal(100)
            preco_unitario = produto.preco * fator_variacao
            desconto = Decimal(random.randint(0, 1000))
            
            ItemProposta.objects.create(
                proposta=proposta,
                produto=produto,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
                desconto=desconto
            )
            
            subtotal = (quantidade * preco_unitario) - desconto
            valor_total += subtotal
        
        # Atualizar valor total da proposta
        proposta.valor_total = valor_total
        # Até 10% de desconto
        proposta.desconto = Decimal(random.randint(0, int(valor_total * Decimal('0.1'))))
        proposta.save()
        
        print(f"Proposta #{proposta.numero} criada para {cliente.nome}")

def limpar_dados_antigos(user):
    """Remove dados antigos do usuário (opcional)"""
    confirmacao = input(f"Deseja limpar todos os dados do usuário '{user.username}'? (s/n): ")
    
    if confirmacao.lower() == 's':
        Proposta.objects.filter(usuario=user).delete()
        Tarefa.objects.filter(usuario=user).delete()
        Atividade.objects.filter(usuario=user).delete()
        Nota.objects.filter(usuario=user).delete()
        Cliente.objects.filter(usuario=user).delete()
        Meta.objects.filter(usuario=user).delete()
        Produto.objects.filter(usuario=user).delete()
        Tag.objects.filter(usuario=user).delete()
        Funil.objects.filter(usuario=user).delete()
        print(f"Dados do usuário '{user.username}' removidos.")
    else:
        print("Manutenção dos dados existentes.")

def main():
    """Função principal"""
    print("=" * 60)
    print("POPULANDO CRM COM DADOS FICTÍCIOS")
    print("=" * 60)
    
    # 1. Criar/Carregar usuário
    user, user2 = criar_usuario_teste()
    
    # 2. Perguntar se deseja limpar dados antigos
    limpar_dados_antigos(user)
    
    # 3. Criar funis
    print("\nCriando funis de vendas...")
    funis = criar_funis(user)
    
    # 4. Criar tags
    print("\nCriando tags...")
    tags = criar_tags(user)
    
    # 5. Criar clientes
    print("\nCriando clientes...")
    clientes = criar_clientes(user, funis, tags)
    
    # 6. Criar produtos
    print("\nCriando produtos/serviços...")
    produtos = criar_produtos(user)
    
    # 7. Criar tarefas
    print("\nCriando tarefas...")
    criar_tarefas(user, clientes, tags)
    
    # 8. Criar atividades
    print("\nCriando atividades...")
    criar_atividades(user, clientes)
    
    # 9. Criar notas
    print("\nCriando notas...")
    criar_notas(user, clientes)
    
    # 10. Criar metas
    print("\nCriando metas...")
    criar_metas(user)
    
    # 11. Criar propostas
    print("\nCriando propostas...")
    criar_propostas(user, clientes, produtos)
    
    print("\n" + "=" * 60)
    print("POPULAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print("\nDados criados:")
    print(f"- {Funil.objects.filter(usuario=user).count()} funis")
    print(f"- {Tag.objects.filter(usuario=user).count()} tags")
    print(f"- {Cliente.objects.filter(usuario=user).count()} clientes")
    print(f"- {Produto.objects.filter(usuario=user).count()} produtos")
    print(f"- {Tarefa.objects.filter(usuario=user).count()} tarefas")
    print(f"- {Atividade.objects.filter(usuario=user).count()} atividades")
    print(f"- {Nota.objects.filter(usuario=user).count()} notas")
    print(f"- {Meta.objects.filter(usuario=user).count()} metas")
    print(f"- {Proposta.objects.filter(usuario=user).count()} propostas")
    print("\nCredenciais para login:")
    print("Usuário: teste | Senha: teste123")
    print("Usuário: vendedor | Senha: vendedor123")

if __name__ == "__main__":
    main()