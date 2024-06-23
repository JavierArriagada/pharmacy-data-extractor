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

class FarmexSpider(scrapy.Spider):
    name = 'farmex'
    allowed_domains = ['farmex.cl']
    start_urls = ['https://farmex.cl/']
    base_url = 'https://farmex.cl/collections/'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Uncomment for headless execution
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        self.categories = ['analgesicos']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        self.driver.get(response.url)
        time.sleep(5)  # Wait for JavaScript to load contents
        for category in self.categories:
            url = f"{self.base_url}{category}"
            self.driver.get(url)
            time.sleep(5)  # Wait for JavaScript to load contents
            
            while True:
                try:
                    products = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'product-grid-item')]")
                    if not products:
                        print("No products found, breaking the loop.")
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
                    print("No products found due to NoSuchElementException, breaking the loop.")
                    break

                # Add pagination logic here if required
                #self.scroll_to_pagination()

                # Handling pagination
                next_page_button = self.get_next_page_button()
                if next_page_button:
                    self.driver.execute_script("arguments[0].click();", next_page_button)
                    time.sleep(5)  # Wait for the page to load
                else:
                    print("No more pages to navigate.")
                    break
                
                
    def extract_product_details(self, product):
        try:
            product_name_element = product.find_element(By.XPATH, ".//h5[contains(@class, 'product-name')]//a")
            product_url = product_name_element.get_attribute('href')
            product_name = product_name_element.text
        except NoSuchElementException:
            product_url = 'No URL'
            product_name = 'No name'
        try:
            price = product.find_element(By.XPATH, ".//span[contains(@class, 'price-compare')]").text
        except NoSuchElementException:
            price = 'No price'
        try:
            price_sale = product.find_element(By.XPATH, ".//span[contains(@class, 'price-sale')]").text
        except NoSuchElementException:
            price_sale = 'No sale price'

        price_benef = '0'  # Adjust this XPath to retrieve benefit price if available
        sku = '0' # Adjust this XPath to retrieve sku price if available
        brand = 'brand'
        return brand, product_url, product_name, price, price_sale, price_benef, sku
    '''
    def scroll_to_pagination(self):
        try:
            pagination_element = self.driver.find_element(By.XPATH, "//nav[@class='pagination-container']")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", pagination_element)
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of(pagination_element)
            )
        except (NoSuchElementException, TimeoutException):
            print("Pagination element not found or not visible.")
    '''
    def get_next_page_button(self):
        try:
            next_button = self.driver.find_element(By.XPATH, "//a[@class='next']")
            if "disabled" in next_button.get_attribute("class"):
                return None
            return next_button
        except NoSuchElementException:
            return None
    
    def closed(self, reason):
        self.driver.quit()
