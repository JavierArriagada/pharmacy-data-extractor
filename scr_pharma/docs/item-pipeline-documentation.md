# Documentación del ItemLoader y Pipeline

## ItemLoader y Procesamiento de Campos

El `ItemLoader` es una clase proporcionada por Scrapy que facilita la población de items scraped. En nuestro proyecto, utilizamos un `ItemLoader` personalizado definido en `items.py` para procesar los datos extraídos antes de almacenarlos.

### Definición de ScrPharmaItem

```python
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
```

### Funciones de Procesamiento

- `str.strip`: Elimina espacios en blanco al inicio y final de la cadena.
- `replace_comma`: Reemplaza comas por puntos en los valores numéricos.
- `safe_string`: Asegura que la cadena no exceda una longitud máxima y maneja caracteres especiales.
- `validate_url`: Valida y limpia las URLs.
- `safe_price`: Convierte el precio a un formato numérico seguro.
- `format_datetime`: Formatea la fecha y hora al formato deseado.

## Pipeline

El pipeline, definido en `pipelines.py`, es responsable de procesar los items después de que han sido extraídos por el spider. Realiza las siguientes tareas:

1. Escribe los datos en un archivo CSV.
2. Inserta los datos en una base de datos MySQL (si está habilitado).

### Escritura en CSV

```python
def write_to_csv(self, item, spider_name):
    file_path = f'datafolder/{spider_name}_{datetime.now().strftime("%Y_%m_%d")}.csv'
    file_exists = os.path.isfile(file_path)
    with open(file_path, 'a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=item.fields.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(item)
```

### Inserción en Base de Datos

```python
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

El pipeline maneja tanto la escritura en CSV como la inserción en la base de datos, asegurando que los datos extraídos se almacenen de manera segura y eficiente para su posterior análisis o uso.
