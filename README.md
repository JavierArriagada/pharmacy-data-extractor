# Documentación del Proyecto de Web Scraping con Scrapy

## Estructura del Proyecto

Un proyecto típico de Scrapy tiene la siguiente estructura:

```
scr_pharma/
    scrapy.cfg
    scr_pharma/
        __init__.py
        credentials.py
        herlpers.py
        items.py
        main.py
        middlewares.py
        pipelines.py
        requirements.txt
        settings.py
        spiders/
            __init__.py
            spiderfarmacia1.py
            spiderfarmacia2.py
            ...
        datafolder/
```

- `scrapy.cfg`: el archivo de configuración del proyecto.
- `items.py`: define los modelos de datos para los items que se extraen.
- `pipelines.py`: define los pipelines donde los items son procesados después de ser extraidos.
- `settings.py`: define la configuración del proyecto.
- `spiders/`: un directorio donde se guardan los spiders.
- `credentials`: archivo con informacion de conexión a MySQL.
- `helpers`: archivo con funciones de postproceso de datos.

## Items y Item Loaders

Los items son modelos de datos que definen los campos que se quieren extraer. Por ejemplo, para extraer los beneficios de las farmacias.

```python
class ScrPharmaItem(scrapy.Item):
    # define the fields for your item here like:
    name = Field()
    url = Field()
    category = Field()
    price = Field()
    price_sale = Field()
    brand = Field()
    timestamp = Field()
    spider_name = Field()
    code = Field()
    price_benef = Field()   
```

Los Item Loaders proporcionan un mecanismo para llenar los items. Un Item Loader toma un item y una respuesta de Scrapy, y los llena con los datos extraidos.

## Pipelines

Los pipelines se utilizan para post-procesar los items una vez que han sido extraidos. En en este caso, el pipeline se usa para insertar los items en una base de datos MySQL `scr_benefit`, ademas de generar los `csv`.

```python
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
```

## Requisitos

- Python 3.
- Chrome debe estar instalado en el sistema.
- Se recomienda usar un entorno virtual para instalar las dependencias del proyecto.

## Configuración de la base de datos
Antes de ejecutar el proyecto, configurar la conexión a la base de datos MySQL local. Para hacerlo, modificar el archivo `credentials.py` en la carpeta raiz del proyecto, con la información de tu base de datos. Aquí  un ejemplo de cómo podría verse el archivo:



```python
#/*==============================================================*/
#/*  credentials.py */
#/*==============================================================*/
USER = 'your_username'
PASSWORD = 'your_password'
IP = 'localhost'
BD_NAME = 'your_database'
```
## Ejecución del Proyecto

Para ejecutar el proyecto, seguir estos pasos:

1. Navegar a la carpeta raíz del proyecto donde se encuentra el archivo `main.py`.
2. Crear y activar un entorno virtual :
    * Opcion 1: Usando venv

        ```powershell
        # PowerShell
        python -m venv env
        .\env\Scripts\activate
        ```
    
        ```bash
        # bash
        python -m venv env
        source env/bin/activate
        ```
        Dependiendo del sistema operativo y de la versión de Python instalada, puede que se deba usar `python3` en lugar de `python` para ejecutar los comandos siguientes.

    * Opcion 2: Usando Anaconda para crear un ambiente virtual con `Python 3.12.3` **Recomendado**

        En una terminal con el ambiente virtual activado, navegar a la carpeta raíz del proyecto donde se encuentra el archivo `main.py`.

3. Con en ambiente virtual ativado, instalar las dependencias del proyecto con el siguiente comando:

    ```bash    
    pip install -r requirements.txt
    ```

4. Realizar los siguientes cambios en la base de datos MySQL:

    ```sql
    CREATE TABLE `scr_pharma` (
        `id` INT UNSIGNED AUTO_INCREMENT,
        `name` VARCHAR(255) NOT NULL,
        `url` VARCHAR(255) NOT NULL,
        `category` VARCHAR(255) NOT NULL,
        `price` DECIMAL(10,2),
        `price_sale` DECIMAL(10,2),
        `brand` VARCHAR(255) NOT NULL,
        `timestamp` DATETIME NOT NULL,
        `spider_name` VARCHAR(255) NOT NULL,
        `code` VARCHAR(255),
        `price_benef` DECIMAL(10,2),
        PRIMARY KEY (`id`),
        UNIQUE KEY `url_unique` (`url`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ```

6. Ejecutar los spider: Finalmente, puede ejecutar los spider con el siguiente comando::

    ```bash
    python main.py
    ```

Esto ejecutará los spiders que se encuentran en la carpeta `spiders\`. Se Puede ver el progreso de la extracción de datos en la terminal. Al finalizar, se generarán archivos CSV en la carpeta `datafolder\` y los datos extraídos se insertarán en la base de datos MySQL `scr_pharma`.
