#!/usr/bin/env python3
import os
import sys
from app import app

def check_dependencies():
    """Verifica se todas as dependências estão instaladas"""
    try:
        import flask
        import mysql.connector
        import requests
        import pandas
        import sklearn
        import reportlab
        print("✅ Todas as dependências estão instaladas")
        return True
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("📦 Instale as dependências com: pip install -r requirements.txt")
        return False

def check_database_connection():
    """Verifica a conexão com o banco de dados"""
    try:
        from app import get_db_connection
        conn = get_db_connection()
        if conn:
            print("✅ Conexão com o banco de dados estabelecida")
            conn.close()
            return True
        else:
            print("❌ Falha na conexão com o banco de dados")
            return False
    except Exception as e:
        print(f"❌ Erro na conexão com o banco: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Iniciando ERP IoT ML - Sistema de Gestão")
    print("=" * 50)
    
    # Verificar dependências
    if not check_dependencies():
        sys.exit(1)
    
    # Verificar banco de dados
    if not check_database_connection():
        print("⚠️  Continuando sem conexão com o banco...")
    
    # Iniciar aplicação
    print("\n📊 Sistema ERP IoT ML inicializando...")
    print("🌐 Disponível em: http://localhost:5000")
    print("👤 Login padrão: admin / admin123")
    print("⏹️  Para parar o servidor, pressione Ctrl+C")
    print("=" * 50)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Servidor parado pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")

if __name__ == '__main__':
    main()
