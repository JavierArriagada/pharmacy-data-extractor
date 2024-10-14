import json
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time

from scrapy.loader import ItemLoader
from datetime import datetime
from ..items import ScrPharmaItem 


class CruzVerdeSpider(scrapy.Spider):
    name = 'cruzverde'
    allowed_domains = ['cruzverde.cl']
    start_urls = ['https://www.cruzverde.cl/']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        #chrome_options.add_argument("--headless")  # Descomentar para ejecución en modo headless
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def parse(self, response):
        self.driver.get(response.url)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            cookies = self.driver.get_cookies()
            for cookie in cookies:
                self.driver.add_cookie(cookie)

            api_url = 'https://api.cruzverde.cl/product-service/categories/category-tree?showInMenu=true'
            self.driver.get(api_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            data = json.loads(self.driver.find_element(By.TAG_NAME, 'body').text)
            for item in data:
                yield from self.extract_category(item, path=[])
        except Exception as e:
            self.logger.error(f"Error loading page: {str(e)}")
            self.driver.quit()

    def extract_category(self, category, path):
        new_path = path + [category['name']]
        category_id = category['id']
        full_url = f"https://www.cruzverde.cl{category['path']}"

        yield scrapy.Request(
            full_url, 
            callback=self.load_category_page, 
            meta={'category_path': new_path, 'category_id': category_id, 'category_url': full_url}
        )

        if 'categories' in category:
            for subcategory in category['categories']:
                yield from self.extract_category(subcategory, new_path)

    def load_category_page(self, response):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )

            category_id = response.meta['category_id']
            category_path = response.meta['category_path']
            offset = 0
            limit = 48

            # Obtener el total de productos en la primera iteración
            api_url = f"https://api.cruzverde.cl/product-service/products/search?limit={limit}&offset={offset}&sort=&q=&refine[]=cgid={category_id}&inventoryId=zona308&inventoryZone=zona308"
            self.driver.get(api_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            data = json.loads(self.driver.find_element(By.TAG_NAME, 'body').text)

            total_products = data.get('total', 0)
            iterations = (total_products + limit - 1) // limit  # Número total de iteraciones necesarias

            for i in range(iterations):
                offset = i * limit
                api_url = f"https://api.cruzverde.cl/product-service/products/search?limit={limit}&offset={offset}&sort=&q=&refine[]=cgid={category_id}&inventoryId=zona308&inventoryZone=zona308"
                self.driver.get(api_url)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'body'))
                )
                data = json.loads(self.driver.find_element(By.TAG_NAME, 'body').text)
                
                for product in data.get('hits', []):
                    image_link = product['image']['link']
                    # Extraer el código del producto y el código de categoría
                    try:
                        product_code, cat_code = image_link.split('/')[-1].split('-', 1)
                        cat_code = cat_code.split('.jpg')[0]
                        product_url = f"https://www.cruzverde.cl/{cat_code}/{product_code}.html"
                    except Exception as e:
                        self.logger.warning(f"Error parsing image link '{image_link}': {str(e)}")
                        product_url = response.url  # Fallback a la URL de la categoría

                    loader = ItemLoader(item=ScrPharmaItem())
                    loader.add_value('brand', product.get('brand', 'Unknown Brand'))
                    loader.add_value('name', product.get('productName', 'Unknown Product Name'))
                    loader.add_value('url', product_url)
                    price = product.get('prices', {}).get('price-list-cl', '0')                   
                    loader.add_value('price', price)
                    loader.add_value('price_sale', product.get('prices', {}).get('price-sale-cl', price))
                    loader.add_value('price_benef', '0')
                    loader.add_value('code', product.get('productId', 'No SKU'))
                    loader.add_value('category', ' > '.join(category_path))                    
                    loader.add_value('timestamp', datetime.now())
                    loader.add_value('spider_name', self.name)
                    yield loader.load_item()

        except Exception as e:
            self.logger.error(f"Error loading category page: {str(e)}")

    def closed(self, reason):
        self.driver.quit()
