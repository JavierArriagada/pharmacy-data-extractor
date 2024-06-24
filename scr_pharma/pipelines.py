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
                Column('price_benef', Float),
                Column('code', String),
                Column('brand', String),
                Column('timestamp', DateTime),
                Column('spider_name', String),
                autoload_with=self.engine)
            metadata.create_all(self.engine)

    def process_item(self, item, spider):
        self.write_to_csv(item, spider.name)
        if self.enable_database_insertion:
            self.insert_into_database(item)
        return item

    def close_spider(self, spider):
        # No se necesita ninguna acción especial aquí, ya que todo se procesa ítem por ítem
        pass

    def write_to_csv(self, item, spider_name):
        file_path = f'datafolder/{spider_name}_{datetime.now().strftime("%Y_%m_%d")}.csv'
        file_exists = os.path.isfile(file_path)
        with open(file_path, 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=item.fields.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(item)

    def insert_into_database(self, item):
        if not self.enable_database_insertion:
            return
        session = self.Session()
        try:
            insert_stmt = self.pharma_table.insert().values({field: item.get(field) for field in item.fields.keys()})
            session.execute(insert_stmt)
            session.commit()
        except Exception as e:
            print(f"Database error: {str(e)}")
            session.rollback()
        finally:
            session.close()