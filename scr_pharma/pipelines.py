import os
import csv
from sqlalchemy import create_engine, Table, Column, Integer, String, DECIMAL, DateTime, MetaData, Index
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from scrapy.utils.project import get_project_settings
from .credentials import SQLALCHEMY_DATABASE_URI

class ScrPharmaPipeline:
    def __init__(self):
        settings = get_project_settings()
        self.enable_database_insertion = settings.getbool('ENABLE_DATABASE_INSERTION', True)

        if self.enable_database_insertion:
            self.engine = create_engine(SQLALCHEMY_DATABASE_URI)
            self.Session = sessionmaker(bind=self.engine)
            metadata = MetaData()
            self.pharma_table = Table('scr_pharma', metadata,
                Column('id', Integer, primary_key=True, autoincrement=True),
                Column('name', String(255), nullable=False),
                Column('url', String(255), nullable=False),
                Column('category', String(255), nullable=False),
                Column('price', DECIMAL(10, 2), nullable=True),
                Column('price_sale', DECIMAL(10, 2), nullable=True),
                Column('brand', String(255), nullable=False),
                Column('timestamp', DateTime, nullable=False),
                Column('spider_name', String(255), nullable=False),
                Column('code', String(255), nullable=True),
                Column('price_benef', DECIMAL(10, 2), nullable=True),
                # Definición del índice según el esquema db.sql
                Index('url_index', 'url')
            )
            metadata.create_all(self.engine)

        # Estructura para almacenar ítems en memoria para todos los spiders
        self.memory_storage = {}

    def process_item(self, item, spider):
        # Almacena todos los ítems en memoria, agrupados por URL
        url = item.get('url')
        if url:
            if url not in self.memory_storage:
                self.memory_storage[url] = {
                    'name': item.get('name'),
                    'url': url,
                    'category': set(),  # Usamos un set para evitar duplicados
                    'price': self.convert_to_decimal(item.get('price')),
                    'price_sale': self.convert_to_decimal(item.get('price_sale')),
                    'price_benef': self.convert_to_decimal(item.get('price_benef')),
                    'code': item.get('code'),
                    'brand': item.get('brand'),
                    'timestamp': item.get('timestamp'),
                    'spider_name': item.get('spider_name')
                }
            # Agrega la categoría al set de categorías
            category = item.get('category')
            if category:
                self.memory_storage[url]['category'].add(category)
        else:
            spider.logger.warning(f"Ítem sin URL: {item}")

        return item

    def close_spider(self, spider):
        # Procesa los ítems almacenados en memoria
        processed_items = self.process_memory_storage()
        # Escribe los ítems procesados en CSV y/o en la base de datos
        for item in processed_items:
            self.write_to_csv(item, spider.name)
            if self.enable_database_insertion:
                self.insert_into_database(item)

    def process_memory_storage(self):
        processed_items = []
        for url, data in self.memory_storage.items():
            # Convierte el set de categorías a una lista ordenada y luego a una cadena separada por ' > '
            categories = ' > '.join(sorted(data['category']))
            processed_item = {
                'name': data['name'],
                'url': data['url'],
                'category': categories,
                'price': data['price'],
                'price_sale': data['price_sale'],
                'price_benef': data['price_benef'],
                'code': data['code'],
                'brand': data['brand'],
                'timestamp': data['timestamp'],
                'spider_name': data['spider_name']
            }
            processed_items.append(processed_item)
        return processed_items

    def convert_to_decimal(self, value):
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def write_to_csv(self, item, spider_name):
        # Asegura que el directorio 'datafolder' exista
        os.makedirs('datafolder', exist_ok=True)
        file_path = f'datafolder/{spider_name}_{datetime.now().strftime("%Y_%m_%d")}.csv'
        file_exists = os.path.isfile(file_path)
        with open(file_path, 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=item.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(item)

    def insert_into_database(self, item):
        if not self.enable_database_insertion:
            return
        session = self.Session()
        try:
            # Prepara los datos para la inserción
            insert_data = {
                'name': item['name'],
                'url': item['url'],
                'category': item['category'],
                'price': item['price'],
                'price_sale': item['price_sale'],
                'price_benef': item['price_benef'],
                'code': item['code'],
                'brand': item['brand'],
                'timestamp': item['timestamp'],
                'spider_name': item['spider_name']
            }
            insert_stmt = self.pharma_table.insert().values(**insert_data)
            session.execute(insert_stmt)
            session.commit()
        except Exception as e:
            print(f"Database error: {str(e)}")
            session.rollback()
        finally:
            session.close()
