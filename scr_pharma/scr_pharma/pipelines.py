# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class ScrPharmaPipeline:
    def process_item(self, item, spider):
        return item

class CruzVerdePipeline:
    def process_item(self, item, spider):
        # Convertir precios a float
        item['precio'] = float(item['precio'].replace('$', '').replace('.', '').replace(',', '.'))
        return item