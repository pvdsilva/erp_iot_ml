import requests
import time
from datetime import datetime, timedelta

# Cidades da Baixada Santista
CIDADES_BAIXADA_SANTISTA = {
    'santos': {'nome': 'Santos', 'api_param': 'Santos,BR'},
    'sao_vicente': {'nome': 'São Vicente', 'api_param': 'São Vicente,BR'},
    'guaruja': {'nome': 'Guarujá', 'api_param': 'Guarujá,BR'},
    'cubatao': {'nome': 'Cubatão', 'api_param': 'Cubatão,BR'},
    'praia_grande': {'nome': 'Praia Grande', 'api_param': 'Praia Grande,BR'},
    'mongagua': {'nome': 'Mongaguá', 'api_param': 'Mongaguá,BR'},
    'itanhaem': {'nome': 'Itanhaém', 'api_param': 'Itanhaém,BR'},
    'bertioga': {'nome': 'Bertioga', 'api_param': 'Bertioga,BR'},
    'peruibe': {'nome': 'Peruíbe', 'api_param': 'Peruíbe,BR'}
}

# Configurações
API_TIMEOUT = 15  # segundos
MAX_RETRIES = 2   # número de tentativas
CACHE_DURATION = 600  # 10 minutos

# Cache em memória
weather_cache = {}

def get_cidades_baixada_santista():
    """Retorna a lista de cidades para o combobox"""
    return CIDADES_BAIXADA_SANTISTA

