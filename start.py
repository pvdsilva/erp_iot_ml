#!/usr/bin/env python3
# start.py - Script alternativo para iniciar a aplicação

import os
import sys
import webbrowser
from threading import Timer

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

def open_browser():
    """Abre o navegador automaticamente"""
    webbrowser.open_new('http://localhost:5000/')

if __name__ == '__main__':
    print("🚀 Iniciando ERP IoT ML...")
    print("📊 Sistema disponível em: http://localhost:5000")
    print("👤 Login: admin / admin123")
    print("🔧 Modo: Desenvolvimento")
    print("-" * 50)
    
    # Abrir navegador após 2 segundos
    Timer(2, open_browser).start()
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 Servidor parado pelo usuário")
    except Exception as e:
        print(f"❌ Erro: {e}")
