import os
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
        
        self.items_to_process = []
        self.products_seen = {}  # Diccionario para gestionar URLs vistas
        
        if self.enable_database_insertion:
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
                Column('price_benef', Float),  # New field
                Column('code', String),  # New field
                Column('brand', String),
                Column('timestamp', DateTime),
                Column('spider_name', String),
                autoload_with=self.engine)
            metadata.create_all(self.engine)

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
            if self.enable_database_insertion:
                self.insert_into_database(item)
            return item

    def close_spider(self, spider):
        if spider.name == "cruzverde":
            # Procesamiento de lotes al final del spider
            file_path = f'datafolder/{spider.name}_{datetime.now().strftime("%Y_%m_%d")}.csv'
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=next(iter(self.products_seen.values())).keys())
                writer.writeheader()  # Write column names as the first row
                for item in self.products_seen.values():
                    writer.writerow(item)
            if self.enable_database_insertion:
                self.insert_into_database()

    def write_to_csv(self, item, spider_name):
        file_path = f'datafolder/{spider_name}_{datetime.now().strftime("%Y_%m_%d")}.csv'
        # Check if file exists to decide whether to write headers
        file_exists = os.path.isfile(file_path)
        with open(file_path, 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=item.fields.keys())
            if not file_exists:
                writer.writeheader()  # Write header only if the file is new
            writer.writerow(item)

    def insert_into_database(self, item=None):
        if not self.enable_database_insertion:
            return
        session = self.Session()
        try:
            if item:
                # Insertar un solo ítem directamente en la base de datos
                insert_stmt = self.pharma_table.insert().values({field: item.get(field) for field in item.fields.keys()})  # Dynamic fields
                session.execute(insert_stmt)
            else:
                # Insertar por lotes para el spider 'cruzverde' al final
                for item in self.products_seen.values():
                    insert_stmt = self.pharma_table.insert().values({field: item[field] for field in item.fields.keys()})  # Dynamic fields
                    session.execute(insert_stmt)
            session.commit()
        except Exception as e:
            print(f"Database error: {str(e)}")
        finally:
            session.close()