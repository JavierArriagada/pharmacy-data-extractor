import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
import time
from scrapy.loader import ItemLoader
from datetime import datetime
from ..items import ScrPharmaItem

class FarmexSpider(scrapy.Spider):
    name = 'farmex'
    allowed_domains = ['farmex.cl']
    start_urls = ['https://farmex.cl/']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Uncomment for headless execution
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.action = ActionChains(self.driver)

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], callback=self.parse_categories)

    def parse_categories(self, response):
        self.driver.get(response.url)
        time.sleep(2)  # Wait for JavaScript to load contents
        self.close_popup()
        category_elements = self.driver.find_elements(By.XPATH, "//ul[@class='nav main-nav']//li[@class='dropdown'][1]//ul[@class='dropdown-menu']//li[@class='dropdown dropdown-submenu']//a[@class='dropdown-link']")
        
        categories = []
        for element in category_elements:
            category_url = element.get_attribute('href')
            category_name = category_url.split('/')[-1]
            categories.append((category_name, category_url))
        
        # Process categories one by one
        for category_name, category_url in categories:
            yield scrapy.Request(url=category_url, callback=self.parse_category, meta={'category_name': category_name, 'category_url': category_url})

    def parse_category(self, response):
        category = response.meta['category_name']
        category_url = response.meta['category_url']
        
        if 'collections' in category_url or 'collections' in category:
            yield from self.parse_collections(response, category)
        else:
            yield from self.parse_pages(response, category)

    def parse_collections(self, response, category):
        self.driver.get(response.url)
        time.sleep(2)  # Wait for JavaScript to load contents
        self.close_popup()

        page_number = 1
        while True:
            # Extract items from the current page
            items = list(self.extract_items(category))
            
            if not items:
                self.logger.info(f"No more products found in category {category}. Ending pagination.")
                break

            for item in items:
                yield item

            # Try to navigate to the next page
            page_number += 1
            next_page_url = f"{response.url.split('?')[0]}?page={page_number}"
            self.driver.get(next_page_url)
            time.sleep(2)  # Wait for the new page to load
            self.close_popup()

            # Check if there are products on the new page
            if not self.driver.find_elements(By.XPATH, "//div[contains(@class, 'product-grid-item')]"):
                self.logger.info(f"No more products found on page {page_number} of category {category}. Ending pagination.")
                break

    def extract_items(self, category):
        products = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'product-grid-item')]")
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

    def close_popup(self):
        try:
            body = self.driver.find_element(By.TAG_NAME, 'body')
            self.action.move_to_element(body).click().perform()
            time.sleep(1)
        except Exception as e:
            print(f"Error closing popup: {str(e)}")

    def parse_pages(self, response, category):
        self.logger.info(f"Non-collection category detected: {category}. This is a placeholder for future implementation.")
        yield from ()             
                
    def extract_product_details(self, product):
        try:
            product_name_element = product.find_element(By.XPATH, ".//h5[contains(@class, 'product-name')]//a")
            product_url = product_name_element.get_attribute('href')
            product_name = product_name_element.text
        except NoSuchElementException:
            product_url = 'No URL'
            product_name = 'No name'
        try:
            price_elements = product.find_elements(By.XPATH, ".//div[contains(@class, 'product-price')]//span")
            if len(price_elements) == 1:
                price = price_elements[0].text
                price_sale = 'No sale price'
            elif len(price_elements) == 2:
                price = price_elements[0].text
                price_sale = price_elements[1].text
            else:
                price = 'No price'
                price_sale = 'No sale price'
        except NoSuchElementException:
            price = 'No price'
            price_sale = 'No sale price'

        price_benef = '0'  # Adjust this XPath to retrieve benefit price if available
        sku = '0'  # Adjust this XPath to retrieve sku if available
        brand = 'brand'
        return brand, product_url, product_name, price, price_sale, price_benef, sku
    
    def closed(self, reason):
        self.driver.quit()
