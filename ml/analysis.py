import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Configuração do banco de dados
db_config = {
    'host': 'localhost',
    'database': 'erp_iot_ml',
    'user': 'root',
    'password': 'gerar usuário e senha no php my admin e inserir a senha aqui entre aspas as apas simples'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def analyze_sales_data():
    """Análise de dados de vendas para o dashboard - ATUALIZADO"""
    conn = get_db_connection()
    if not conn:
        return {
            'top_products': [], 
            'days_analysis': [], 
            'predictions': [], 
            'movement_analysis': [],
            'dia_atual': {},
            'temporal_analysis': {},
            'historical_trends': {}
        }
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Produtos mais vendidos
        query = """
        SELECT 
            p.nome,
            p.preco_venda,
            COALESCE(SUM(iv.quantidade), 0) as total_vendido,
            COALESCE(SUM(iv.total_item), 0) as total_receita
        FROM produtos p
        LEFT JOIN itens_venda iv ON p.id = iv.id_produto
        LEFT JOIN vendas v ON iv.id_venda = v.id
        WHERE p.ativo = TRUE AND v.status = 'concluida'
        GROUP BY p.id, p.nome, p.preco_venda
        ORDER BY total_vendido DESC
        LIMIT 5
        """
        
        cursor.execute(query)
        top_products = cursor.fetchall()
        
        # Converter Decimal para float
        for product in top_products:
            for key, value in product.items():
                if isinstance(value, Decimal):
                    product[key] = float(value)
        
        # DADOS DO DIA ATUAL PARA MOVIMENTO POR DIA - ATUALIZADO
        query_dia_atual = """
        SELECT 
            DATE(v.data_venda) as data_venda,
            DAYNAME(v.data_venda) as dia_semana,
            DAYOFWEEK(v.data_venda) as dia_numero,
            COUNT(*) as total_vendas,
            COALESCE(SUM(v.valor_total), 0) as total_dia,
            AVG(v.valor_total) as media_venda,
            COUNT(DISTINCT v.id_cliente) as clientes_unicos
        FROM vendas v
        WHERE DATE(v.data_venda) = CURDATE() AND v.status = 'concluida'
        GROUP BY DATE(v.data_venda), DAYNAME(v.data_venda), DAYOFWEEK(v.data_venda)
        ORDER BY dia_numero
        """
        
        cursor.execute(query_dia_atual)
        dia_atual_data = cursor.fetchall()
        
        # DADOS HISTÓRICOS PARA ANÁLISE GERAL (últimos 6 meses) - AUMENTADO PARA MELHOR PREVISÃO
        query_historico = """
        SELECT 
            DATE(v.data_venda) as data_venda,
            DAYNAME(v.data_venda) as dia_semana,
            DAYOFWEEK(v.data_venda) as dia_numero,
            COUNT(*) as total_vendas,
            COALESCE(SUM(v.valor_total), 0) as total_dia,
            AVG(v.valor_total) as media_venda,
            COUNT(DISTINCT v.id_cliente) as clientes_unicos
        FROM vendas v
        WHERE v.data_venda >= DATE_SUB(NOW(), INTERVAL 6 MONTH) AND v.status = 'concluida'
        GROUP BY DATE(v.data_venda), DAYNAME(v.data_venda), DAYOFWEEK(v.data_venda)
        ORDER BY data_venda DESC
        """
        
        cursor.execute(query_historico)
        historico_data = cursor.fetchall()
        
        # ANÁLISE DE MOVIMENTO APENAS COM DADOS DO DIA ATUAL
        movement_analysis = analyze_sales_movement(dia_atual_data)
        
        # ANÁLISE TRADICIONAL POR DIA DA SEMANA (com dados históricos)
        days_analysis = process_days_analysis(historico_data)
        
        # ANÁLISE DO DIA ATUAL
        dia_atual_analysis = analyze_current_day(dia_atual_data)
        
        # Converter Decimal para float
        for day in days_analysis:
            for key, value in day.items():
                if isinstance(value, Decimal):
                    day[key] = float(value)
        
        # PREVISÕES MELHORADAS (usando dados históricos)
        predictions = generate_advanced_predictions(historico_data, movement_analysis)
        
        # ANÁLISE TEMPORAL
        temporal_analysis = generate_temporal_analysis(historico_data, movement_analysis)
        
        # ANÁLISE DE TENDÊNCIAS HISTÓRICAS
        historical_trends = analyze_historical_trends(historico_data)
        
        return {
            'top_products': top_products,
            'days_analysis': days_analysis,
            'predictions': predictions,
            'movement_analysis': movement_analysis,
            'dia_atual': dia_atual_analysis,
            'temporal_analysis': temporal_analysis,
            'historical_trends': historical_trends
        }
        
    except Error as e:
        print(f"Erro ao analisar dados de vendas: {e}")
        return {
            'top_products': [], 
            'days_analysis': [], 
            'predictions': [], 
            'movement_analysis': [],
            'dia_atual': {},
            'temporal_analysis': {},
            'historical_trends': {}
        }
    finally:
        if conn and conn.is_connected():
            conn.close()

def analyze_current_day(dia_atual_data):
    """Analisa dados do dia atual - ATUALIZADO"""
    if not dia_atual_data:
        return {
            'vendas_hoje': 0,
            'receita_hoje': 0.0,
            'clientes_hoje': 0,
            'ticket_medio_hoje': 0.0,
            'ultima_atualizacao': datetime.now().strftime('%H:%M:%S'),
            'status': 'sem_vendas'
        }
    
    try:
        # Somar todos os registros do dia atual
        total_vendas = sum(int(dia['total_vendas']) for dia in dia_atual_data)
        total_receita = sum(float(dia['total_dia'] or 0) for dia in dia_atual_data)
        total_clientes = sum(int(dia['clientes_unicos']) for dia in dia_atual_data)
        
        # Calcular ticket médio
        ticket_medio = total_receita / total_vendas if total_vendas > 0 else 0
        
        return {
            'vendas_hoje': total_vendas,
            'receita_hoje': total_receita,
            'clientes_hoje': total_clientes,
            'ticket_medio_hoje': ticket_medio,
            'ultima_atualizacao': datetime.now().strftime('%H:%M:%S'),
            'status': 'com_vendas' if total_vendas > 0 else 'sem_vendas'
        }
    except Exception as e:
        print(f"Erro ao analisar dados do dia atual: {e}")
        return {
            'vendas_hoje': 0,
            'receita_hoje': 0.0,
            'clientes_hoje': 0,
            'ticket_medio_hoje': 0.0,
            'ultima_atualizacao': datetime.now().strftime('%H:%M:%S'),
            'status': 'erro'
        }

def analyze_sales_movement(dia_atual_data):
    """Analisa movimento APENAS com dados do dia atual - ATUALIZADO"""
    if not dia_atual_data:
        # Se não há dados do dia atual, retornar estrutura vazia para todos os dias
        return generate_empty_movement_analysis()
    
    movement_analysis = []
    day_names_ptbr = {
        'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
        'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    
    # Criar um dicionário para agrupar por dia da semana
    dias_agrupados = {}
    for dia in dia_atual_data:
        dia_semana = day_names_ptbr.get(dia['dia_semana'], dia['dia_semana'])
        if dia_semana not in dias_agrupados:
            dias_agrupados[dia_semana] = {
                'vendas_hoje': 0,
                'receita_hoje': 0,
                'clientes_hoje': 0
            }
        
        dias_agrupados[dia_semana]['vendas_hoje'] += int(dia['total_vendas'])
        dias_agrupados[dia_semana]['receita_hoje'] += float(dia['total_dia'] or 0)
        dias_agrupados[dia_semana]['clientes_hoje'] += int(dia['clientes_unicos'])
    
    # Preencher todos os dias da semana
    todos_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    
    for dia_semana in todos_dias:
        if dia_semana in dias_agrupados:
            dados = dias_agrupados[dia_semana]
            movement_analysis.append({
                'dia_semana': dia_semana,
                'vendas_hoje': dados['vendas_hoje'],
                'receita_hoje': dados['receita_hoje'],
                'clientes_hoje': dados['clientes_hoje'],
                'status': 'com_vendas' if dados['vendas_hoje'] > 0 else 'sem_vendas'
            })
        else:
            movement_analysis.append({
                'dia_semana': dia_semana,
                'vendas_hoje': 0,
                'receita_hoje': 0,
                'clientes_hoje': 0,
                'status': 'sem_vendas'
            })
    
    return movement_analysis

def generate_empty_movement_analysis():
    """Gera análise de movimento vazia para todos os dias"""
    todos_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    movement_analysis = []
    
    for dia_semana in todos_dias:
        movement_analysis.append({
            'dia_semana': dia_semana,
            'vendas_hoje': 0,
            'receita_hoje': 0,
            'clientes_hoje': 0,
            'status': 'sem_vendas'
        })
    
    return movement_analysis

def generate_advanced_predictions(days_raw_data, movement_analysis):
    """Gera previsões avançadas baseadas no histórico de vendas - NOVA FUNÇÃO"""
    if not days_raw_data:
        return generate_fallback_predictions()
    
    try:
        # Agrupar vendas por dia da semana
        daily_patterns = defaultdict(list)
        day_names_ptbr = {
            'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
            'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }
        
        for day in days_raw_data:
            dia_semana = day_names_ptbr.get(day['dia_semana'], day['dia_semana'])
            if day['total_dia'] and float(day['total_dia']) > 0:
                daily_patterns[dia_semana].append(float(day['total_dia']))
        
        # Calcular estatísticas por dia da semana
        daily_stats = {}
        for dia, valores in daily_patterns.items():
            if valores:
                daily_stats[dia] = {
                    'media': np.mean(valores),
                    'mediana': np.median(valores),
                    'desvio_padrao': np.std(valores),
                    'min': np.min(valores),
                    'max': np.max(valores),
                    'count': len(valores)
                }
        
        predictions = []
        today = datetime.now().date()
        
        for i in range(1, 6):  # Próximos 5 dias
            target_date = today + timedelta(days=i)
            dia_semana = target_date.strftime('%A')
            dia_semana_ptbr = day_names_ptbr.get(dia_semana, dia_semana)
            
            # Previsão baseada no padrão histórico do dia da semana
            if dia_semana_ptbr in daily_stats:
                stats = daily_stats[dia_semana_ptbr]
                
                # Usar mediana para evitar outliers
                base_prediction = stats['mediana']
                
                # Ajustar baseado na sazonalidade (finais de semana tendem a ser maiores)
                weekend_factors = {'Sábado': 1.3, 'Domingo': 1.4, 'Sexta': 1.2}
                factor = weekend_factors.get(dia_semana_ptbr, 1.0)
                
                # Ajuste por confiabilidade dos dados
                confidence_factor = min(1.0, stats['count'] / 10)  # Mais dados = mais confiança
                
                prediction_value = base_prediction * factor * confidence_factor
                
                # Determinar confiança
                if stats['count'] >= 8:
                    confianca = 'ALTA'
                elif stats['count'] >= 4:
                    confianca = 'MÉDIA'
                else:
                    confianca = 'BAIXA'
                
                # Determinar tendência
                if stats['count'] > 1:
                    variacao = (stats['max'] - stats['min']) / stats['mediana']
                    if variacao < 0.2:
                        tendencia = 'ESTÁVEL'
                    elif stats['max'] == max(valores[-3:]):  # Últimos valores altos
                        tendencia = 'CRESCENTE'
                    else:
                        tendencia = 'VARIÁVEL'
                else:
                    tendencia = 'INDEFINIDA'
                    
            else:
                # Fallback para dias sem histórico
                prediction_value = 1000.00
                confianca = 'BAIXA'
                tendencia = 'ESTIMADA'
            
            predictions.append({
                'dia': target_date.strftime('%d/%m'),
                'dia_semana': dia_semana_ptbr,
                'previsao': max(0, round(prediction_value, 2)),
                'confianca': confianca,
                'tendencia': tendencia,
                'tecnicas': ['Análise Histórica', 'Padrão Sazonal'],
                'detalhes': f"Baseado em {daily_stats[dia_semana_ptbr]['count'] if dia_semana_ptbr in daily_stats else 0} registros históricos"
            })
        
        return predictions
        
    except Exception as e:
        print(f"Erro ao gerar previsões avançadas: {e}")
        return generate_fallback_predictions()

def generate_fallback_predictions():
    """Gera previsões de fallback"""
    predictions = []
    today = datetime.now()
    day_names_ptbr = {
        'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
        'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    
    for i in range(1, 6):
        target_date = today + timedelta(days=i)
        dia_semana_ptbr = day_names_ptbr.get(target_date.strftime('%A'), target_date.strftime('%A'))
        
        predictions.append({
            'dia': target_date.strftime('%d/%m'),
            'dia_semana': dia_semana_ptbr,
            'previsao': 1000.00,
            'confianca': 'BAIXA',
            'tendencia': 'ESTIMADA',
            'tecnicas': ['Média Básica'],
            'detalhes': 'Dados históricos insuficientes'
        })
    
    return predictions

def analyze_historical_trends(days_raw_data):
    """Analisa padrões históricos para identificar dias mais movimentados"""
    if not days_raw_data:
        return {
            'dias_mais_movimentados': [],
            'tendencia_sazonal': {},
            'fatores_influencia': []
        }
    
    # Agrupar por dia da semana
    daily_patterns = defaultdict(list)
    day_names_ptbr = {
        'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
        'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    
    for day in days_raw_data:
        dia_semana = day_names_ptbr.get(day['dia_semana'], day['dia_semana'])
        if day['total_dia'] and float(day['total_dia']) > 0:
            daily_patterns[dia_semana].append(float(day['total_dia']))
    
    # Calcular médias e identificar padrões
    dias_analise = []
    for dia, valores in daily_patterns.items():
        if valores:
            media = np.mean(valores)
            desvio_padrao = np.std(valores) if len(valores) > 1 else 0
            dias_analise.append({
                'dia_semana': dia,
                'media_receita': media,
                'desvio_padrao': desvio_padrao,
                'total_registros': len(valores),
                'consistencia': 'ALTA' if desvio_padrao < media * 0.3 else 'MEDIA' if desvio_padrao < media * 0.5 else 'BAIXA'
            })
    
    # Ordenar por média de receita (mais movimentados primeiro)
    dias_analise.sort(key=lambda x: x['media_receita'], reverse=True)
    
    # Identificar fatores de influência
    fatores = []
    if any(dia['dia_semana'] in ['Sexta', 'Sábado', 'Domingo'] for dia in dias_analise[:3]):
        fatores.append('Final de semana')
    if any(dia['dia_semana'] in ['Segunda', 'Terça'] for dia in dias_analise[:3]):
        fatores.append('Início da semana')
    if len(fatores) == 0 and dias_analise:
        fatores.append('Padrão consistente')
    
    return {
        'dias_mais_movimentados': dias_analise[:5],  # Top 5 dias
        'tendencia_sazonal': {'padrao': 'ANALISADO' if dias_analise else 'INSUFICIENTE'},
        'fatores_influencia': fatores
    }

def process_days_analysis(days_raw_data):
    """Processa análise tradicional por dia da semana"""
    if not days_raw_data:
        return []
    
    daily_totals = defaultdict(lambda: {'total_vendas': 0, 'total_dia': 0, 'count': 0})
    day_names_ptbr = {
        'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
        'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    
    for day in days_raw_data:
        dia_semana = day_names_ptbr.get(day['dia_semana'], day['dia_semana'])
        daily_totals[dia_semana]['total_vendas'] += float(day['total_vendas'] or 0)
        daily_totals[dia_semana]['total_dia'] += float(day['total_dia'] or 0)
        daily_totals[dia_semana]['count'] += 1
    
    days_analysis = []
    for dia, totals in daily_totals.items():
        if totals['count'] > 0:
            days_analysis.append({
                'dia_semana': dia,
                'total_vendas': totals['total_vendas'],
                'total_dia': totals['total_dia'],
                'media_vendas': totals['total_vendas'] / totals['count'],
                'semanas_analisadas': totals['count']
            })
    
    dia_ordem = {'Segunda': 1, 'Terça': 2, 'Quarta': 3, 'Quinta': 4, 'Sexta': 5, 'Sábado': 6, 'Domingo': 7}
    days_analysis.sort(key=lambda x: dia_ordem.get(x['dia_semana'], 8))
    return days_analysis

def generate_temporal_analysis(days_raw_data, movement_analysis):
    """Gera análise temporal"""
    if not days_raw_data:
        return {
            'dias_pico': [],
            'ticket_medio_geral': 0,
            'long_term_forecast': {}
        }
    
    # Encontrar dias de pico baseado no movimento atual
    dias_com_vendas = [dia for dia in movement_analysis if dia['vendas_hoje'] > 0]
    dias_ordenados = sorted(dias_com_vendas, key=lambda x: x['vendas_hoje'], reverse=True)
    dias_pico = [dia['dia_semana'] for dia in dias_ordenados[:2]] if dias_ordenados else []
    
    # Calcular ticket médio geral do dia atual
    total_vendas_hoje = sum(dia['vendas_hoje'] for dia in movement_analysis)
    total_receita_hoje = sum(dia['receita_hoje'] for dia in movement_analysis)
    ticket_medio_geral = total_receita_hoje / total_vendas_hoje if total_vendas_hoje > 0 else 0
    
    # Previsão de longo prazo baseada no dia atual
    long_term_forecast = {}
    if total_vendas_hoje > 0:
        # Estimativa semanal baseada no desempenho do dia
        previsao_semanal = total_receita_hoje * 7
        previsao_mensal = total_receita_hoje * 30
        
        long_term_forecast = {
            'proxima_semana': {
                'periodo': 'Próxima Semana',
                'previsao_vendas': total_vendas_hoje * 7,
                'previsao_receita': round(previsao_semanal, 2),
                'confianca': 'MEDIA' if total_vendas_hoje > 5 else 'BAIXA'
            },
            'proximo_mes': {
                'periodo': 'Próximo Mês',
                'previsao_vendas': total_vendas_hoje * 30,
                'previsao_receita': round(previsao_mensal, 2),
                'confianca': 'BAIXA'
            }
        }
    
    return {
        'dias_pico': dias_pico,
        'ticket_medio_geral': round(ticket_medio_geral, 2),
        'long_term_forecast': long_term_forecast
    }

# ... (mantenha as outras funções get_low_stock_alerts, get_monthly_sales, get_total_inventory iguais)

def get_low_stock_alerts():
    """Alertas de estoque baixo"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        query = """
        SELECT 
            nome,
            SUM(quantidade) as quantidade_total,
            MAX(estoque_minimo) as estoque_minimo,
            unidade,
            CASE 
                WHEN SUM(quantidade) = 0 THEN 'ZERADO'
                WHEN SUM(quantidade) <= MAX(estoque_minimo) THEN 'BAIXO'
                ELSE 'NORMAL'
            END as status
        FROM produtos 
        WHERE ativo = TRUE 
        GROUP BY nome, unidade
        HAVING quantidade_total = 0 OR quantidade_total <= estoque_minimo
        ORDER BY quantidade_total ASC
        """
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        alerts = cursor.fetchall()
        
        for alert in alerts:
            alert['quantidade'] = alert['quantidade_total']
            for key, value in alert.items():
                if isinstance(value, Decimal):
                    alert[key] = float(value)
        
        return alerts
        
    except Error as e:
        print(f"Erro ao obter alertas de estoque: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            conn.close()

def get_monthly_sales():
    """Vendas mensais com cálculo de lucro"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        query = """
        SELECT 
            DATE_FORMAT(v.data_venda, '%Y-%m') as mes,
            DATE_FORMAT(v.data_venda, '%m/%Y') as mes_formatado,
            COALESCE(SUM(v.valor_total), 0) as total_vendas,
            COUNT(*) as total_vendas_count,
            COALESCE(SUM(v.desconto), 0) as total_desconto,
            COALESCE(SUM(v.valor_total + v.desconto), 0) as receita_bruta,
            COALESCE(SUM(iv.quantidade * p.preco_custo), 0) as custo_total,
            COALESCE(SUM((v.valor_total + v.desconto) - (iv.quantidade * p.preco_custo)), 0) as lucro_bruto,
            COALESCE(SUM(v.valor_total - (iv.quantidade * p.preco_custo)), 0) as lucro_liquido,
            CASE 
                WHEN COALESCE(SUM(v.valor_total + v.desconto), 0) > 0 THEN
                    ROUND((COALESCE(SUM(v.valor_total - (iv.quantidade * p.preco_custo)), 0) / 
                           COALESCE(SUM(v.valor_total + v.desconto), 0)) * 100, 2)
                ELSE 0
            END as margem_lucro
        FROM vendas v
        JOIN itens_venda iv ON v.id = iv.id_venda
        JOIN produtos p ON iv.id_produto = p.id
        WHERE v.data_venda >= DATE_SUB(NOW(), INTERVAL 6 MONTH) AND v.status = 'concluida'
        GROUP BY DATE_FORMAT(v.data_venda, '%Y-%m'), DATE_FORMAT(v.data_venda, '%m/%Y')
        ORDER BY mes DESC
        LIMIT 6
        """
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        monthly_sales = cursor.fetchall()
        
        for sale in monthly_sales:
            for key, value in sale.items():
                if isinstance(value, Decimal):
                    sale[key] = float(value)
        
        return monthly_sales
        
    except Error as e:
        print(f"Erro ao obter vendas mensais: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            conn.close()

def get_total_inventory():
    """Valor total do inventário"""
    conn = get_db_connection()
    if not conn:
        return 0
    
    try:
        query = """
        SELECT SUM(sub.total_produto)
        FROM (
            SELECT 
                nome,
                SUM(quantidade) * AVG(preco_custo) as total_produto
            FROM produtos 
            WHERE ativo = TRUE 
            GROUP BY nome
        ) as sub
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        
        return float(result[0]) if result and result[0] else 0
        
    except Error as e:
        print(f"Erro ao calcular inventário: {e}")
        return 0
    finally:
        if conn and conn.is_connected():
            conn.close()
