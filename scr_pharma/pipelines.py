from sqlalchemy import create_engine, Table, Column, Integer, String, Float, MetaData, DateTime
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from scrapy.utils.project import get_project_settings
import csv
from .credentials import SQLALCHEMY_DATABASE_URI

class ScrPharmaPipeline:
    def __init__(self):
        settings = get_project_settings()
        self.enable_database_insertion = settings.getbool('ENABLE_DATABASE_INSERTION', True)
        self.engine = create_engine(SQLALCHEMY_DATABASE_URI)
        self.Session = sessionmaker(bind=self.engine)
        metadata = MetaData()
        self.pharma_table = Table('scr_pharma', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('name', String),
            Column('url', String, unique=True),
            Column('category', String),
            Column('price', Float),
            Column('price_sale', Float),
            Column('brand', String),
            Column('timestamp', DateTime),
            Column('spider_name', String),
            autoload_with=self.engine)
        metadata.create_all(self.engine)
        self.items_to_process = []
        self.products_seen = {}  # Diccionario para gestionar URLs vistas

    def process_item(self, item, spider):
        if spider.name == "cruzverde":
            url = item['url']
            if url in self.products_seen:
                # Concatenar las categorías si el URL ya ha sido visto
                self.products_seen[url]['category'] += ' | ' + item['category']
            else:
                self.products_seen[url] = item
            return item
        else:
            # Procesamiento inmediato para otros spiders
            self.write_to_csv(item, spider.name)
            self.insert_into_database(item)
            return item

    def close_spider(self, spider):
        if spider.name == "cruzverde":
            # Procesamiento de lotes al final del spider
            file_path = f'datafolder/{spider.name}_{datetime.now().strftime("%Y_%m_%d")}.csv'
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['name', 'url', 'category', 'price', 'price_sale', 'brand', 'timestamp', 'spider_name'])
                for item in self.products_seen.values():
                    writer.writerow([item['name'], item['url'], item['category'], 
                                     item['price'], item['price_sale'], item['brand'], 
                                     item['timestamp'], item['spider_name']])
            self.insert_into_database()

    def write_to_csv(self, item, spider_name):
        # Escribir inmediatamente al CSV para spiders que no son 'cruzverde'
        with open(f'datafolder/{spider_name}_{datetime.now().strftime("%Y_%m_%d")}.csv', 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([item.get('name'), item.get('url'), item.get('category'), 
                             item.get('price'), item.get('price_sale'), item.get('brand'), 
                             item.get('timestamp', datetime.now()), item.get('spider_name')])

    def insert_into_database(self, item=None):
        if not self.enable_database_insertion:
            return
        session = self.Session()
        try:
            if item:
                # Insertar un solo ítem directamente en la base de datos
                insert_stmt = self.pharma_table.insert().values(
                    name=item.get('name'),
                    url=item.get('url'),
                    category=item.get('category'),
                    price=item.get('price'),
                    price_sale=item.get('price_sale'),
                    brand=item.get('brand'),
                    timestamp=item.get('timestamp', datetime.now()),
                    spider_name=item.get('spider_name')
                )
                session.execute(insert_stmt)
            else:
                # Insertar por lotes para el spider 'cruzverde' al final
                for item in self.products_seen.values():
                    insert_stmt = self.pharma_table.insert().values(
                        name=item['name'], url=item['url'], category=item['category'],
                        price=item['price'], price_sale=item['price_sale'], brand=item['brand'],
                        timestamp=item['timestamp'], spider_name=item['spider_name']
                    )
                    session.execute(insert_stmt)
            session.commit()
        except Exception as e:
            print(f"Database error: {str(e)}")
        finally:
            session.close()
