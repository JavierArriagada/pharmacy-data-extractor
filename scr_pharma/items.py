from scrapy import Item, Field
from itemloaders.processors import TakeFirst, MapCompose

def safe_price(value):
    try:
        # Convertir a cadena y limpiar, asegurando que se manejen casos donde el valor pueda estar vacío o mal formado
        return str(value).replace('$', '').replace(',', '').strip() if value else '0'
    except Exception as e:
        return '0'  # Retorna un valor predeterminado si algo sale mal

class ScrPharmaItem(Item):
    name = Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    url = Field(
        output_processor=TakeFirst()
    )
    category = Field(
        output_processor=TakeFirst()
    )
    price = Field(
        input_processor=MapCompose(safe_price),
        output_processor=TakeFirst()
    )
    price_sale = Field(
        input_processor=MapCompose(safe_price),
        output_processor=TakeFirst()
    )
    brand = Field(
        output_processor=TakeFirst()
    )
    timestamp = Field() 
    spider_name = Field(
        output_processor=TakeFirst()
    )
