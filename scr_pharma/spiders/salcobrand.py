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


import urllib.parse
class SalcobrandSpider(scrapy.Spider):
    name = 'salcobrand'
    allowed_domains = ['salcobrand.cl']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        #chrome_options.add_argument("--headless")  # Uncomment for headless execution
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.categories = ['medicamentos']

    def start_requests(self):
        yield scrapy.Request(url='https://salcobrand.cl', callback=self.parse, dont_filter=True)

    def parse(self, response):
        self.driver.get(response.url)
        base_url = 'https://salcobrand.cl/t/'

        for category in self.categories:
            url = f"{base_url}{category}"
            self.driver.get(url)
            time.sleep(5)  # Wait for JavaScript to load contents
            
            try:
                products = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'product clickable')]")
                
                if not products:
                    print(f"No products found for category {category}, breaking the loop.")
                    break
                
                for product in products:
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
            
            except NoSuchElementException:
                print(f"No products found due to NoSuchElementException for category {category}, breaking the loop.")
                break

    def extract_product_details(self, product):
        try:
            brand = 'Default Brand'  # Adjust according to the site's structure if needed
        except NoSuchElementException:
            brand = 'No brand'
        try:
            product_url = product.find_element(By.XPATH, ".//a").get_attribute('href')
            product_name = product.find_element(By.XPATH, ".//div[contains(@class, 'info')]//a//span[contains(@class, 'product-info')]").text
            parsed_url = urllib.parse.urlparse(product_url)
            params = urllib.parse.parse_qs(parsed_url.query)
            sku = params.get('default_sku', [''])[0]
            product_url = urllib.parse.urlunparse(parsed_url._replace(query=''))
        except NoSuchElementException:
            product_url = 'No URL'
            product_name = 'No name'
            sku = 'No SKU'
        try:
            price = product.find_element(By.XPATH, ".//div[contains(@class, 'info')]//a//div[contains(@class, 'product-prices')]//div[contains(@class, 'sale-price secondary-price')]//span").text
        except NoSuchElementException:
            price = '0'
        price_benef = '0'  # Adjust this XPath to retrieve benefit price if available
        price_sale = '0'  # Adjust this XPath to retrieve benefit price if available
        
        return brand, product_url, product_name, price, price_sale, price_benef, sku

    def closed(self, reason):
        self.driver.quit()