from scrapy import Item, Field
from itemloaders.processors import TakeFirst, MapCompose
from .helpers import *



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
        input_processor=MapCompose(safe_price),
        output_processor=TakeFirst()
    )
    price_sale = Field(
        input_processor=MapCompose(safe_price),
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
        input_processor=MapCompose(safe_price),
        output_processor=TakeFirst()
    )
