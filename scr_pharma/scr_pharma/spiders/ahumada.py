import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time

class AhumadaSpider(scrapy.Spider):
    name = 'ahumada'
    allowed_domains = ['farmaciasahumada.cl']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        options = Options()
        #options.headless = True  # Uncomment to run in headless mode
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.categories = [
            'dispositivos-medicos-primeros-auxilios'
            #'medicamentos-enfermedades-especificas',
            #'medicamentos-sistema-nervioso' 
            ]
        self.current_category_index = 0

    def start_requests(self):
        yield scrapy.Request(url='https://www.farmaciasahumada.cl', callback=self.parse, dont_filter=True)

    def parse(self, response):
        self.driver.get(response.url)
        base_url = 'https://www.farmaciasahumada.cl/on/demandware.store/Sites-ahumada-cl-Site/default/Search-UpdateGrid'
        
        while self.current_category_index < len(self.categories):
            category = self.categories[self.current_category_index]
            start = 0
            size = 12
            
            url = f"{base_url}?cgid={category}&start={start}&sz={size}"
            self.driver.get(url)
            
            while True:
                time.sleep(3)  # Wait for JavaScript to load contents
                try:
                    products = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'product-tile')]//div[contains(@class, 'product-tile h-100')]")
                    for product in products:
                        # Extract product details with error handling
                        brand, product_url, product_name, price, price_internet = self.extract_product_details(product)
                        yield {
                            'brand': brand,
                            'product_url': product_url,
                            'product_name': product_name,
                            'price': price,
                            'price_internet': price_internet,
                            'category': category
                        }
                except NoSuchElementException:
                    # Handle the case where the product list itself is not found
                    break
                
                more_button = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'more')]")
                if not more_button:
                    print(f"No more button found for category {category}, moving to next category.")
                    break

                more_button[0].click()
                start += size
                url = f"{base_url}?cgid={category}&start={start}&sz={size}"
                self.driver.get(url)
            
            self.current_category_index += 1

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
            price = 'No price'
        try:
            price_internet = product.find_element(By.XPATH, ".//del//span//span[@class='value']").get_attribute('content')
        except NoSuchElementException:
            price_internet = 'No internet price'
        return brand, product_url, product_name, price, price_internet

    def closed(self, reason):
        self.driver.quit()
