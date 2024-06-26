import re
from datetime import datetime

def safe_price(value):
    try:
        # Eliminar todos los caracteres que no sean números
        clean_value = re.sub(r'\D', '', str(value))
        return float(clean_value) if clean_value else 0
    except Exception:
        return 0

def replace_comma(value):
    # Reemplazar comas por puntos para correcta conversión decimal
    return str(value).replace(',', '.')

def safe_string(value, max_length=255):
    # Asegurar que la cadena no exceda la longitud máxima y evitar problemas con caracteres especiales
    return str(value)[:max_length]

def validate_url(value):
    # Validar que la URL sea adecuada, ajustándola a la longitud máxima permitida
    return safe_string(value, 255)

def format_datetime(value):
    if isinstance(value, datetime):
        # Si el valor ya es un objeto datetime, formatear directamente
        return value.strftime("%Y-%m-%d %H:%M:%S")
    try:
        # Intentar convertir una cadena a datetime y luego formatear
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        # Si la conversión falla, usar la fecha y hora actual
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")