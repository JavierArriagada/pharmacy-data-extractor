import scrapy
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.firefox import GeckoDriverManager
import time

class LigaFarmaciaSpider(scrapy.Spider):
    name = 'ligafarmacia'
    allowed_domains = ['ligafarmacia.cl']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        options = Options()
        #options.headless = True  # Uncomment to run in headless mode
        self.driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        self.start_urls = ['https://ligafarmacia.cl/medicamentos/']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        self.driver.get(response.url)
        while True:
            time.sleep(3)  # Wait for JavaScript to load contents
            self.extract_products()

            next_button = self.get_next_page_button()
            if next_button:
                try:
                    self.driver.execute_script("arguments[0].click();", next_button)
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    self.driver.execute_script("arguments[0].click();", next_button)
            else:
                break

    def extract_products(self):
        products = self.driver.find_elements(By.XPATH, "//div[@class='product-wrap mb-25']")
        for product in products:
            print(product)
            product_url, product_name, brand, price = self.extract_product_details(product)
            yield {
                'product_url': product_url,
                'product_name': product_name,
                'brand': brand,
                'price': price
            }

    def extract_product_details(self, product):
        try:
            product_url = product.find_element(By.XPATH, ".//a").get_attribute('href')
        except NoSuchElementException:
            product_url = 'No URL'
        try:
            product_name = product.find_element(By.XPATH, ".//p[contains(@class, 'nombre')]").text
        except NoSuchElementException:
            product_name = 'No name'
        try:
            brand = product.find_element(By.XPATH, ".//p[contains(@class, 'laboratorio')]").text
        except NoSuchElementException:
            brand = 'No brand'
        try:
            price = product.find_element(By.XPATH, ".//p[contains(@class, 'precio')]").text
        except NoSuchElementException:
            price = 'No price'
                    
        return product_url, product_name, brand, price

    def get_next_page_button(self):
        try:
            current_page = self.driver.find_element(By.XPATH, "//li[@class='page-item active']")
            next_page = current_page.find_element(By.XPATH, "following-sibling::li[@class='page-item null']")
            
            if next_page:
                try:
                    next_button = next_page.find_element(By.XPATH, ".//button")
                except NoSuchElementException:
                    next_button = next_page.find_element(By.XPATH, ".//a")
                return next_button
        except NoSuchElementException:
            return None
        return None

    def closed(self, reason):
        self.driver.quit()
