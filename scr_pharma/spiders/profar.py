import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
from scrapy.loader import ItemLoader
from datetime import datetime
from ..items import ScrPharmaItem

class ProfarSpider(scrapy.Spider):
    name = 'profar'
    allowed_domains = ['profar.cl']
    start_urls = ['https://www.profar.cl']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Uncomment for headless execution
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.categories = [
            'medicamentos',
            'dermocosmetica',
            'belleza',
            'cuidado-personal',
            'salud-animal'
            ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        self.driver.get(response.url)
        base_url = 'https://www.profar.cl/'
        time.sleep(5)  # Esperar a que se cargue el JavaScript
        for category in self.categories:
            url = f"{base_url}{category}"
            self.driver.get(url)
            time.sleep(5)  # Esperar a que se cargue el JavaScript
            
            current_url = self.driver.current_url  # Almacenar la URL actual
            while True:
                self.scroll_to_pagination()  # Desplazarse al botón de paginación y hacer clic
                time.sleep(2)  # Esperar a que carguen los productos
                
                new_url = self.driver.current_url  # Obtener la nueva URL después del clic
                if current_url == new_url:
                    print("URL has not changed after clicking 'Show more', stopping pagination.")
                    break  # Si la URL no cambia, detener la paginación
                else:
                    current_url = new_url  # Actualizar la URL actual para la siguiente iteración
                
                # Desplazarse de nuevo al inicio de la página para asegurar que todos los elementos estén cargados
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)  # Dar tiempo para que el scroll y la carga se completen

            # Extracción de productos después de asegurar que todos los elementos estén visibles
            products_after_click = self.driver.find_elements(By.XPATH, "//section[contains(@class, 'product-summary')]")
            for product in products_after_click:
                loader = ItemLoader(item=ScrPharmaItem(), selector=product)
                brand, product_url, product_name, price, price_sale, price_benef, sku = self.extract_product_details(product)
                loader.add_value('brand', brand)
                loader.add_value('url', product_url)
                loader.add_value('name', product_name)
                loader.add_value('price', price)
                loader.add_value('price_sale', price_sale)
                loader.add_value('price_benef', price_benef)
                loader.add_value('code', sku)
                loader.add_value('category', category)
                loader.add_value('timestamp', datetime.now())
                loader.add_value('spider_name', self.name)
                yield loader.load_item()

    def scroll_to_pagination(self):
        try:
            # Desplazarse al final de la página primero para cargar todos los elementos
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Esperar a que se carguen todos los productos
            
            # Luego, localizar el botón de cargar más resultados
            load_more_button = self.driver.find_element(By.XPATH, "//button[contains(@class, 'vtex-button bw1 ba fw5 v-mid relative pa0 lh-solid br2 min-h-small t-action--small bg-action-primary b--action-primary c-on-action-primary hover-bg-action-primary hover-b--action-primary hover-c-on-action-primary pointer')]")
            
            # Hacer scroll hasta el botón
            self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
            time.sleep(2)  # Pequeña espera para asegurar que el scroll se ha completado

            # Hacer clic en el botón
            self.driver.execute_script("arguments[0].click();", load_more_button)
        except NoSuchElementException:
            print("Load more button not found.")

                
    def extract_product_details(self, product):
        try:
            product_url = product.find_element(By.XPATH, ".//a").get_attribute('href')
        except NoSuchElementException:
            product_url = 'No URL'
        try:
            product_name = product.find_element(By.XPATH, ".//article//div[12]//span").text
        except NoSuchElementException:
            product_name = 'No name'
        '''try:
            brand = product.find_element(By.XPATH, ".//div[contains(@class, 'product-brand')]").text
        except NoSuchElementException:
            brand = 'No brand' 
            '''
        try:
            price = product.find_element(By.XPATH, ".//article//div[14]//span[contains(@class,'sellingPriceValue')]").text
        except NoSuchElementException:
            price = 'No price'
        try:
            price_sale = product.find_element(By.XPATH, ".//article//div[14]//span[contains(@class,'listPriceValue')]").text
        except NoSuchElementException:
            price_sale = 'No price'
        price_benef = '0'  # Adjust this XPath to retrieve benefit price if available
        price_sale = '0'  # Adjust this XPath to retrieve sale price if available
        sku = '0'  # Adjust this XPath to retrieve SKU if available
        brand = 'Profar'
        return brand, product_url, product_name, price, price_sale, price_benef, sku
    
    def closed(self, reason):
        self.driver.quit()
