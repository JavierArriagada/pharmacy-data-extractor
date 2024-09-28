
from datetime import datetime
import mysql.connector
import credentials as config
from sentence_transformers import SentenceTransformer
import chromadb

# Establecer conexión a la base de datos MySQL
def connect_mysql():
    return mysql.connector.connect(
        host=config.IP,
        user=config.USER,
        password=config.PASSWORD,
        database=config.BD_NAME
    )

# Establecer conexión a Chroma DB
def connect_chroma():
    return chromadb.Client()

# Crear colección en Chroma DB y guardar embeddings
def save_embeddings_to_chroma(products, collection):
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
     # Prepare batch data
    product_names = [product['name'] for product in products]
    embeddings = model.encode(product_names)
    
    embeddings_list = []
    metadatas = []
    ids = []
    
    for idx, product in enumerate(products):
        embeddings_list.append(embeddings[idx].tolist())
        metadatas.append({'id': product['id'], 'spider_name': product['spider_name']})
        ids.append(str(product['id']))
    
    # Define batch size
    batch_size = 5461  # Maximum allowed batch size
    
    for start in range(0, len(products), batch_size):
        end = start + batch_size
        collection.add(
            embeddings=embeddings_list[start:end],
            metadatas=metadatas[start:end],
            ids=ids[start:end]
        )
        print(f"Successfully added {end - start} items to the collection.")

    print(f"Successfully added {len(products)} items to the collection.")

# Buscar productos similares en Chroma DB y guardar resultados
def find_and_save_similar_products():
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    chroma_client = connect_chroma()
    collection = chroma_client.get_collection(config.CHROMA_COLLECTION)
    print(f"Collection '{config.CHROMA_COLLECTION}' retrieved successfully.")
    internal_products = read_internal_products()
    print(f"Read {len(internal_products)} internal products.")
    results = []
    cfg_load_id = create_cfg_load()

    for product in internal_products:
        embedding = model.encode(product['name'])
        embedding_list = embedding.tolist()
        similar_products = collection.query(
            query_embeddings=[embedding_list], 
            where={'spider_name': {'$in': ['cruzverde', 'ahumada', 'salcobrand', 'profar', 'ligafarmacia']}}
        )

        print(f"Found {len(similar_products)} similar products for product '{product['name']}'.")

        # Iterate over the results
        for i, metadata in enumerate(similar_products['metadatas'][0]):
            product_pharma = read_external_product(metadata['id'])
            if product_pharma:
                result = (
                    cfg_load_id,
                    get_site_id(metadata['spider_name']),
                    product['prodcode'],
                    product['prodcode2'],
                    product_pharma['code'],
                    product_pharma['name'],
                    str(product_pharma['price']),
                    str(product_pharma['price_sale']),
                    str(product_pharma['price_benef']),
                    similar_products['distances'][0][i],
                    product_pharma['url']
                )
                results.append(result)
    print(f"Found {len(results)} similar products.")
    save_results_to_mysql(results)


# Leer productos internos desde MySQL
def read_internal_products():
    conn = connect_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM prd_product")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return products

#Leer producto externo by id
def read_external_product(id):
    conn = connect_mysql()
    cursor = conn.cursor(dictionary=True)
    # Use a parameterized query to safely inject the 'id' variable
    query = "SELECT * FROM scr_pharma WHERE id = %s"
    cursor.execute(query, (id,))
    
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return products[0]

# Leer productos externos desde MySQL
def read_external_products():
    conn = connect_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM scr_pharma")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return products

# Guardar resultados en MySQL
def save_results_to_mysql(results):
    conn = connect_mysql()
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO scr_result (id_load, id_site, prodcode, prodcode2, codext, name, price, priceoffer, pdesctender, prodrating, url)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(insert_query, results)
    conn.commit()
    cursor.close()
    conn.close()

def create_cfg_load():
    conn = connect_mysql()
    cursor = conn.cursor()
    
    insert_query = """
    INSERT INTO cfg_load 
    (restype, id_group, id_group2, descrip, mediatype, loadtype, clitype, codgentype, id_rel, loaddate, qty, qtyok, codefrom, codeto, datefrom, dateto, amount, id_prmusr, legcode, codprefix, id_coupontype, status, id_agreement) 
    VALUES 
    (951, null, null, 'carga scraping', 'P', 'I', 'C', null, null, %s, null, null, null, null, %s, %s, null, null, null, null, null, 'A', null)
    """

    # Current timestamp for loaddate, datefrom, and dateto
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(insert_query, (current_timestamp, current_timestamp, current_timestamp,))
    conn.commit()
    last_insert_id = cursor.lastrowid

    cursor.close()
    conn.close()
    
    return last_insert_id

# Obtener el ID del sitio basado en spider_name
def get_site_id(spider_name):
    site_ids = {
        'cruzverde': 11,
        'ahumada': 12,
        'salcobrand': 13,
        'profar': 14,
        'ligafarmacia': 15
    }
    return site_ids.get(spider_name, None)


def main():
    # Conectar a Chroma DB y crear la colección
    chroma_client = connect_chroma()
    collection = chroma_client.create_collection(config.CHROMA_COLLECTION)
    print(f"Collection '{config.CHROMA_COLLECTION}' created successfully.")
    # Leer productos externos y guardar embeddings en Chroma DB
    external_products = read_external_products()
    print(f"Read {len(external_products)} external products.")
    save_embeddings_to_chroma(external_products, collection)
    find_and_save_similar_products()

if __name__ == "__main__":
    main()
