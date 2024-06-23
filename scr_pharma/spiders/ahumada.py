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

class AhumadaSpider(scrapy.Spider):
    name = 'ahumada'
    allowed_domains = ['farmaciasahumada.cl']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Descomentar para ejecución en modo headless
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.categories = [
            'medicamentos',
            'belleza',
            'higiene-y-cuidado-personal',
            'dermocosmetica',
            'vitaminas-y-suplementos',
            'infantil-y-maternidad',
            'dispositivos-medicos',
            'bebidas-y-alimentos',
            'mundo-mascota',
            'recetario-magistral'
        ]

    def start_requests(self):
        yield scrapy.Request(url='https://www.farmaciasahumada.cl', callback=self.parse, dont_filter=True)

    def parse(self, response):
        self.driver.get(response.url)
        base_url = 'https://www.farmaciasahumada.cl/on/demandware.store/Sites-ahumada-cl-Site/default/Search-UpdateGrid'

        for category in self.categories:
            start = 0
            size = 48
            
            while True:
                url = f"{base_url}?cgid={category}&start={start}&sz={size}"
                self.driver.get(url)
                time.sleep(3)  # Wait for JavaScript to load contents
                
                try:
                    products = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'product-tile')]//div[contains(@class, 'product-tile h-100')]")
                    
                    if not products:
                        print(f"No products found for category {category}, breaking the loop.")
                        break
                    
                    for product in products:
                        loader = ItemLoader(item=ScrPharmaItem(), selector=product)
                        brand, product_url, product_name, price, price_internet = self.extract_product_details(product)
                        loader.add_value('brand', brand)
                        loader.add_value('url', product_url)
                        loader.add_value('name', product_name)
                        loader.add_value('price', price_internet)
                        loader.add_value('price_sale', price)
                        loader.add_value('category', category)
                        loader.add_value('timestamp', datetime.now())
                        loader.add_value('spider_name', self.name)
                        yield loader.load_item()
                
                except NoSuchElementException:
                    print(f"No products found due to NoSuchElementException for category {category}, breaking the loop.")
                    break
                
                more_button = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'more')]")
                if not more_button:
                    print(f"No more button found for category {category}, moving to next category.")
                    break

                more_button[0].click()
                start += size

    def extract_product_details(self, product):
        try:
            brand = product.find_element(By.XPATH, ".//div[@class='product-tile-brand']//span").text
        except NoSuchElementException:
            brand = 'No brand'
        try:
            product_url = product.find_element(By.XPATH, ".//a[@class='link']").get_attribute('href')
            product_name = product.find_element(By.XPATH, ".//a[@class='link']").text
        except NoSuchElementException:
            product_url = 'No URL'
            product_name = 'No name'
        try:
            price = product.find_element(By.XPATH, ".//span[@class = 'sales']//span").text
        except NoSuchElementException:
            price = '0'
        try:
            price_internet = product.find_element(By.XPATH, ".//del//span//span[@class='value']").get_attribute('content')
        except NoSuchElementException:
            price_internet = '0'
        return brand, product_url, product_name, price, price_internet

    def closed(self, reason):
        self.driver.quit()
