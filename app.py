from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, make_response
from datetime import timedelta, datetime
import mysql.connector
from mysql.connector import Error
import json
from utils.weather import get_weather_data, get_cidades_baixada_santista
from ml.analysis import analyze_sales_data, get_low_stock_alerts, get_monthly_sales, get_total_inventory
from io import BytesIO
import os
from functools import wraps
import hashlib
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.secret_key = 'erp_iot_ml_secret_key_2025_university_project'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Configuração do banco de dados
db_config = {
    'host': 'localhost',
    'database': 'erp_iot_ml',
    'user': 'erp_user',
    'password': 'erp_password123'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Erro de conexão: {e}")
        # Fallback para configuração local se necessário
        try:
            local_config = {
                'host': 'localhost',
                'database': 'erp_iot_ml',
                'user': 'root',
                'password': 'gerar usuário e senha no php my admin e inserir a senha aqui entre aspas simples'
            }
            conn = mysql.connector.connect(**local_config)
            return conn
        except Error:
            return None

# Sistema de autenticação
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] not in ['administrador', 'proprietario']:
            flash('Acesso restrito a administradores.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Middlewares de segurança
@app.before_request
def check_authentication():
    """Verificar autenticação em todas as requisições"""
    # Se não está logado e tenta acessar páginas protegidas, redireciona para login
    if 'user_id' not in session and request.endpoint and request.endpoint not in ['login', 'static', 'logout', 'health', 'index']:
        return redirect(url_for('login'))

@app.after_request
def after_request(response):
    """Adicionar headers de segurança em TODAS as respostas"""
    # Headers para prevenir cache AGressivamente
    if request.endpoint != 'static':
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    
    # Headers de segurança adicionais
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Header específico para páginas de login
    if request.endpoint == 'login':
        response.headers["X-Login-Page"] = "true"
    
    return response

# Rotas de autenticação
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hash_password(password)
        
        conn = get_db_connection()
        if not conn:
            flash('Erro de conexão com o banco de dados.', 'danger')
            return render_template('login.html')
            
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE username = %s AND password_hash = %s AND ativo = TRUE", 
                          (username, password_hash))
            user = cursor.fetchone()
            
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['user_type'] = user['tipo']
                session['user_name'] = user['nome']
                session.permanent = True
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Usuário ou senha incorretos!', 'danger')
        except Error as e:
            print(f"Erro ao fazer login: {e}")
            flash('Erro interno do sistema. Tente novamente.', 'danger')
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    response = make_response(render_template('login.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    return response

@app.route('/logout')
def logout():
    """Logout seguro com prevenção total de cache e sessão"""
    # Limpar toda a sessão do Flask
    session.clear()
    
    # Criar resposta com headers anti-cache extremamente agressivos
    response = make_response(redirect(url_for('login')))
    
    # Headers para prevenir caching de forma MUITO agressiva
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, no-transform'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Limpar cookies de sessão explicitamente
    response.set_cookie('session', '', expires=0, max_age=0, path='/')
    
    # Adicionar header para forçar recarregamento no cliente
    response.headers['X-Logout'] = 'true'
    
    flash('Você foi desconectado com segurança.', 'info')
    return response

# Dashboard principal
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        weather_data = get_weather_data('Santos,BR')
    except Exception as e:
        print(f"Erro ao obter dados meteorológicos: {e}")
        weather_data = {
            'city': 'Santos',
            'current_temp': 'N/A',
            'current_description': 'Dados não disponíveis',
            'current_icon': '01d',
            'forecast': []
        }
    
    try:
        sales_analysis = analyze_sales_data()
        print(f"DEBUG - Sales Analysis: {sales_analysis}")  # DEBUG
    except Exception as e:
        print(f"Erro na análise de vendas: {e}")
        sales_analysis = {'top_products': [], 'days_analysis': [], 'predictions': []}
    
    try:
        low_stock_alerts = get_low_stock_alerts()
    except Exception as e:
        print(f"Erro nos alertas de estoque: {e}")
        low_stock_alerts = []
    
    try:
        monthly_sales = get_monthly_sales()
    except Exception as e:
        print(f"Erro nas vendas mensais: {e}")
        monthly_sales = []
    
    try:
        total_inventory = get_total_inventory()
    except Exception as e:
        print(f"Erro no inventário total: {e}")
        total_inventory = 0
    
    return render_template('dashboard.html', 
                         weather_data=weather_data,
                         sales_analysis=sales_analysis,
                         low_stock_alerts=low_stock_alerts,
                         monthly_sales=monthly_sales,
                         total_inventory=total_inventory)

# Rotas para gerenciar fornecedores
@app.route('/fornecedores')
@login_required
def fornecedores():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM fornecedores ORDER BY nome")
        fornecedores = cursor.fetchall()
        return render_template('fornecedores/listar.html', fornecedores=fornecedores)
    except Error as e:
        print(f"Erro ao buscar fornecedores: {e}")
        flash('Erro ao carregar fornecedores.', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/fornecedor/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_fornecedor():
    if request.method == 'POST':
        tipo = request.form['tipo']
        nome = request.form['nome']
        documento = request.form['documento']
        email = request.form.get('email', '')
        telefone = request.form.get('telefone', '')
        endereco = request.form.get('endereco', '')
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO fornecedores (tipo, nome, documento, email, telefone, endereco) VALUES (%s, %s, %s, %s, %s, %s)",
                (tipo, nome, documento, email, telefone, endereco)
            )
            conn.commit()
            flash('Fornecedor adicionado com sucesso!', 'success')
            return redirect(url_for('fornecedores'))
        except Error as e:
            print(f"Erro ao adicionar fornecedor: {e}")
            flash('Erro ao adicionar fornecedor.', 'danger')
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    return render_template('fornecedores/adicionar.html')

@app.route('/fornecedor/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_fornecedor(id):
    if request.method == 'POST':
        tipo = request.form['tipo']
        nome = request.form['nome']
        documento = request.form['documento']
        email = request.form.get('email', '')
        telefone = request.form.get('telefone', '')
        endereco = request.form.get('endereco', '')
        ativo = request.form.get('ativo', 0)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE fornecedores SET tipo=%s, nome=%s, documento=%s, email=%s, 
                telefone=%s, endereco=%s, ativo=%s WHERE id=%s""",
                (tipo, nome, documento, email, telefone, endereco, ativo, id)
            )
            conn.commit()
            flash('Fornecedor atualizado com sucesso!', 'success')
            return redirect(url_for('fornecedores'))
        except Error as e:
            print(f"Erro ao editar fornecedor: {e}")
            flash('Erro ao editar fornecedor.', 'danger')
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM fornecedores WHERE id = %s", (id,))
        fornecedor = cursor.fetchone()
        return render_template('fornecedores/editar.html', fornecedor=fornecedor)
    except Error as e:
        print(f"Erro ao carregar fornecedor: {e}")
        flash('Erro ao carregar dados do fornecedor.', 'danger')
        return redirect(url_for('fornecedores'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# Rotas para gerenciar produtos
@app.route('/produtos')
@login_required
def produtos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, f.nome as nome_fornecedor 
            FROM produtos p 
            LEFT JOIN fornecedores f ON p.id_fornecedor = f.id 
            ORDER BY p.nome
        """)
        produtos = cursor.fetchall()
        return render_template('produtos/listar.html', produtos=produtos)
    except Error as e:
        print(f"Erro ao buscar produtos: {e}")
        flash('Erro ao carregar produtos.', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/produto/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_produto():
    if request.method == 'POST':
        nome = request.form['nome']
        data_entrada = request.form['data_entrada']
        quantidade = float(request.form['quantidade'])
        unidade = request.form['unidade']
        id_fornecedor = request.form.get('id_fornecedor') or None
        descricao = request.form.get('descricao', '')
        nota_fiscal = request.form.get('nota_fiscal', '')
        preco_custo = float(request.form['preco_custo'])
        margem_lucro = float(request.form['margem_lucro'])
        preco_venda = preco_custo * (1 + margem_lucro / 100)
        estoque_minimo = int(request.form.get('estoque_minimo', 0))
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO produtos 
                (nome, data_entrada, quantidade, unidade, id_fornecedor, descricao, nota_fiscal, 
                 preco_custo, margem_lucro, preco_venda, estoque_minimo) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (nome, data_entrada, quantidade, unidade, id_fornecedor, descricao, nota_fiscal, 
                 preco_custo, margem_lucro, preco_venda, estoque_minimo)
            )
            conn.commit()
            flash('Produto adicionado com sucesso!', 'success')
            return redirect(url_for('produtos'))
        except Error as e:
            print(f"Erro ao adicionar produto: {e}")
            flash('Erro ao adicionar produto.', 'danger')
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nome FROM fornecedores WHERE ativo = TRUE ORDER BY nome")
        fornecedores = cursor.fetchall()
        return render_template('produtos/adicionar.html', fornecedores=fornecedores)
    except Error as e:
        print(f"Erro ao buscar fornecedores: {e}")
        flash('Erro ao carregar formulário.', 'danger')
        return redirect(url_for('produtos'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/produto/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    if request.method == 'POST':
        nome = request.form['nome']
        data_entrada = request.form['data_entrada']
        quantidade = float(request.form['quantidade'])
        unidade = request.form['unidade']
        id_fornecedor = request.form.get('id_fornecedor') or None
        descricao = request.form.get('descricao', '')
        nota_fiscal = request.form.get('nota_fiscal', '')
        preco_custo = float(request.form['preco_custo'])
        margem_lucro = float(request.form['margem_lucro'])
        preco_venda = preco_custo * (1 + margem_lucro / 100)
        estoque_minimo = int(request.form.get('estoque_minimo', 0))
        ativo = request.form.get('ativo', 0)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE produtos SET nome=%s, data_entrada=%s, quantidade=%s, unidade=%s, 
                id_fornecedor=%s, descricao=%s, nota_fiscal=%s, preco_custo=%s, margem_lucro=%s, 
                preco_venda=%s, estoque_minimo=%s, ativo=%s WHERE id=%s""",
                (nome, data_entrada, quantidade, unidade, id_fornecedor, descricao, nota_fiscal,
                 preco_custo, margem_lucro, preco_venda, estoque_minimo, ativo, id)
            )
            conn.commit()
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('produtos'))
        except Error as e:
            print(f"Erro ao editar produto: {e}")
            flash('Erro ao editar produto.', 'danger')
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM produtos WHERE id = %s", (id,))
        produto = cursor.fetchone()
        
        cursor.execute("SELECT id, nome FROM fornecedores WHERE ativo = TRUE ORDER BY nome")
        fornecedores = cursor.fetchall()
        
        return render_template('produtos/editar.html', produto=produto, fornecedores=fornecedores)
    except Error as e:
        print(f"Erro ao carregar produto: {e}")
        flash('Erro ao carregar dados do produto.', 'danger')
        return redirect(url_for('produtos'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# Rotas para gerenciar clientes
@app.route('/clientes')
@login_required
def clientes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM clientes ORDER BY nome")
        clientes = cursor.fetchall()
        return render_template('clientes/listar.html', clientes=clientes)
    except Error as e:
        print(f"Erro ao buscar clientes: {e}")
        flash('Erro ao carregar clientes.', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/cliente/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_cliente():
    if request.method == 'POST':
        tipo = request.form['tipo']
        nome = request.form['nome']
        documento = request.form.get('documento', '')
        data_nascimento = request.form.get('data_nascimento') or None
        religiao = request.form.get('religiao', '')
        email = request.form.get('email', '')
        telefone_fixo = request.form.get('telefone_fixo', '')
        telefone_celular = request.form.get('telefone_celular', '')
        endereco = request.form.get('endereco', '')
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO clientes 
                (tipo, nome, documento, data_nascimento, religiao, email, telefone_fixo, telefone_celular, endereco) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (tipo, nome, documento, data_nascimento, religiao, email, telefone_fixo, telefone_celular, endereco)
            )
            conn.commit()
            flash('Cliente adicionado com sucesso!', 'success')
            return redirect(url_for('clientes'))
        except Error as e:
            print(f"Erro ao adicionar cliente: {e}")
            flash('Erro ao adicionar cliente.', 'danger')
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    return render_template('clientes/adicionar.html')

@app.route('/cliente/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_cliente(id):
    if request.method == 'POST':
        tipo = request.form['tipo']
        nome = request.form['nome']
        documento = request.form.get('documento', '')
        data_nascimento = request.form.get('data_nascimento') or None
        religiao = request.form.get('religiao', '')
        email = request.form.get('email', '')
        telefone_fixo = request.form.get('telefone_fixo', '')
        telefone_celular = request.form.get('telefone_celular', '')
        endereco = request.form.get('endereco', '')
        ativo = request.form.get('ativo', 0)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE clientes SET tipo=%s, nome=%s, documento=%s, data_nascimento=%s, 
                religiao=%s, email=%s, telefone_fixo=%s, telefone_celular=%s, endereco=%s, ativo=%s 
                WHERE id=%s""",
                (tipo, nome, documento, data_nascimento, religiao, email, telefone_fixo, 
                 telefone_celular, endereco, ativo, id)
            )
            conn.commit()
            flash('Cliente atualizado com sucesso!', 'success')
            return redirect(url_for('clientes'))
        except Error as e:
            print(f"Erro ao editar cliente: {e}")
            flash('Erro ao editar cliente.', 'danger')
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM clientes WHERE id = %s", (id,))
        cliente = cursor.fetchone()
        return render_template('clientes/editar.html', cliente=cliente)
    except Error as e:
        print(f"Erro ao carregar cliente: {e}")
        flash('Erro ao carregar dados do cliente.', 'danger')
        return redirect(url_for('clientes'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# Rotas para gerenciar vendas - CORRIGIDAS
@app.route('/vendas')
@login_required
def vendas():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT v.*, c.nome as nome_cliente 
            FROM vendas v 
            LEFT JOIN clientes c ON v.id_cliente = c.id 
            ORDER BY v.data_venda DESC
        """)
        vendas = cursor.fetchall()
        return render_template('vendas/listar.html', vendas=vendas)
    except Error as e:
        print(f"Erro ao buscar vendas: {e}")
        flash('Erro ao carregar vendas.', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/venda/nova', methods=['GET', 'POST'])
@login_required
def nova_venda():
    if request.method == 'POST':
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Iniciar transação
            conn.start_transaction()
            
            id_cliente = request.form.get('id_cliente') or None
            forma_pagamento = request.form['forma_pagamento']
            observacoes = request.form.get('observacoes', '')
            desconto = float(request.form.get('desconto', 0))
            valor_total = float(request.form.get('valor_total', 0))
            itens = json.loads(request.form.get('itens', '[]'))
            
            # VALIDAÇÃO: Verificar se há itens
            if not itens:
                flash('Adicione pelo menos um item à venda!', 'danger')
                return redirect(url_for('nova_venda'))
            
            # VALIDAÇÃO DE ESTOQUE ANTES de inserir a venda
            for item in itens:
                id_produto = item.get('id_produto')
                quantidade = float(item.get('quantidade'))
                
                cursor.execute("SELECT quantidade, nome FROM produtos WHERE id = %s FOR UPDATE", (id_produto,))
                produto = cursor.fetchone()
                
                if not produto:
                    raise Exception(f"Produto ID {id_produto} não encontrado")
                
                if produto[0] < quantidade:
                    raise Exception(f"Estoque insuficiente para {produto[1]}. Disponível: {produto[0]}, Solicitado: {quantidade}")
            
            # Inserir venda com status definido
            cursor.execute(
                """INSERT INTO vendas (id_cliente, forma_pagamento, observacoes, desconto, valor_total, status) 
                VALUES (%s, %s, %s, %s, %s, 'concluida')""",
                (id_cliente, forma_pagamento, observacoes, desconto, valor_total)
            )
            venda_id = cursor.lastrowid
            
            # Processar itens da venda
            for item in itens:
                id_produto = item.get('id_produto')
                quantidade = float(item.get('quantidade'))
                preco_unitario = float(item.get('preco_unitario'))
                total_item = quantidade * preco_unitario
                
                cursor.execute(
                    """INSERT INTO itens_venda (id_venda, id_produto, quantidade, preco_unitario, total_item)
                    VALUES (%s, %s, %s, %s, %s)""",
                    (venda_id, id_produto, quantidade, preco_unitario, total_item)
                )
                
                # Atualizar estoque do produto
                cursor.execute(
                    "UPDATE produtos SET quantidade = quantidade - %s WHERE id = %s",
                    (quantidade, id_produto)
                )
            
            # Commit da transação
            conn.commit()
            flash('Venda realizada com sucesso!', 'success')
            return redirect(url_for('vendas'))
            
        except Exception as e:
            # Rollback em caso de erro
            if conn:
                conn.rollback()
            print(f"Erro ao processar venda: {e}")
            flash(f'Erro ao processar venda: {str(e)}', 'danger')
            return redirect(url_for('nova_venda'))
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id, nome FROM clientes WHERE ativo = TRUE ORDER BY nome")
        clientes = cursor.fetchall()
        
        cursor.execute("SELECT id, nome, preco_venda, quantidade FROM produtos WHERE ativo = TRUE AND quantidade > 0 ORDER BY nome")
        produtos = cursor.fetchall()
        
        return render_template('vendas/nova.html', clientes=clientes, produtos=produtos)
    except Error as e:
        print(f"Erro ao carregar formulário de venda: {e}")
        flash('Erro ao carregar formulário.', 'danger')
        return redirect(url_for('vendas'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/venda/detalhes/<int:id>')
@login_required
def detalhes_venda(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Buscar dados da venda
        cursor.execute("""
            SELECT v.*, c.nome as nome_cliente, c.email as email_cliente 
            FROM vendas v 
            LEFT JOIN clientes c ON v.id_cliente = c.id 
            WHERE v.id = %s
        """, (id,))
        venda = cursor.fetchone()
        
        if not venda:
            flash('Venda não encontrada.', 'danger')
            return redirect(url_for('vendas'))
        
        # Buscar itens da venda
        cursor.execute("""
            SELECT iv.*, p.nome as nome_produto, p.unidade 
            FROM itens_venda iv 
            JOIN produtos p ON iv.id_produto = p.id 
            WHERE iv.id_venda = %s
        """, (id,))
        itens = cursor.fetchall()
        
        return render_template('vendas/detalhes.html', venda=venda, itens=itens)
        
    except Error as e:
        print(f"Erro ao buscar detalhes da venda: {e}")
        flash('Erro ao carregar detalhes da venda.', 'danger')
        return redirect(url_for('vendas'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/venda/imprimir/<int:id>')
@login_required
def imprimir_venda(id):
    """Gerar PDF da venda com indicação de cancelamento - CORRIGIDO"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Buscar dados da venda
        cursor.execute("""
            SELECT v.*, c.nome as nome_cliente, c.documento as documento_cliente, 
                   c.email as email_cliente, c.telefone_celular, c.endereco as endereco_cliente
            FROM vendas v 
            LEFT JOIN clientes c ON v.id_cliente = c.id 
            WHERE v.id = %s
        """, (id,))
        venda = cursor.fetchone()
        
        if not venda:
            flash('Venda não encontrada.', 'danger')
            return redirect(url_for('vendas'))
        
        # Buscar itens da venda
        cursor.execute("""
            SELECT iv.*, p.nome as nome_produto, p.unidade 
            FROM itens_venda iv 
            JOIN produtos p ON iv.id_produto = p.id 
            WHERE iv.id_venda = %s
        """, (id,))
        itens = cursor.fetchall()
        
        cursor.execute("SELECT * FROM empresa LIMIT 1")
        empresa_data = cursor.fetchone()
        
        # Gerar PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        styles = getSampleStyleSheet()
        
        # Estilo para título com cor vermelha se cancelada
        style_title = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1,
            textColor=colors.red if venda['status'] == 'cancelada' else colors.black
        )
        
        # Título do recibo com indicação de cancelamento
        if venda['status'] == 'cancelada':
            title = Paragraph("RECIBO DE VENDA - CANCELADA", style_title)
        else:
            title = Paragraph("RECIBO DE VENDA", style_title)
        
        elements.append(title)
        
        # Informações da empresa
        if empresa_data:
            empresa_info = [
                f"<b>Empresa:</b> {empresa_data['nome']}",
                f"<b>Documento:</b> {empresa_data['documento']}",
                f"<b>Endereço:</b> {empresa_data['endereco']}",
                f"<b>Telefone:</b> {empresa_data['telefone']}",
                f"<b>Email:</b> {empresa_data['email']}"
            ]
            for info in empresa_info:
                elements.append(Paragraph(info, styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # Informações da venda
        info_venda = [
            f"<b>Nº Venda:</b> {venda['id']}",
            f"<b>Data:</b> {venda['data_venda'].strftime('%d/%m/%Y %H:%M')}",
            f"<b>Forma de Pagamento:</b> {venda['forma_pagamento'].replace('_', ' ').title()}"
        ]
        
        # Adicionar status da venda (com destaque se cancelada)
        status_text = f"<b>Status:</b> <font color='{'red' if venda['status'] == 'cancelada' else 'green'}'>" \
                     f"{venda['status'].upper()}</font>"
        info_venda.append(status_text)
        
        if venda['nome_cliente']:
            info_venda.insert(2, f"<b>Cliente:</b> {venda['nome_cliente']}")
            if venda['documento_cliente']:
                info_venda.insert(3, f"<b>Documento:</b> {venda['documento_cliente']}")
        
        for info in info_venda:
            elements.append(Paragraph(info, styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # Itens da venda
        data = [['Produto', 'Quantidade', 'Unitário', 'Total']]
        
        for item in itens:
            data.append([
                item['nome_produto'],
                f"{item['quantidade']} {item['unidade']}",
                f"R$ {item['preco_unitario']:.2f}",
                f"R$ {item['total_item']:.2f}"
            ])
        
        # TOTALS - CORRIGIDO: Sem tags HTML
        subtotal = venda['valor_total'] + venda['desconto']
        
        # Adicionar linha em branco para separação
        data.append(['', '', '', ''])
        
        # Subtotal
        data.append(['', '', 'Subtotal:', f"R$ {subtotal:.2f}"])
        
        # Desconto (se houver)
        if venda['desconto'] > 0:
            data.append(['', '', 'Desconto:', f"-R$ {venda['desconto']:.2f}"])
        
        # Total
        data.append(['', '', 'TOTAL:', f"R$ {venda['valor_total']:.2f}"])
        
        table = Table(data)
        
        # Estilo da tabela com cor de fundo diferente para vendas canceladas
        if venda['status'] == 'cancelada':
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -4), colors.lightgrey),
                ('BACKGROUND', (0, -3), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.darkred)
            ])
        else:
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -4), colors.beige),
                ('BACKGROUND', (0, -3), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])
        
        table.setStyle(table_style)
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Aviso de cancelamento em destaque
        if venda['status'] == 'cancelada':
            warning_style = ParagraphStyle(
                'Warning',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.red,
                backColor=colors.yellow,
                borderPadding=10,
                alignment=1
            )
            warning_text = Paragraph(
                "<b>⚠️ ATENÇÃO: ESTA VENDA FOI CANCELADA ⚠️</b><br/>" +
                "Os produtos foram repostos no estoque e esta venda não é válida.",
                warning_style
            )
            elements.append(warning_text)
            elements.append(Spacer(1, 10))
        
        # Observações
        if venda['observacoes']:
            elements.append(Paragraph("<b>Observações:</b>", styles['Normal']))
            elements.append(Paragraph(venda['observacoes'], styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # Rodapé com data de impressão
        footer_text = f"Recibo gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        if venda['status'] == 'cancelada':
            footer_text += " - VENDA CANCELADA"
        
        footer = Paragraph(footer_text, styles['Italic'])
        elements.append(footer)
        
        doc.build(elements)
        buffer.seek(0)
        
        # Nome do arquivo com indicação de cancelamento
        filename = f"recibo_venda_{venda['id']}"
        if venda['status'] == 'cancelada':
            filename += "_CANCELADA"
        filename += f"_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Error as e:
        print(f"Erro ao gerar PDF da venda: {e}")
        flash('Erro ao gerar PDF.', 'danger')
        return redirect(url_for('vendas'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/vendas/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar_venda(id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Iniciar transação
        conn.start_transaction()
        
        # Verificar se a venda existe e obter seu status com lock
        cursor.execute("SELECT status FROM vendas WHERE id = %s FOR UPDATE", (id,))
        venda = cursor.fetchone()
        
        if not venda:
            return jsonify({'success': False, 'error': 'Venda não encontrada'}), 404
            
        if venda['status'] == 'cancelada':
            return jsonify({'success': False, 'error': 'Venda já está cancelada'}), 400
        
        # Buscar itens da venda para repor estoque
        cursor.execute("""
            SELECT iv.id_produto, iv.quantidade 
            FROM itens_venda iv 
            WHERE iv.id_venda = %s
        """, (id,))
        itens = cursor.fetchall()
        
        # Repor estoque para cada item da venda
        for item in itens:
            cursor.execute(
                "UPDATE produtos SET quantidade = quantidade + %s WHERE id = %s",
                (item['quantidade'], item['id_produto'])
            )
        
        # Atualizar status da venda para cancelada
        cursor.execute(
            "UPDATE vendas SET status = 'cancelada' WHERE id = %s",
            (id,)
        )
        
        # Commit da transação
        conn.commit()
        return jsonify({'success': True, 'message': 'Venda cancelada e estoque reposto com sucesso'})
        
    except Exception as e:
        # Rollback em caso de erro
        if conn:
            conn.rollback()
        print(f"Erro ao cancelar venda: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ... (o restante do código permanece igual - orçamentos, empresa, usuários, etc.)

# Rotas para gerenciar orçamentos
@app.route('/orcamentos')
@login_required
def orcamentos():
    """Listar todos os orçamentos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT o.*, c.nome as nome_cliente 
            FROM orcamentos o 
            LEFT JOIN clientes c ON o.id_cliente = c.id 
            ORDER BY o.data_criacao DESC
        """)
        orcamentos = cursor.fetchall()
        return render_template('orcamentos/listar.html', orcamentos=orcamentos)
    except Error as e:
        print(f"Erro ao buscar orçamentos: {e}")
        flash('Erro ao carregar orçamentos.', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/orcamento/novo', methods=['GET', 'POST'])
@login_required
def novo_orcamento():
    """Criar novo orçamento com carrinho de itens"""
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            id_cliente = request.form.get('id_cliente') or None
            forma_pagamento = request.form['forma_pagamento']
            validade = int(request.form.get('validade', 7))
            condicoes_pagamento = request.form.get('condicoes_pagamento', '')
            observacoes = request.form.get('observacoes', '')
            desconto = float(request.form.get('desconto', 0))
            valor_total = float(request.form.get('valor_total', 0))
            itens = json.loads(request.form.get('itens', '[]'))
            
            # Inserir orçamento
            cursor.execute(
                """INSERT INTO orcamentos 
                (id_cliente, forma_pagamento, validade, condicoes_pagamento, observacoes, desconto, valor_total) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (id_cliente, forma_pagamento, validade, condicoes_pagamento, observacoes, desconto, valor_total)
            )
            orcamento_id = cursor.lastrowid
            
            # Processar itens do orçamento
            for item in itens:
                id_produto = item.get('id_produto')
                quantidade = float(item.get('quantidade'))
                preco_unitario = float(item.get('preco_unitario'))
                total_item = quantidade * preco_unitario
                
                cursor.execute(
                    """INSERT INTO itens_orcamento (id_orcamento, id_produto, quantidade, preco_unitario, total_item)
                    VALUES (%s, %s, %s, %s, %s)""",
                    (orcamento_id, id_produto, quantidade, preco_unitario, total_item)
                )
            
            conn.commit()
            flash('Orçamento criado com sucesso!', 'success')
            return redirect(url_for('detalhes_orcamento', id=orcamento_id))
            
        except Error as e:
            print(f"Erro ao processar orçamento: {e}")
            flash('Erro ao processar orçamento.', 'danger')
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id, nome FROM clientes WHERE ativo = TRUE ORDER BY nome")
        clientes = cursor.fetchall()
        
        cursor.execute("SELECT id, nome, preco_venda, quantidade FROM produtos WHERE ativo = TRUE AND quantidade > 0 ORDER BY nome")
        produtos = cursor.fetchall()
        
        return render_template('orcamentos/novo.html', clientes=clientes, produtos=produtos)
    except Error as e:
        print(f"Erro ao carregar formulário de orçamento: {e}")
        flash('Erro ao carregar formulário.', 'danger')
        return redirect(url_for('orcamentos'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/orcamento/detalhes/<int:id>')
@login_required
def detalhes_orcamento(id):
    """Visualizar detalhes de um orçamento"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Buscar dados do orçamento
        cursor.execute("""
            SELECT o.*, c.nome as nome_cliente, c.email as email_cliente, c.telefone_celular
            FROM orcamentos o 
            LEFT JOIN clientes c ON o.id_cliente = c.id 
            WHERE o.id = %s
        """, (id,))
        orcamento = cursor.fetchone()
        
        if not orcamento:
            flash('Orçamento não encontrado.', 'danger')
            return redirect(url_for('orcamentos'))
        
        # Buscar itens do orçamento
        cursor.execute("""
            SELECT io.*, p.nome as nome_produto, p.unidade 
            FROM itens_orcamento io 
            JOIN produtos p ON io.id_produto = p.id 
            WHERE io.id_orcamento = %s
        """, (id,))
        itens = cursor.fetchall()
        
        return render_template('orcamentos/detalhes.html', orcamento=orcamento, itens=itens)
        
    except Error as e:
        print(f"Erro ao buscar detalhes do orçamento: {e}")
        flash('Erro ao carregar detalhes do orçamento.', 'danger')
        return redirect(url_for('orcamentos'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/orcamento/imprimir/<int:id>')
@login_required
def imprimir_orcamento(id):
    """Gerar PDF do orçamento - CORRIGIDO"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Buscar dados do orçamento
        cursor.execute("""
            SELECT o.*, c.nome as nome_cliente, c.documento as documento_cliente, 
                   c.email as email_cliente, c.telefone_celular, c.endereco as endereco_cliente
            FROM orcamentos o 
            LEFT JOIN clientes c ON o.id_cliente = c.id 
            WHERE o.id = %s
        """, (id,))
        orcamento = cursor.fetchone()
        
        if not orcamento:
            flash('Orçamento não encontrado.', 'danger')
            return redirect(url_for('orcamentos'))
        
        # Buscar itens do orçamento
        cursor.execute("""
            SELECT io.*, p.nome as nome_produto, p.unidade 
            FROM itens_orcamento io 
            JOIN produtos p ON io.id_produto = p.id 
            WHERE io.id_orcamento = %s
        """, (id,))
        itens = cursor.fetchall()
        
        cursor.execute("SELECT * FROM empresa LIMIT 1")
        empresa_data = cursor.fetchone()
        
        # Gerar PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        styles = getSampleStyleSheet()
        style_title = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1
        )
        
        title = Paragraph("ORÇAMENTO", style_title)
        elements.append(title)
        
        # Informações da empresa
        if empresa_data:
            empresa_info = [
                f"<b>Empresa:</b> {empresa_data['nome']}",
                f"<b>Documento:</b> {empresa_data['documento']}",
                f"<b>Endereço:</b> {empresa_data['endereco']}",
                f"<b>Telefone:</b> {empresa_data['telefone']}",
                f"<b>Email:</b> {empresa_data['email']}"
            ]
            for info in empresa_info:
                elements.append(Paragraph(info, styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # Informações do orçamento
        info_orcamento = [
            f"<b>Nº Orçamento:</b> {orcamento['id']}",
            f"<b>Data:</b> {orcamento['data_criacao'].strftime('%d/%m/%Y %H:%M')}",
            f"<b>Validade:</b> {orcamento['validade']} dias",
            f"<b>Forma de Pagamento:</b> {orcamento['forma_pagamento'].replace('_', ' ').title()}"
        ]
        
        if orcamento['nome_cliente']:
            info_orcamento.insert(2, f"<b>Cliente:</b> {orcamento['nome_cliente']}")
            if orcamento['documento_cliente']:
                info_orcamento.insert(3, f"<b>Documento:</b> {orcamento['documento_cliente']}")
        
        for info in info_orcamento:
            elements.append(Paragraph(info, styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # Itens do orçamento
        data = [['Produto', 'Quantidade', 'Unitário', 'Total']]
        
        for item in itens:
            data.append([
                item['nome_produto'],
                f"{item['quantidade']} {item['unidade']}",
                f"R$ {item['preco_unitario']:.2f}",
                f"R$ {item['total_item']:.2f}"
            ])
        
        # TOTAIS - CORRIGIDO: Sem tags HTML
        subtotal = orcamento['valor_total'] + orcamento['desconto']
        
        # Adicionar linha em branco para separação
        data.append(['', '', '', ''])
        
        # Subtotal
        data.append(['', '', 'Subtotal:', f"R$ {subtotal:.2f}"])
        
        # Desconto (se houver)
        if orcamento['desconto'] > 0:
            data.append(['', '', 'Desconto:', f"-R$ {orcamento['desconto']:.2f}"])
        
        # Total
        data.append(['', '', 'TOTAL:', f"R$ {orcamento['valor_total']:.2f}"])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -4), colors.beige),
            ('BACKGROUND', (0, -3), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Observações
        if orcamento['observacoes']:
            elements.append(Paragraph("<b>Observações:</b>", styles['Normal']))
            elements.append(Paragraph(orcamento['observacoes'], styles['Normal']))
            elements.append(Spacer(1, 10))
        
        if orcamento['condicoes_pagamento']:
            elements.append(Paragraph("<b>Condições de Pagamento:</b>", styles['Normal']))
            elements.append(Paragraph(orcamento['condicoes_pagamento'], styles['Normal']))
        
        elements.append(Spacer(1, 20))
        footer = Paragraph(f"Orçamento gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Italic'])
        elements.append(footer)
        
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"orcamento_{orcamento['id']}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mimetype='application/pdf'
        )
        
    except Error as e:
        print(f"Erro ao gerar PDF do orçamento: {e}")
        flash('Erro ao gerar PDF.', 'danger')
        return redirect(url_for('orcamentos'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
@app.route('/orcamento/aprovar/<int:id>')
@login_required
def aprovar_orcamento(id):
    """Aprovar orçamento - VERSÃO SEGURA"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        print(f"🔧 DEBUG: Aprovando orçamento {id}")
        
        # Primeiro verificar o status atual
        cursor.execute("SELECT status FROM orcamentos WHERE id = %s", (id,))
        orcamento = cursor.fetchone()
        
        if not orcamento:
            flash('Orçamento não encontrado.', 'danger')
            return redirect(url_for('orcamentos'))
        
        print(f"🔧 DEBUG: Status atual: {orcamento['status']}")
        
        # Atualizar APENAS se for pendente
        if orcamento['status'] == 'pendente':
            cursor.execute(
                "UPDATE orcamentos SET status = 'aprovado' WHERE id = %s",
                (id,)
            )
            conn.commit()
            print(f"🔧 DEBUG: Orçamento {id} aprovado com sucesso")
            flash('Orçamento aprovado com sucesso!', 'success')
        else:
            flash(f'Não é possível aprovar um orçamento com status: {orcamento["status"]}', 'warning')
        
    except Error as e:
        print(f"❌ ERRO ao aprovar orçamento {id}: {e}")
        flash('Erro ao aprovar orçamento.', 'danger')
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    
    return redirect(url_for('orcamentos'))

@app.route('/orcamento/cancelar/<int:id>')
@login_required
def cancelar_orcamento(id):
    """Cancelar orçamento com validação"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        print(f"DEBUG: Tentando cancelar orçamento {id}")
        
        # Primeiro verificar se o orçamento existe e seu status atual
        cursor.execute("SELECT status FROM orcamentos WHERE id = %s", (id,))
        orcamento = cursor.fetchone()
        
        if not orcamento:
            flash('Orçamento não encontrado.', 'danger')
            return redirect(url_for('orcamentos'))
            
        if orcamento['status'] == 'cancelado':
            flash('Este orçamento já está cancelado.', 'warning')
            return redirect(url_for('orcamentos'))
            
        if orcamento['status'] == 'convertido':
            flash('Não é possível cancelar um orçamento já convertido em venda.', 'danger')
            return redirect(url_for('orcamentos'))
        
        # Atualizar status para cancelado
        cursor.execute(
            "UPDATE orcamentos SET status = 'cancelado' WHERE id = %s",
            (id,)
        )
        conn.commit()
        
        print(f"DEBUG: Orçamento {id} cancelado com sucesso")
        flash('Orçamento cancelado com sucesso!', 'success')
        
    except Error as e:
        print(f"ERRO ao cancelar orçamento {id}: {e}")
        flash('Erro ao cancelar orçamento.', 'danger')
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    
    return redirect(url_for('orcamentos'))

@app.route('/orcamento/converter-venda/<int:id>')
@login_required
def converter_orcamento_venda(id):
    """Converter orçamento em venda - VERSÃO CORRIGIDA"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        print(f"🔄 DEBUG: Iniciando conversão do orçamento {id}")
        
        # Buscar dados do orçamento
        cursor.execute("""
            SELECT o.*, c.nome as nome_cliente 
            FROM orcamentos o 
            LEFT JOIN clientes c ON o.id_cliente = c.id 
            WHERE o.id = %s
        """, (id,))
        orcamento = cursor.fetchone()
        
        if not orcamento:
            flash('Orçamento não encontrado.', 'danger')
            return redirect(url_for('orcamentos'))
        
        print(f"🔍 DEBUG: Orçamento {id} - Status: {orcamento['status']}")
        
        # Validar status
        if orcamento['status'] not in ['pendente', 'aprovado']:
            flash(f'Não é possível converter um orçamento com status: {orcamento["status"]}', 'danger')
            return redirect(url_for('detalhes_orcamento', id=id))
        
        # Buscar itens do orçamento
        cursor.execute("""
            SELECT io.*, p.nome as nome_produto, p.unidade, p.quantidade as estoque_atual
            FROM itens_orcamento io 
            JOIN produtos p ON io.id_produto = p.id 
            WHERE io.id_orcamento = %s
        """, (id,))
        itens = cursor.fetchall()
        
        if not itens:
            flash('Orçamento não possui itens para converter.', 'danger')
            return redirect(url_for('detalhes_orcamento', id=id))
        
        # Verificar estoque
        estoque_insuficiente = []
        for item in itens:
            if item['quantidade'] > item['estoque_atual']:
                estoque_insuficiente.append(
                    f"{item['nome_produto']} (Necessário: {item['quantidade']}, Disponível: {item['estoque_atual']})"
                )
        
        if estoque_insuficiente:
            flash(f'Estoque insuficiente: {", ".join(estoque_insuficiente)}', 'danger')
            return redirect(url_for('detalhes_orcamento', id=id))
        
        # CRIAR VENDA - SEM STATUS (para evitar o erro)
        cursor.execute(
            """INSERT INTO vendas (id_cliente, forma_pagamento, observacoes, desconto, valor_total, status) 
            VALUES (%s, %s, %s, %s, %s, 'concluida')""",
            (orcamento['id_cliente'], orcamento['forma_pagamento'], 
             f"Convertido do orçamento #{orcamento['id']}", 
             orcamento['desconto'], orcamento['valor_total'])
        )
        venda_id = cursor.lastrowid
        
        print(f"💰 DEBUG: Venda {venda_id} criada")
        
        # Processar itens da venda
        for item in itens:
            cursor.execute(
                """INSERT INTO itens_venda (id_venda, id_produto, quantidade, preco_unitario, total_item)
                VALUES (%s, %s, %s, %s, %s)""",
                (venda_id, item['id_produto'], item['quantidade'], 
                 item['preco_unitario'], item['total_item'])
            )
            
            # Atualizar estoque
            cursor.execute(
                """UPDATE produtos SET quantidade = quantidade - %s WHERE id = %s""",
                (item['quantidade'], item['id_produto'])
            )
        
        # Atualizar status do orçamento para convertido
        cursor.execute(
            "UPDATE orcamentos SET status = 'convertido' WHERE id = %s",
            (id,)
        )
        
        conn.commit()
        
        print(f"✅ DEBUG: Conversão concluída - Orçamento {id} → Venda {venda_id}")
        flash(f'Orçamento convertido em venda #{venda_id} com sucesso!', 'success')
        return redirect(url_for('detalhes_venda', id=venda_id))
        
    except Error as e:
        print(f"❌ ERRO na conversão do orçamento {id}: {e}")
        flash(f'Erro ao converter orçamento em venda: {str(e)}', 'danger')
        return redirect(url_for('orcamentos'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# Rotas para gerenciar empresa
@app.route('/empresa')
@login_required
def empresa():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM empresa LIMIT 1")
        empresa_data = cursor.fetchone()
        return render_template('empresa/editar.html', empresa=empresa_data)
    except Error as e:
        print(f"Erro ao buscar dados da empresa: {e}")
        flash('Erro ao carregar dados da empresa.', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/empresa/editar', methods=['POST'])
@login_required
def editar_empresa():
    if request.method == 'POST':
        tipo = request.form['tipo']
        nome = request.form['nome']
        documento = request.form['documento']
        email = request.form.get('email', '')
        telefone = request.form.get('telefone', '')
        endereco = request.form.get('endereco', '')
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM empresa")
            count = cursor.fetchone()[0]
            
            if count > 0:
                cursor.execute(
                    """UPDATE empresa SET tipo=%s, nome=%s, documento=%s, email=%s, telefone=%s, endereco=%s""",
                    (tipo, nome, documento, email, telefone, endereco)
                )
            else:
                cursor.execute(
                    """INSERT INTO empresa (tipo, nome, documento, email, telefone, endereco) 
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (tipo, nome, documento, email, telefone, endereco)
                )
            
            conn.commit()
            flash('Dados da empresa atualizados com sucesso!', 'success')
            return redirect(url_for('empresa'))
        except Error as e:
            print(f"Erro ao atualizar dados da empresa: {e}")
            flash('Erro ao atualizar dados da empresa.', 'danger')
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    return redirect(url_for('empresa'))

# Rotas para gerenciar usuários
@app.route('/usuarios')
@login_required
@admin_required
def usuarios():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios ORDER BY nome")
        usuarios = cursor.fetchall()
        return render_template('usuarios/listar.html', usuarios=usuarios)
    except Error as e:
        print(f"Erro ao buscar usuários: {e}")
        flash('Erro ao carregar usuários.', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/usuario/adicionar', methods=['GET', 'POST'])
@login_required
@admin_required
def adicionar_usuario():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hash_password(password)
        tipo = request.form['tipo']
        nome = request.form['nome']
        cpf = request.form.get('cpf', '').strip() or None
        telefone = request.form.get('telefone', '')
        email = request.form.get('email', '')
        endereco = request.form.get('endereco', '')
        tipo_sanguineo = request.form.get('tipo_sanguineo', '')
        cor = request.form.get('cor', '')
        altura = request.form.get('altura', '')
        cor_cabelos = request.form.get('cor_cabelos', '')
        estado_civil = request.form.get('estado_civil', '')
        conjugue = request.form.get('conjugue', '')
        filhos = request.form.get('filhos', 0)
        funcao = request.form.get('funcao', '')
        departamento = request.form.get('departamento', '')
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO usuarios 
                (username, password_hash, tipo, nome, cpf, telefone, email, endereco, tipo_sanguineo, cor, altura, cor_cabelos, estado_civil, conjugue, filhos, funcao, departamento) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (username, password_hash, tipo, nome, cpf, telefone, email, endereco, tipo_sanguineo, cor, altura, cor_cabelos, estado_civil, conjugue, filhos, funcao, departamento)
            )
            conn.commit()
            flash('Usuário adicionado com sucesso!', 'success')
            return redirect(url_for('usuarios'))
        except Error as e:
            print(f"Erro ao adicionar usuário: {e}")
            flash('Erro ao adicionar usuário.', 'danger')
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    return render_template('usuarios/adicionar.html')

@app.route('/usuario/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    if request.method == 'POST':
        username = request.form['username']
        tipo = request.form['tipo']
        nome = request.form['nome']
        cpf = request.form.get('cpf', '').strip() or None
        telefone = request.form.get('telefone', '').strip() or None
        email = request.form.get('email', '').strip() or None
        endereco = request.form.get('endereco', '').strip() or None
        tipo_sanguineo = request.form.get('tipo_sanguineo', '').strip() or None
        cor = request.form.get('cor', '').strip() or None
        altura = request.form.get('altura', '').strip() or None
        cor_cabelos = request.form.get('cor_cabelos', '').strip() or None
        estado_civil = request.form.get('estado_civil', '').strip() or None
        conjugue = request.form.get('conjugue', '').strip() or None
        filhos = request.form.get('filhos', 0) or 0
        funcao = request.form.get('funcao', '').strip() or None
        departamento = request.form.get('departamento', '').strip() or None
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if request.form.get('password'):
                password_hash = hash_password(request.form['password'])
                cursor.execute(
                    """UPDATE usuarios SET username=%s, password_hash=%s, tipo=%s, nome=%s, 
                    cpf=%s, telefone=%s, email=%s, endereco=%s, tipo_sanguineo=%s, cor=%s, 
                    altura=%s, cor_cabelos=%s, estado_civil=%s, conjugue=%s, filhos=%s, 
                    funcao=%s, departamento=%s WHERE id=%s""",
                    (username, password_hash, tipo, nome, cpf, telefone, email, endereco, 
                     tipo_sanguineo, cor, altura, cor_cabelos, estado_civil, conjugue, 
                     filhos, funcao, departamento, id)
                )
            else:
                cursor.execute(
                    """UPDATE usuarios SET username=%s, tipo=%s, nome=%s, 
                    cpf=%s, telefone=%s, email=%s, endereco=%s, tipo_sanguineo=%s, cor=%s, 
                    altura=%s, cor_cabelos=%s, estado_civil=%s, conjugue=%s, filhos=%s, 
                    funcao=%s, departamento=%s WHERE id=%s""",
                    (username, tipo, nome, cpf, telefone, email, endereco, 
                     tipo_sanguineo, cor, altura, cor_cabelos, estado_civil, conjugue, 
                     filhos, funcao, departamento, id)
                )
            
            conn.commit()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('usuarios'))
            
        except Error as e:
            print(f"Erro ao editar usuário: {e}")
            flash(f'Erro ao editar usuário: {str(e)}', 'danger')
            return redirect(url_for('editar_usuario', id=id))
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
        usuario = cursor.fetchone()
        
        if not usuario:
            flash('Usuário não encontrado.', 'danger')
            return redirect(url_for('usuarios'))
        
        return render_template('usuarios/editar.html', usuario=usuario)
        
    except Error as e:
        print(f"Erro ao carregar usuário: {e}")
        flash('Erro ao carregar dados do usuário.', 'danger')
        return redirect(url_for('usuarios'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/usuario/toggle/<int:id>')
@login_required
@admin_required
def toggle_usuario(id):
    """Ativa/desativa usuário"""
    if id == session.get('user_id'):
        flash('Você não pode desativar sua própria conta!', 'danger')
        return redirect(url_for('usuarios'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT ativo FROM usuarios WHERE id = %s", (id,))
        usuario = cursor.fetchone()
        
        if usuario:
            novo_estado = not usuario['ativo']
            cursor.execute("UPDATE usuarios SET ativo = %s WHERE id = %s", (novo_estado, id))
            conn.commit()
            
            acao = "ativado" if novo_estado else "desativado"
            flash(f'Usuário {acao} com sucesso!', 'success')
        else:
            flash('Usuário não encontrado.', 'danger')
            
    except Error as e:
        print(f"Erro ao alterar estado do usuário: {e}")
        flash('Erro ao alterar estado do usuário.', 'danger')
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    
    return redirect(url_for('usuarios'))

# Rota para relatório de inventário
@app.route('/relatorio/inventario')
@login_required
def relatorio_inventario():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT p.nome, p.quantidade, p.unidade, p.preco_custo, p.preco_venda, 
                   (p.quantidade * p.preco_custo) as valor_total, f.nome as fornecedor
            FROM produtos p
            LEFT JOIN fornecedores f ON p.id_fornecedor = f.id
            WHERE p.ativo = TRUE
            ORDER BY p.nome
        """)
        produtos = cursor.fetchall()
        
        cursor.execute("SELECT SUM(quantidade * preco_custo) as total FROM produtos WHERE ativo = TRUE")
        total_inventario = cursor.fetchone()['total'] or 0
        
        cursor.execute("SELECT * FROM empresa LIMIT 1")
        empresa_data = cursor.fetchone()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        styles = getSampleStyleSheet()
        style_title = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1
        )
        
        title = Paragraph("Relatório de Inventário", style_title)
        elements.append(title)
        
        if empresa_data:
            empresa_info = [
                f"Empresa: {empresa_data['nome']}",
                f"Documento: {empresa_data['documento']}",
                f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            ]
            for info in empresa_info:
                elements.append(Paragraph(info, styles['Normal']))
                elements.append(Spacer(1, 5))
        
        elements.append(Spacer(1, 20))
        
        data = [['Produto', 'Quantidade', 'Unidade', 'Preço Custo', 'Preço Venda', 'Valor Total', 'Fornecedor']]
        
        for produto in produtos:
            data.append([
                produto['nome'],
                str(produto['quantidade']),
                produto['unidade'],
                f"R$ {produto['preco_custo']:.2f}",
                f"R$ {produto['preco_venda']:.2f}",
                f"R$ {produto['valor_total']:.2f}",
                produto['fornecedor'] or 'N/A'
            ])
        
        data.append(['TOTAL', '', '', '', '', f"R$ {total_inventario:.2f}", ''])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        footer = Paragraph(f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} por {session.get('user_name', 'Sistema')}", styles['Italic'])
        elements.append(footer)
        
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"relatorio_inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )
        
    except Error as e:
        print(f"Erro ao gerar relatório: {e}")
        flash('Erro ao gerar relatório.', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
# =============================================
# ROTAS DE RELATÓRIOS - PRODUTOS VENDIDOS POR MÊS
# =============================================

@app.route('/relatorio/produtos-vendidos-mensal')
@login_required
def relatorio_produtos_vendidos_mensal():
    """Relatório de produtos vendidos no mês vigente com análise de rentabilidade"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Buscar produtos vendidos no mês atual
        query = """
        SELECT 
            p.nome,
            p.unidade,
            p.preco_custo,
            SUM(iv.quantidade) as quantidade_vendida,
            SUM(iv.total_item) as receita_total,
            AVG(iv.preco_unitario) as preco_medio_venda,
            SUM(iv.quantidade * p.preco_custo) as custo_total,
            SUM(iv.total_item - (iv.quantidade * p.preco_custo)) as lucro_total,
            CASE 
                WHEN SUM(iv.quantidade * p.preco_custo) > 0 THEN
                    ROUND((SUM(iv.total_item - (iv.quantidade * p.preco_custo)) / 
                           SUM(iv.quantidade * p.preco_custo)) * 100, 2)
                ELSE 0
            END as margem_lucro_percentual,
            RANK() OVER (ORDER BY SUM(iv.total_item - (iv.quantidade * p.preco_custo)) DESC) as ranking_rentabilidade
        FROM itens_venda iv
        JOIN produtos p ON iv.id_produto = p.id
        JOIN vendas v ON iv.id_venda = v.id
        WHERE v.status = 'concluida'
          AND YEAR(v.data_venda) = YEAR(CURRENT_DATE)
          AND MONTH(v.data_venda) = MONTH(CURRENT_DATE)
        GROUP BY p.id, p.nome, p.unidade, p.preco_custo
        ORDER BY lucro_total DESC
        """
        
        cursor.execute(query)
        produtos = cursor.fetchall()
        
        # Calcular totais
        total_receita = sum(float(prod['receita_total'] or 0) for prod in produtos)
        total_lucro = sum(float(prod['lucro_total'] or 0) for prod in produtos)
        total_vendas = sum(float(prod['quantidade_vendida'] or 0) for prod in produtos)
        
        cursor.execute("SELECT * FROM empresa LIMIT 1")
        empresa_data = cursor.fetchone()
        
        # Gerar PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        styles = getSampleStyleSheet()
        style_title = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1
        )
        
        # Título
        mes_atual = datetime.now().strftime('%B/%Y').title()
        title = Paragraph(f"Relatório de Produtos Vendidos - {mes_atual}", style_title)
        elements.append(title)
        
        # Informações da empresa
        if empresa_data:
            empresa_info = [
                f"<b>Empresa:</b> {empresa_data['nome']}",
                f"<b>Documento:</b> {empresa_data['documento']}",
                f"<b>Endereço:</b> {empresa_data['endereco']}",
                f"<b>Data de emissão:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            ]
            for info in empresa_info:
                elements.append(Paragraph(info, styles['Normal']))
                elements.append(Spacer(1, 5))
        
        elements.append(Spacer(1, 20))
        
        # Resumo do mês
        resumo_data = [
            ['Total de Receita', f"R$ {total_receita:.2f}"],
            ['Total de Lucro', f"R$ {total_lucro:.2f}"],
            ['Quantidade Total Vendida', f"{total_vendas:.0f} unidades"],
            ['Margem Média', f"{(total_lucro/total_receita*100) if total_receita > 0 else 0:.2f}%"],
            ['Produtos com Vendas', f"{len(produtos)} produtos"]
        ]
        
        resumo_table = Table(resumo_data, colWidths=[200, 150])
        resumo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(resumo_table)
        elements.append(Spacer(1, 20))
        
        # Tabela de produtos
        if produtos:
            # Cabeçalho da tabela
            data = [['Produto', 'Qtd Vendida', 'Receita', 'Custo', 'Lucro', 'Margem', 'Rentabilidade']]
            
            for produto in produtos:
                lucro = float(produto['lucro_total'] or 0)
                margem = float(produto['margem_lucro_percentual'] or 0)
                ranking = produto['ranking_rentabilidade']
                
                # Definir cor baseada na rentabilidade
                if ranking <= 3:
                    classificacao = "⭐ ALTA"
                elif ranking <= 6:
                    classificacao = "⚡ MÉDIA"
                else:
                    classificacao = "📊 BAIXA"
                
                data.append([
                    produto['nome'],
                    f"{produto['quantidade_vendida']:.0f} {produto['unidade']}",
                    f"R$ {float(produto['receita_total'] or 0):.2f}",
                    f"R$ {float(produto['custo_total'] or 0):.2f}",
                    f"R$ {lucro:.2f}",
                    f"{margem:.1f}%",
                    classificacao
                ])
            
            table = Table(data, colWidths=[120, 70, 70, 70, 70, 60, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
            ]))
            
            # Aplicar cores para os produtos mais rentáveis
            for i in range(1, len(data)):
                if i <= 4:  # Top 3 + cabeçalho
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#d4edda')),
                        ('TEXTCOLOR', (0, i), (-1, i), colors.HexColor('#155724')),
                        ('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold')
                    ]))
                elif i <= 7:  # Próximos 3
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#fff3cd')),
                        ('TEXTCOLOR', (0, i), (-1, i), colors.HexColor('#856404'))
                    ]))
            
            elements.append(table)
            elements.append(Spacer(1, 20))
            
            # Análise dos produtos mais rentáveis
            if len(produtos) >= 3:
                elements.append(Paragraph("<b>🏆 Produtos Mais Rentáveis do Mês:</b>", styles['Heading3']))
                for i, produto in enumerate(produtos[:3], 1):
                    elements.append(Paragraph(
                        f"{i}º - {produto['nome']}: Lucro de R$ {float(produto['lucro_total'] or 0):.2f} "
                        f"(Margem: {float(produto['margem_lucro_percentual'] or 0):.1f}%)", 
                        styles['Normal']
                    ))
                elements.append(Spacer(1, 10))
        
        else:
            elements.append(Paragraph("<b>Nenhum produto vendido neste mês.</b>", styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # Legenda
        legenda = [
            "⭐ ALTA: Produtos com maior lucro total (Top 3)",
            "⚡ MÉDIA: Produtos com rentabilidade intermediária",
            "📊 BAIXA: Produtos com menor rentabilidade"
        ]
        
        for item in legenda:
            elements.append(Paragraph(item, styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # Rodapé
        footer = Paragraph(
            f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} por {session.get('user_name', 'Sistema')}",
            styles['Italic']
        )
        elements.append(footer)
        
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"relatorio_produtos_vendidos_{datetime.now().strftime('%Y%m')}.pdf",
            mimetype='application/pdf'
        )
        
    except Error as e:
        print(f"Erro ao gerar relatório de produtos vendidos: {e}")
        flash('Erro ao gerar relatório.', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/relatorio/produtos-vendidos-mes/<int:ano>/<int:mes>')
@login_required
def relatorio_produtos_vendidos_mes(ano, mes):
    """Relatório de produtos vendidos em mês específico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Buscar produtos vendidos no mês específico
        query = """
        SELECT 
            p.nome,
            p.unidade,
            p.preco_custo,
            SUM(iv.quantidade) as quantidade_vendida,
            SUM(iv.total_item) as receita_total,
            AVG(iv.preco_unitario) as preco_medio_venda,
            SUM(iv.quantidade * p.preco_custo) as custo_total,
            SUM(iv.total_item - (iv.quantidade * p.preco_custo)) as lucro_total,
            CASE 
                WHEN SUM(iv.quantidade * p.preco_custo) > 0 THEN
                    ROUND((SUM(iv.total_item - (iv.quantidade * p.preco_custo)) / 
                           SUM(iv.quantidade * p.preco_custo)) * 100, 2)
                ELSE 0
            END as margem_lucro_percentual,
            RANK() OVER (ORDER BY SUM(iv.total_item - (iv.quantidade * p.preco_custo)) DESC) as ranking_rentabilidade
        FROM itens_venda iv
        JOIN produtos p ON iv.id_produto = p.id
        JOIN vendas v ON iv.id_venda = v.id
        WHERE v.status = 'concluida'
          AND YEAR(v.data_venda) = %s
          AND MONTH(v.data_venda) = %s
        GROUP BY p.id, p.nome, p.unidade, p.preco_custo
        ORDER BY lucro_total DESC
        """
        
        cursor.execute(query, (ano, mes))
        produtos = cursor.fetchall()
        
        # Calcular totais
        total_receita = sum(float(prod['receita_total'] or 0) for prod in produtos)
        total_lucro = sum(float(prod['lucro_total'] or 0) for prod in produtos)
        total_vendas = sum(float(prod['quantidade_vendida'] or 0) for prod in produtos)
        
        cursor.execute("SELECT * FROM empresa LIMIT 1")
        empresa_data = cursor.fetchone()
        
        # Gerar PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        styles = getSampleStyleSheet()
        style_title = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1
        )
        
        # Título
        from datetime import datetime
        data_ref = datetime(ano, mes, 1)
        mes_nome = data_ref.strftime('%B/%Y').title()
        title = Paragraph(f"Relatório de Produtos Vendidos - {mes_nome}", style_title)
        elements.append(title)
        
        # Informações da empresa
        if empresa_data:
            empresa_info = [
                f"<b>Empresa:</b> {empresa_data['nome']}",
                f"<b>Documento:</b> {empresa_data['documento']}",
                f"<b>Endereço:</b> {empresa_data['endereco']}",
                f"<b>Período:</b> {mes_nome}",
                f"<b>Data de emissão:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            ]
            for info in empresa_info:
                elements.append(Paragraph(info, styles['Normal']))
                elements.append(Spacer(1, 5))
        
        elements.append(Spacer(1, 20))
        
        # Resumo do mês
        resumo_data = [
            ['Total de Receita', f"R$ {total_receita:.2f}"],
            ['Total de Lucro', f"R$ {total_lucro:.2f}"],
            ['Quantidade Total Vendida', f"{total_vendas:.0f} unidades"],
            ['Margem Média', f"{(total_lucro/total_receita*100) if total_receita > 0 else 0:.2f}%"],
            ['Produtos com Vendas', f"{len(produtos)} produtos"]
        ]
        
        resumo_table = Table(resumo_data, colWidths=[200, 150])
        resumo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(resumo_table)
        elements.append(Spacer(1, 20))
        
        # Tabela de produtos
        if produtos:
            # Cabeçalho da tabela
            data = [['Produto', 'Qtd Vendida', 'Receita', 'Custo', 'Lucro', 'Margem', 'Rentabilidade']]
            
            for produto in produtos:
                lucro = float(produto['lucro_total'] or 0)
                margem = float(produto['margem_lucro_percentual'] or 0)
                ranking = produto['ranking_rentabilidade']
                
                # Definir cor baseada na rentabilidade
                if ranking <= 3:
                    classificacao = "⭐ ALTA"
                elif ranking <= 6:
                    classificacao = "⚡ MÉDIA"
                else:
                    classificacao = "📊 BAIXA"
                
                data.append([
                    produto['nome'],
                    f"{produto['quantidade_vendida']:.0f} {produto['unidade']}",
                    f"R$ {float(produto['receita_total'] or 0):.2f}",
                    f"R$ {float(produto['custo_total'] or 0):.2f}",
                    f"R$ {lucro:.2f}",
                    f"{margem:.1f}%",
                    classificacao
                ])
            
            table = Table(data, colWidths=[120, 70, 70, 70, 70, 60, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
            ]))
            
            # Aplicar cores para os produtos mais rentáveis
            for i in range(1, len(data)):
                if i <= 4:  # Top 3 + cabeçalho
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#d4edda')),
                        ('TEXTCOLOR', (0, i), (-1, i), colors.HexColor('#155724')),
                        ('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold')
                    ]))
                elif i <= 7:  # Próximos 3
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#fff3cd')),
                        ('TEXTCOLOR', (0, i), (-1, i), colors.HexColor('#856404'))
                    ]))
            
            elements.append(table)
            elements.append(Spacer(1, 20))
            
            # Análise dos produtos mais rentáveis
            if len(produtos) >= 3:
                elements.append(Paragraph("<b>🏆 Produtos Mais Rentáveis do Mês:</b>", styles['Heading3']))
                for i, produto in enumerate(produtos[:3], 1):
                    elements.append(Paragraph(
                        f"{i}º - {produto['nome']}: Lucro de R$ {float(produto['lucro_total'] or 0):.2f} "
                        f"(Margem: {float(produto['margem_lucro_percentual'] or 0):.1f}%)", 
                        styles['Normal']
                    ))
                elements.append(Spacer(1, 10))
        
        else:
            elements.append(Paragraph(f"<b>Nenhum produto vendido em {mes_nome}.</b>", styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # Legenda
        legenda = [
            "⭐ ALTA: Produtos com maior lucro total (Top 3)",
            "⚡ MÉDIA: Produtos com rentabilidade intermediária",
            "📊 BAIXA: Produtos com menor rentabilidade"
        ]
        
        for item in legenda:
            elements.append(Paragraph(item, styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # Rodapé
        footer = Paragraph(
            f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} por {session.get('user_name', 'Sistema')}",
            styles['Italic']
        )
        elements.append(footer)
        
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"relatorio_produtos_vendidos_{ano:04d}{mes:02d}.pdf",
            mimetype='application/pdf'
        )
        
    except Error as e:
        print(f"Erro ao gerar relatório de produtos vendidos: {e}")
        flash('Erro ao gerar relatório.', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/meses-com-vendas')
@login_required
def api_meses_com_vendas():
    """API para obter meses que possuem vendas"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT 
            YEAR(v.data_venda) as ano,
            MONTH(v.data_venda) as mes,
            DATE_FORMAT(v.data_venda, '%Y-%m') as mes_ano,
            DATE_FORMAT(v.data_venda, '%m/%Y') as mes_formatado,
            COUNT(*) as total_vendas,
            SUM(v.valor_total) as valor_total
        FROM vendas v
        WHERE v.status = 'concluida'
        GROUP BY YEAR(v.data_venda), MONTH(v.data_venda), DATE_FORMAT(v.data_venda, '%Y-%m'), DATE_FORMAT(v.data_venda, '%m/%Y')
        ORDER BY ano DESC, mes DESC
        LIMIT 12
        """
        
        cursor.execute(query)
        meses = cursor.fetchall()
        
        # Formatar os dados
        for mes in meses:
            mes['valor_total'] = float(mes['valor_total'] or 0)
            mes['total_vendas'] = int(mes['total_vendas'] or 0)
        
        return jsonify({
            'success': True,
            'meses': meses
        })
        
    except Error as e:
        print(f"Erro ao buscar meses com vendas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# API para dados do dashboard
@app.route('/api/dashboard/data')
@login_required
def api_dashboard_data():
    """Endpoint API para dados do dashboard"""
    try:
        weather_data = get_weather_data('Santos,BR')
        sales_analysis = analyze_sales_data()
        low_stock_alerts = get_low_stock_alerts()
        monthly_sales = get_monthly_sales()
        total_inventory = get_total_inventory()
        
        return jsonify({
            'weather': weather_data,
            'sales_analysis': sales_analysis,
            'low_stock_alerts': low_stock_alerts,
            'monthly_sales': monthly_sales,
            'total_inventory': total_inventory
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API para produtos
@app.route('/api/produtos')
@login_required
def api_produtos():
    """API para buscar produtos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, nome, preco_venda, quantidade, unidade
            FROM produtos 
            WHERE ativo = TRUE AND quantidade > 0 
            ORDER BY nome
        """)
        produtos = cursor.fetchall()
        return jsonify(produtos)
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# API para estoque total
@app.route('/api/estoque/total')
@login_required
def api_estoque_total():
    """API para valor total do estoque"""
    try:
        total = get_total_inventory()
        return jsonify({'total_inventory': total})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Health check
@app.route('/health')
def health_check():
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected'}), 500
        
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Error as e:
        return jsonify({'status': 'unhealthy', 'database': 'error', 'error': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# API para estatísticas do dashboard
@app.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    """API para estatísticas do dashboard"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE ativo = TRUE")
        total_produtos = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM clientes WHERE ativo = TRUE")
        total_clientes = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM fornecedores WHERE ativo = TRUE")
        total_fornecedores = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM orcamentos WHERE status = 'pendente'")
        total_orcamentos = cursor.fetchone()['total']
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'total_produtos': total_produtos,
            'total_clientes': total_clientes,
            'total_fornecedores': total_fornecedores,
            'total_orcamentos': total_orcamentos
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API para dados meteorológicos
@app.route('/api/weather/<city_key>')
@login_required
def api_weather_city(city_key):
    """API para dados meteorológicos de cidade específica"""
    try:
        weather_data = get_weather_data(city_key)
        return jsonify(weather_data)
    except Exception as e:
        print(f"Erro na API de clima: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cidades')
@login_required
def api_cidades():
    """API para lista de cidades da Baixada Santista"""
    try:
        cidades = get_cidades_baixada_santista()
        return jsonify(cidades)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API para alertas de estoque
@app.route('/api/stock/alerts')
@login_required
def api_stock_alerts():
    """API para alertas de estoque - CORRIGIDA"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Query CORRIGIDA: Consolida por produto
        query = """
            SELECT 
                nome,
                SUM(quantidade) as quantidade,
                MAX(estoque_minimo) as estoque_minimo,
                unidade
            FROM produtos 
            WHERE ativo = TRUE 
            GROUP BY nome, unidade
            HAVING quantidade = 0 OR quantidade <= estoque_minimo
            ORDER BY quantidade ASC
        """
        
        cursor.execute(query)
        produtos = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'alerts': produtos,
            'total': len(produtos)
        })
        
    except Error as e:
        print(f"Erro ao buscar alertas de estoque: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao buscar alertas de estoque'
        }), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# Debug routes
@app.route('/debug/db-test')
def debug_db_test():
    """Testar conexão e estrutura do banco"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Testar estrutura da tabela
        cursor.execute("DESCRIBE orcamentos")
        estrutura = cursor.fetchall()
        
        # Testar dados atuais
        cursor.execute("SELECT id, status FROM orcamentos")
        dados = cursor.fetchall()
        
        return jsonify({
            'estrutura': estrutura,
            'dados': dados,
            'status_coluna': [col for col in estrutura if col['Field'] == 'status']
        })
        
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Criar diretórios necessários
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/img', exist_ok=True)
    
    print("🚀 Iniciando ERP IoT ML...")
    print("📊 Sistema disponível em: http://localhost:5000")
    print("👤 Login: admin / admin123")
    print("🔒 Sistema de segurança ativado")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
