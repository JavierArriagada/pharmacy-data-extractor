import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
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
        chrome_options.add_argument("--headless")  # Descomentar para ejecución en modo headless
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.visited_urls = set()
        self.processed_categories = set()
        self.action = ActionChains(self.driver)

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], callback=self.parse_categories)

    def parse_categories(self, response):
        self.driver.get(response.url)
        time.sleep(2)  # Wait for JavaScript to load contents
        self.close_popup()
        
        # Collect all category links
        categories = set()
        
        # List of XPaths to collect category elements
        category_xpaths = [
            "//ul[@class='nav main-nav']//li[@class='dropdown'][1]",
            "//ul[@class='nav main-nav']//li[@class='dropdown'][2]",
            "//ul[@class='nav main-nav']//li[@class='dropdown'][3]",
            "(//ul[@class='nav main-nav']//li)[176]",
            "//ul[@class='nav main-nav']//li[@class='dropdown'][5]"
        ]
        
        for xpath in category_xpaths:
            category_element = self.driver.find_element(By.XPATH, xpath)
            # Collect all <a href=""> elements within this category element
            a_elements = category_element.find_elements(By.XPATH, ".//a[@href]")
            for a in a_elements:
                category_url = a.get_attribute('href')
                category_name =  category_url.split('/')[-1]
                if category_url and category_url not in self.visited_urls:
                    self.visited_urls.add(category_url)
                    categories.add((category_name, category_url))
        
        # Now we have collected all the category URLs, we can process them
        for category_name, category_url in categories:
            yield scrapy.Request(
                url=category_url,
                callback=self.parse_category,
                meta={'category_name': category_name, 'category_url': category_url}
            )

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
        self.driver.get(response.url)
        time.sleep(2)  # Wait for JavaScript to load contents
        self.close_popup()

        # Extract items from the single page
        items = list(self.extract_page_items(category))
        
        for item in items:
            yield item           

    def extract_product_details(self, product):
        try:
            product_name_element = product.find_element(By.XPATH, ".//h5[contains(@class, 'product-name')]//a")
            product_url = product_name_element.get_attribute('href')
            product_name = product_name_element.text
        except NoSuchElementException:
            product_url = 'No URL'
            product_name = 'No name'
        
        # Extract prices and other details
        try:
            price_elements = product.find_elements(By.XPATH, ".//div[contains(@class, 'product-price')]//span")
            if len(price_elements) == 1:
                price = price_elements[0].text
                price_sale = price
            elif len(price_elements) == 2:
                price = price_elements[0].text
                price_sale = price_elements[1].text
            else:
                price = 'No price'
                price_sale = 'No sale price'
        except NoSuchElementException:
            price = 'No price'
            price_sale = 'No sale price'

        price_benef = '0'  
        sku = 'No SKU'
        
        # Open product URL to extract additional information
        self.driver.execute_script("window.open(arguments[0], '_blank');", product_url)
        self.driver.switch_to.window(self.driver.window_handles[-1])
        
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='product-availability-wrapper']//ul[@class='list-unstyled']//a")
                )
            )
            brand_element = self.driver.find_element(
                By.XPATH, "//div[@class='product-availability-wrapper']//ul[@class='list-unstyled']//a"
            )
            brand = brand_element.text
        except (NoSuchElementException, TimeoutException):
            brand = 'No brand'

        # If price_sale is "Sin Stock" or does not exist, extract price from the product page
        if price_sale == 'No sale price' or "Sin Stock" in price_sale:
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[@class='product-price']//div[@class='detail-price']")
                    )
                )
                price = self.driver.find_element(
                    By.XPATH, "//div[@class='product-price']//div[@class='detail-price']"
                ).text
                price_sale = price
            except (NoSuchElementException, TimeoutException):
                price = 'No price'
                price_sale = 'No sale price'

        if price == '0' and price_sale != '0':
            price = price_sale

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        
        return brand, product_url, product_name, price, price_sale, price_benef, sku

    def extract_page_items(self, category):
        products = self.driver.find_elements(By.XPATH, "//div[@class='item-content']")
        for product in products:
            loader = ItemLoader(item=ScrPharmaItem(), selector=product)
            brand, product_url, product_name, price, price_sale, price_benef, sku = self.extract_page_product_details(product)
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

    def extract_page_product_details(self, product):
        try:
            product_name_element = product.find_element(By.XPATH, ".//a[contains(@class, 'product-title')]")
            product_url = product_name_element.get_attribute('href')
            product_name = product_name_element.text
        except NoSuchElementException:
            product_url = 'No URL'
            product_name = 'No name'
        
        # Extract prices and other details
        try:
            price_element = product.find_element(By.XPATH, ".//span[contains(@class, 'product-compare-price')]")
            price = price_element.text
            price_sale_element = product.find_element(By.XPATH, ".//span[contains(@class, 'product-price')]")
            price_sale = price_sale_element.text
        except NoSuchElementException:
            price = 'No price'
            price_sale = 'No sale price'

        price_benef = '0'  
        sku = 'No SKU'  
        
        # Open product URL to extract additional information
        self.driver.execute_script("window.open(arguments[0], '_blank');", product_url)
        self.driver.switch_to.window(self.driver.window_handles[-1])
        
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='product-availability-wrapper']//ul[@class='list-unstyled']//a")
                )
            )
            brand_element = self.driver.find_element(
                By.XPATH, "//div[@class='product-availability-wrapper']//ul[@class='list-unstyled']//a"
            )
            brand = brand_element.text
        except (NoSuchElementException, TimeoutException):
            # Try alternative XPath for brand
            try:
                brand_element = self.driver.find_element(By.XPATH, "//div[@class='vendor']//a")
                brand = brand_element.text
            except (NoSuchElementException, TimeoutException):
                brand = 'No brand'

        # If price_sale is "Sin Stock" or does not exist, extract price from the product page
        if price_sale == 'No sale price' or "Sin Stock" in price_sale:
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[@class='product-price']//div[@class='detail-price']")
                    )
                )
                price = self.driver.find_element(
                    By.XPATH, "//div[@class='product-price']//div[@class='detail-price']"
                ).text
                price_sale = price
            except (NoSuchElementException, TimeoutException):
                price = 'No price'
                price_sale = 'No sale price'

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        
        return brand, product_url, product_name, price, price_sale, price_benef, sku
    
    def closed(self, reason):
        self.driver.quit()
