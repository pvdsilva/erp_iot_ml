from flask import render_template, jsonify, request
from models import Produto, Venda, Cliente, Fornecedor, Orcamento
from database import db
from datetime import datetime, timedelta
import requests
import os

@app.route('/dashboard')
def dashboard():
    """Página principal do dashboard"""
    try:
        # Buscar alertas de estoque baixo
        low_stock_alerts = get_low_stock_alerts()
        
        # Dados de vendas (exemplo - adapte conforme seu modelo)
        sales_analysis = get_sales_analysis()
        
        # Vendas mensais
        monthly_sales = get_monthly_sales()
        
        # Inventário total
        total_inventory = get_total_inventory()
        
        # Dados meteorológicos padrão (Santos)
        weather_data = get_weather_data('santos')
        
        return render_template('dashboard.html',
                            low_stock_alerts=low_stock_alerts,
                            sales_analysis=sales_analysis,
                            monthly_sales=monthly_sales,
                            total_inventory=total_inventory,
                            weather_data=weather_data)
    
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        # Retorna template com dados vazios em caso de erro
        return render_template('dashboard.html',
                            low_stock_alerts=[],
                            sales_analysis={},
                            monthly_sales=[],
                            total_inventory=0,
                            weather_data={})

def get_low_stock_alerts():
    """Busca produtos com estoque baixo ou zerado"""
    try:
        alerts = Produto.query.filter(
            (Produto.quantidade <= Produto.estoque_minimo) | 
            (Produto.quantidade <= 0)
        ).order_by(Produto.quantidade.asc()).all()
        return alerts
    except Exception as e:
        print(f"Erro ao buscar alertas: {e}")
        return []

def get_sales_analysis():
    """Análise de vendas (adaptar conforme seu modelo)"""
    try:
        # Exemplo - adapte para seu modelo real
        top_products = []
        days_analysis = []
        predictions = []
        
        return {
            'top_products': top_products,
            'days_analysis': days_analysis,
            'predictions': predictions
        }
    except Exception as e:
        print(f"Erro na análise de vendas: {e}")
        return {}

def get_monthly_sales():
    """Vendas mensais (adaptar conforme seu modelo)"""
    try:
        # Exemplo - adapte para seu modelo real
        return []
    except Exception as e:
        print(f"Erro nas vendas mensais: {e}")
        return []

def get_total_inventory():
    """Calcula valor total do inventário"""
    try:
        total = db.session.query(db.func.sum(Produto.quantidade * Produto.preco_custo)).scalar()
        return total or 0
    except Exception as e:
        print(f"Erro no cálculo do inventário: {e}")
        return 0

@app.route('/api/weather/<cidade>')
def get_weather_api(cidade):
    """API para dados meteorológicos"""
    try:
        weather_data = get_weather_data(cidade)
        return jsonify(weather_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_weather_data(cidade):
    """Busca dados meteorológicos (exemplo - implementar com API real)"""
    # Mapeamento de cidades
    cities = {
        'santos': {'name': 'Santos', 'lat': '-23.9608', 'lon': '-46.3336'},
        'sao_vicente': {'name': 'São Vicente', 'lat': '-23.9629', 'lon': '-46.3919'},
        'guaruja': {'name': 'Guarujá', 'lat': '-23.9931', 'lon': '-46.2564'},
        'praia_grande': {'name': 'Praia Grande', 'lat': '-24.0056', 'lon': '-46.4028'},
        'cubatao': {'name': 'Cubatão', 'lat': '-23.8950', 'lon': '-46.4253'},
        'bertioga': {'name': 'Bertioga', 'lat': '-23.8486', 'lon': '-46.1392'},
        'mongagua': {'name': 'Mongaguá', 'lat': '-24.0875', 'lon': '-46.6208'},
        'itanhaem': {'name': 'Itanhaém', 'lat': '-24.1831', 'lon': '-46.7889'},
        'peruibe': {'name': 'Peruíbe', 'lat': '-24.3200', 'lon': '-46.9983'}
    }
    
    city_info = cities.get(cidade, cities['santos'])
    
    # Dados de exemplo - substitua por chamada real à API de clima
    return {
        'city': city_info['name'],
        'current_temp': 25,
        'current_description': 'Parcialmente nublado',
        'current_icon': '02d',
        'wind_speed': 3.5,
        'humidity': 65,
        'forecast': [
            {'day': 'Seg', 'date': '01/01', 'temp_min': 22, 'temp_max': 28, 'icon': '02d', 'recommendation': 'Bom para vendas'},
            {'day': 'Ter', 'date': '02/01', 'temp_min': 23, 'temp_max': 29, 'icon': '01d', 'recommendation': 'Ótimo para vendas'},
            {'day': 'Qua', 'date': '03/01', 'temp_min': 21, 'temp_max': 27, 'icon': '10d', 'recommendation': 'Vendas moderadas'}
        ]
    }

@app.route('/api/dashboard/stats')
def dashboard_stats():
    """API para estatísticas do dashboard"""
    try:
        total_produtos = Produto.query.count()
        total_clientes = Cliente.query.count()
        total_fornecedores = Fornecedor.query.count()
        total_orcamentos = Orcamento.query.count()
        
        return jsonify({
            'success': True,
            'total_produtos': total_produtos,
            'total_clientes': total_clientes,
            'total_fornecedores': total_fornecedores,
            'total_orcamentos': total_orcamentos
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stock/alerts')
def stock_alerts_api():
    """API para alertas de estoque"""
    try:
        alerts = get_low_stock_alerts()
        alerts_data = []
        
        for alert in alerts:
            alerts_data.append({
                'id': alert.id,
                'nome': alert.nome,
                'quantidade': float(alert.quantidade),
                'estoque_minimo': float(alert.estoque_minimo),
                'unidade': alert.unidade,
                'status': 'ESGOTADO' if alert.quantidade <= 0 else 'BAIXO'
            })
        
        return jsonify({
            'success': True,
            'alerts': alerts_data,
            'total': len(alerts_data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