def get_weather_data(city_key="santos"):
    """
    Obtém dados meteorológicos para uma cidade específica com sistema de retry
    city_key: chave da cidade no dicionário CIDADES_BAIXADA_SANTISTA
    """
    # Verificar cache primeiro
    current_time = time.time()
    cache_key = f"weather_{city_key}"
    
    if cache_key in weather_cache:
        cache_data, cache_timestamp = weather_cache[cache_key]
        if current_time - cache_timestamp < CACHE_DURATION:
            print(f"📦 Retornando dados do cache para {city_key}")
            return cache_data
    
    api_key = "gerar usuário e obter key da api meteorologica no OpenWeatherMap e inserir entre as aspas simples"
    base_url = "http://api.openweathermap.org/data/2.5/forecast"
    
    # Obter parâmetro da cidade selecionada
    cidade_info = CIDADES_BAIXADA_SANTISTA.get(city_key, CIDADES_BAIXADA_SANTISTA['santos'])
    city_param = cidade_info['api_param']
    city_name = cidade_info['nome']
    
    # Sistema de retry
    for attempt in range(MAX_RETRIES):
        try:
            print(f"🌤️ Buscando dados da API para {city_name} (tentativa {attempt + 1})...")
            
            # Tentar buscar dados da API
            params = {
                'q': city_param,
                'appid': api_key,
                'units': 'metric',
                'lang': 'pt_br'
            }
            
            response = requests.get(base_url, params=params, timeout=API_TIMEOUT)
            
            # Verificar se a resposta foi bem sucedida
            if response.status_code == 200:
                data = response.json()
                
                # Validar estrutura básica dos dados
                if validate_weather_data(data):
                    weather_data = process_weather_data(data, city_name)
                    weather_data['city_key'] = city_key
                    weather_data['source'] = 'api'
                    
                    # Salvar no cache
                    weather_cache[cache_key] = (weather_data, current_time)
                    print(f"✅ Dados obtidos da API para {city_name}")
                    
                    return weather_data
                else:
                    print(f"❌ Dados inválidos da API para {city_name}")
            
            else:
                print(f"❌ Erro HTTP {response.status_code} para {city_name}")
                
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout na requisição para {city_name} (tentativa {attempt + 1})")
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)  # Pequena pausa entre tentativas
                continue
                
        except requests.exceptions.ConnectionError:
            print(f"🔌 Erro de conexão para {city_name} (tentativa {attempt + 1})")
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
                continue
                
        except Exception as e:
            print(f"❌ Erro inesperado para {city_name} (tentativa {attempt + 1}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
                continue
    
    # Se todas as tentativas falharam, usar fallback
    print(f"🚨 Todas as tentativas falharam para {city_name}, usando fallback")
    return get_fallback_weather_data(city_name, city_key)

def validate_weather_data(data):
    """Valida a estrutura básica dos dados da API"""
    try:
        if not data or 'list' not in data or 'city' not in data:
            return False
        
        if not data['list'] or len(data['list']) == 0:
            return False
        
        # Verificar primeiro item tem estrutura esperada
        first_item = data['list'][0]
        if 'main' not in first_item or 'weather' not in first_item:
            return False
        
        if 'temp' not in first_item['main'] or not first_item['weather']:
            return False
            
        return True
    except:
        return False

def process_weather_data(data, city_name):
    """Processa os dados da API OpenWeather com datas dinâmicas para 7 dias"""
    try:
        # Usar o primeiro registro como dados atuais
        current = data['list'][0]
        
        current_weather = {
            'city': city_name,
            'country': data['city']['country'],
            'current_temp': round(current['main']['temp']),
            'current_description': current['weather'][0]['description'].title(),
            'current_icon': current['weather'][0]['icon'],
            'humidity': current['main']['humidity'],
            'wind_speed': round(current['wind']['speed'], 1),
            'forecast': []
        }
        
        # Obter data atual para referência
        today = datetime.now().date()
        
        # Agrupar previsões por dia começando de HOJE
        daily_forecasts = {}
        
        for forecast in data['list']:
            try:
                forecast_date = datetime.fromtimestamp(forecast['dt']).date()
                
                # Pular dias passados e considerar apenas a partir de hoje
                if forecast_date < today:
                    continue
                    
                if forecast_date not in daily_forecasts:
                    daily_forecasts[forecast_date] = {
                        'date': forecast_date,
                        'day': get_day_name_from_date(forecast_date),
                        'temp_min': round(forecast['main']['temp_min']),
                        'temp_max': round(forecast['main']['temp_max']),
                        'description': forecast['weather'][0]['description'].title(),
                        'icon': forecast['weather'][0]['icon'],
                        'recommendation': get_weather_recommendation(forecast['weather'][0]['main'])
                    }
                else:
                    # Atualizar min/max
                    daily_forecasts[forecast_date]['temp_min'] = min(
                        daily_forecasts[forecast_date]['temp_min'], 
                        round(forecast['main']['temp_min'])
                    )
                    daily_forecasts[forecast_date]['temp_max'] = max(
                        daily_forecasts[forecast_date]['temp_max'], 
                        round(forecast['main']['temp_max'])
                    )
            except (KeyError, IndexError) as e:
                print(f"⚠️ Erro ao processar previsão: {e}")
                continue
        
        # Converter para lista ordenada por data e pegar 7 dias (hoje + 6)
        forecast_list = []
        for i in range(7):  # Hoje + 6 dias seguintes = 7 dias
            target_date = today + timedelta(days=i)
            
            if target_date in daily_forecasts:
                forecast_data = daily_forecasts[target_date]
                forecast_data['date'] = format_date_from_date(target_date)
                forecast_list.append(forecast_data)
            else:
                # Se não encontrou dados para este dia, criar entrada com dados básicos
                forecast_list.append(create_fallback_forecast(target_date, i))

        current_weather['forecast'] = forecast_list
        return current_weather
        
    except Exception as e:
        print(f"❌ Erro ao processar dados para {city_name}: {e}")
        return get_fallback_weather_data(city_name, "santos")

def create_fallback_forecast(target_date, day_index):
    """Cria uma previsão de fallback para um dia específico"""
    # Baseado na estação do ano (simplificado)
    month = target_date.month
    if month in [12, 1, 2]:  # Verão
        base_temp = 25
    elif month in [3, 4, 5]:  # Outono
        base_temp = 22
    elif month in [6, 7, 8]:  # Inverno
        base_temp = 18
    else:  # Primavera
        base_temp = 23
    
    conditions = [
        ('Ensolarado', '01d', 'Bom para serviços externos'),
        ('Parcialmente nublado', '02d', 'Bom para serviços'),
        ('Nublado', '03d', 'Cuidado com serviços externos'),
        ('Chuva leve', '10d', 'Evitar serviços externos'),
        ('Tempestade', '11d', 'Não recomendado para serviços externos'),
        ('Nevoeiro', '50d', 'Cuidado com serviços externos'),
        ('Chuva moderada', '10d', 'Evitar serviços externos')
    ]
    
    condition = conditions[day_index % len(conditions)]
    
    return {
        'date': format_date_from_date(target_date),
        'day': get_day_name_from_date(target_date),
        'temp_min': base_temp - 3 + (day_index % 2),
        'temp_max': base_temp + 3 + (day_index % 3),
        'description': condition[0],
        'icon': condition[1],
        'recommendation': condition[2]
    }

def get_day_name_from_date(date_obj):
    """Converte objeto date para nome do dia em português"""
    days_ptbr = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    return days_ptbr[date_obj.weekday()]

def format_date_from_date(date_obj):
    """Formata objeto date para DD/MM"""
    return date_obj.strftime('%d/%m')

def get_weather_recommendation(weather_condition):
    """Gera recomendação baseada na condição climática"""
    recommendations = {
        'Clear': 'Bom para serviços externos',
        'Clouds': 'Bom para a maioria dos serviços', 
        'Rain': 'Evitar serviços externos',
        'Drizzle': 'Cuidado com serviços externos',
        'Thunderstorm': 'Não recomendado para serviços',
        'Snow': 'Não recomendado para serviços',
        'Mist': 'Cuidado com serviços externos',
        'Smoke': 'Cuidado com serviços externos',
        'Haze': 'Cuidado com serviços externos',
        'Dust': 'Cuidado com serviços externos',
        'Fog': 'Cuidado com serviços externos',
        'Sand': 'Cuidado com serviços externos',
        'Ash': 'Cuidado com serviços externos',
        'Squall': 'Não recomendado para serviços',
        'Tornado': 'Não recomendado para serviços'
    }
    
    return recommendations.get(weather_condition, 'Condições normais para serviços')

def get_fallback_weather_data(city_name="Santos", city_key="santos"):
    """Dados de fallback quando a API não está disponível - 7 DIAS"""
    print(f"🔄 Usando dados de fallback para {city_name}")
    
    base_date = datetime.now().date()
    forecast = []
    
    for i in range(7):  # 7 dias: hoje + 6
        target_date = base_date + timedelta(days=i)
        forecast.append(create_fallback_forecast(target_date, i))
    
    return {
        'city': city_name,
        'city_key': city_key,
        'country': 'BR',
        'current_temp': 22,
        'current_description': 'Parcialmente nublado',
        'current_icon': '02d',
        'humidity': 65,
        'wind_speed': 3.5,
        'forecast': forecast,
        'source': 'fallback'
    }

def clear_weather_cache():
    """Limpa o cache de dados meteorológicos"""
    global weather_cache
    weather_cache = {}
    print("🗑️ Cache de dados meteorológicos limpo")

def get_cache_info():
    """Retorna informações sobre o cache"""
    current_time = time.time()
    active_entries = 0
    expired_entries = 0
    
    for cache_key, (data, timestamp) in weather_cache.items():
        if current_time - timestamp < CACHE_DURATION:
            active_entries += 1
        else:
            expired_entries += 1
    
    return {
        'total_entries': len(weather_cache),
        'active_entries': active_entries,
        'expired_entries': expired_entries,
        'cache_duration_minutes': CACHE_DURATION / 60
    }

# Teste completo da função
def test_all_cities():
    """Testa todas as cidades para verificar funcionamento"""
    print("\n" + "="*60)
    print("🧪 TESTE COMPLETO DO MÓDULO WEATHER")
    print("="*60)
    
    results = {
        'success': 0,
        'fallback': 0,
        'error': 0
    }
    
    for city_key, city_info in CIDADES_BAIXADA_SANTISTA.items():
        print(f"\n📍 Testando {city_info['nome']}...")
        try:
            start_time = time.time()
            data = get_weather_data(city_key)
            end_time = time.time()
            
            response_time = round(end_time - start_time, 2)
            
            print(f"   ✅ Temperatura: {data['current_temp']}°C")
            print(f"   ✅ Condição: {data['current_description']}")
            print(f"   ✅ Fonte: {data['source']}")
            print(f"   ✅ Previsão: {len(data['forecast'])} dias")
            print(f"   ⏱️  Tempo resposta: {response_time}s")
            
            if data['source'] == 'api':
                results['success'] += 1
            else:
                results['fallback'] += 1
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            results['error'] += 1
    
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES:")
    print(f"   ✅ Sucesso (API): {results['success']}/{len(CIDADES_BAIXADA_SANTISTA)}")
    print(f"   🔄 Fallback: {results['fallback']}/{len(CIDADES_BAIXADA_SANTISTA)}")
    print(f"   ❌ Erros: {results['error']}/{len(CIDADES_BAIXADA_SANTISTA)}")
    print("="*60)
    
    return results

def test_single_city(city_key="santos"):
    """Testa uma cidade específica com detalhes"""
    print(f"\n🔍 TESTE DETALHADO: {city_key.upper()}")
    print("-" * 40)
    
    try:
        data = get_weather_data(city_key)
        
        print(f"🏙️  Cidade: {data['city']}")
        print(f"🌡️  Temperatura: {data['current_temp']}°C")
        print(f"📝 Condição: {data['current_description']}")
        print(f"💧 Umidade: {data['humidity']}%")
        print(f"💨 Vento: {data['wind_speed']} m/s")
        print(f"🔧 Fonte: {data['source']}")
        
        print("\n📅 PREVISÃO 7 DIAS:")
        print("-" * 40)
        for i, day in enumerate(data['forecast']):
            print(f"   {day['day']} {day['date']}: {day['temp_min']}°/{day['temp_max']}°")
            print(f"      {day['description']} - {day['recommendation']}")
            if i < 6:  # Não imprimir linha após o último
                print("   " + "-" * 30)
                
    except Exception as e:
        print(f"❌ Erro no teste: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando testes do módulo weather...")
    
    # Teste individual
    test_single_city("santos")
    
    # Teste completo de todas as cidades
    test_all_cities()
    
    # Informações do cache
    cache_info = get_cache_info()
    print(f"\n💾 INFO CACHE:")
    print(f"   Entradas totais: {cache_info['total_entries']}")
    print(f"   Entradas ativas: {cache_info['active_entries']}")
    print(f"   Duração cache: {cache_info['cache_duration_minutes']} minutos")
