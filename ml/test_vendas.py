# test_vendas.py - Testar vendas e estoque
import mysql.connector
from mysql.connector import Error

def test_vendas():
    print("🧪 TESTANDO VENDAS E ESTOQUE...")
    
    config = {
        'host': 'localhost',
        'database': 'erp_iot_ml',
        'user': 'root',
        'password': 'gerar usuário e senha no php my admin e inserir a senha aqui entre aspas as apas simples'
    }
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        
        print("✅ Conexão estabelecida com sucesso!")
        
        # Verificar estrutura da tabela vendas
        print("\n📊 ESTRUTURA DA TABELA VENDAS:")
        cursor.execute("DESCRIBE vendas")
        colunas_vendas = cursor.fetchall()
        for coluna in colunas_vendas:
            print(f"   - {coluna['Field']} ({coluna['Type']})")
        
        # Verificar estrutura da tabela itens_venda
        print("\n📋 ESTRUTURA DA TABELA ITENS_VENDA:")
        cursor.execute("DESCRIBE itens_venda")
        colunas_itens = cursor.fetchall()
        for coluna in colunas_itens:
            print(f"   - {coluna['Field']} ({coluna['Type']})")
        
        # Verificar dados atuais
        print("\n📈 DADOS ATUAIS:")
        
        # Vendas
        cursor.execute("SELECT COUNT(*) as total, COALESCE(SUM(valor_total), 0) as total_vendas FROM vendas WHERE status = 'concluida'")
        vendas = cursor.fetchone()
        print(f"💰 Vendas concluídas: {vendas['total']} (Total: R$ {vendas['total_vendas']:.2f})")
        
        # Itens de venda
        cursor.execute("SELECT COUNT(*) as total FROM itens_venda")
        itens = cursor.fetchone()
        print(f"📦 Itens de venda: {itens['total']}")
        
        # Produtos com estoque
        cursor.execute("SELECT nome, quantidade, estoque_minimo FROM produtos WHERE ativo = TRUE LIMIT 5")
        produtos = cursor.fetchall()
        print(f"🎯 Primeiros 5 produtos:")
        for p in produtos:
            print(f"   - {p['nome']}: {p['quantidade']} (mín: {p['estoque_minimo']})")
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    test_vendas()
