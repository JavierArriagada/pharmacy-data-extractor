from scrapy import Item, Field
from itemloaders.processors import TakeFirst, MapCompose
from datetime import datetime

def safe_price(value):
    try:
        # Eliminar símbolos de moneda y convertir a decimal
        clean_value = str(value).replace('$', '').replace(',', '').replace('.', '').strip()
        return float(clean_value) if clean_value else 0.0
    except Exception:
        return 0.0

def replace_comma(value):
    # Reemplazar comas por puntos para correcta conversión decimal
    return str(value).replace(',', '.')

def to_decimal(value):
    try:
        # Convertir a decimal con dos decimales de precisión
        return "{:.2f}".format(float(value))
    except ValueError:
        return "0.00"

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


class ScrPharmaItem(Item):
    name = Field(
        input_processor=MapCompose(str.strip, replace_comma, lambda x: safe_string(x, 255)),
        output_processor=TakeFirst()
    )
    url = Field(
        input_processor=MapCompose(validate_url),
        output_processor=TakeFirst()
    )
    category = Field(
        input_processor=MapCompose(str.strip, lambda x: safe_string(x, 255)),
        output_processor=TakeFirst()
    )
    price = Field(
        input_processor=MapCompose(safe_price, to_decimal),
        output_processor=TakeFirst()
    )
    price_sale = Field(
        input_processor=MapCompose(safe_price, to_decimal),
        output_processor=TakeFirst()
    )
    brand = Field(
        input_processor=MapCompose(str.strip, lambda x: safe_string(x, 255)),
        output_processor=TakeFirst()
    )
    timestamp = Field(
        input_processor=MapCompose(format_datetime),
        output_processor=TakeFirst()
    )
    spider_name = Field(
        input_processor=MapCompose(str.strip, lambda x: safe_string(x, 255)),
        output_processor=TakeFirst()
    )
    code = Field(
        input_processor=MapCompose(str.strip, lambda x: safe_string(x, 255)),
        output_processor=TakeFirst()
    )
    price_benef = Field(
        input_processor=MapCompose(safe_price, to_decimal),
        output_processor=TakeFirst()
    )
