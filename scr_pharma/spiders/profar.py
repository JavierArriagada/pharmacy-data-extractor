import re
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
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
        chrome_options.add_argument("--headless")  # Uncomment for headless execution
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        # Maximize the browser window to ensure desktop mode
        self.driver.maximize_window()

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        self.driver.get(response.url)
        base_url = 'https://www.profar.cl/'
        time.sleep(5)  # Wait for JavaScript to load
        # Maximize the browser window to ensure desktop mode
        self.driver.maximize_window()
        # Click the menu trigger button to reveal the menu
        try:
            menu_button = self.driver.find_element(By.XPATH, "//button[@data-id='mega-menu-trigger-button']")
            self.driver.execute_script("arguments[0].click();", menu_button)
            time.sleep(2)  # Wait for the menu to appear
        except NoSuchElementException:
            print("Menu trigger button not found.")

        # Find main category elements
        categories_elements = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'vtex-mega-menu-2-x-menuItem')]//a")

        category_urls = []
        category_names = []

        # For each main category, extract href and name
        for category_element in categories_elements:
            category_url = category_element.get_attribute('href')
            category_name = category_element.text.strip()
            if category_url and category_url not in category_urls:
                category_urls.append(category_url)
                category_names.append(category_name)
            else:
                continue  # Skip if URL is already in the list

            # Hover over the category to reveal subcategories
            action = ActionChains(self.driver)
            action.move_to_element(category_element).perform()
            time.sleep(2)  # Wait for subcategories to appear

            # Extract subcategory elements
            subcategory_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'vtex-mega-menu-2-x-submenuList')]//a")
            for subcategory_element in subcategory_elements:
                subcategory_url = subcategory_element.get_attribute('href')
                subcategory_name = subcategory_element.text.strip()
                if subcategory_url and subcategory_url not in category_urls:
                    category_urls.append(subcategory_url)
                    category_names.append(subcategory_name)

        # Now, for each category URL, proceed to scrape products
        for url, category in zip(category_urls, category_names):
            self.driver.get(url)
            time.sleep(5)  # Wait for JavaScript to load

            current_url = self.driver.current_url  # Store the current URL
            while True:
                self.scroll_to_pagination()  # Scroll to the pagination button and click
                time.sleep(2)  # Wait for products to load

                new_url = self.driver.current_url  # Get the new URL after the click
                if current_url == new_url:
                    print("URL has not changed after clicking 'Show more', stopping pagination.")
                    break  # If URL doesn't change, stop pagination
                else:
                    current_url = new_url  # Update current URL for next iteration

                # Scroll back to the top to ensure all elements are loaded
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)  # Give time for scroll and load to complete

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
            # Scroll to the bottom of the page first to load all elements
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for all products to load

            # Then, locate the load more button
            load_more_button = self.driver.find_element(By.XPATH, "//button[contains(@class, 'vtex-button bw1 ba fw5 v-mid relative pa0 lh-solid br2 min-h-small t-action--small bg-action-primary b--action-primary c-on-action-primary hover-bg-action-primary hover-b--action-primary hover-c-on-action-primary pointer')]")

            # Scroll to the button
            self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
            time.sleep(2)  # Small wait to ensure scroll has completed

            # Click the button
            self.driver.execute_script("arguments[0].click();", load_more_button)
        except NoSuchElementException:
            print("Load more button not found.")

    def extract_product_details(self, product):
        try:
            product_url = product.find_element(By.XPATH, ".//a").get_attribute('href')
            # Use regex to extract SKU from URL
            # Extract the last part of the URL before '/p'
            last_part = product_url.rstrip('/').split('/')[-1]
            if last_part == 'p':
                last_part = product_url.rstrip('/').split('/')[-2]
            # Find the last numeric sequence in last_part
            matches = re.findall(r'(\d+)', last_part)
            if matches:
                sku = matches[-1]
            else:
                sku = 'No SKU'
        except NoSuchElementException:
            product_url = 'No URL'
            sku = 'No SKU'
        try:
            product_name = product.find_element(By.XPATH, ".//article//div[10]//span").text
        except NoSuchElementException:
            product_name = 'No name'

        # Extract the price by concatenating the spans
        try:
            price_container = product.find_element(By.XPATH, ".//span[contains(@class,'listPriceValue')]//span[contains(@class,'currencyContainer')]")
            price_parts = price_container.find_elements(By.XPATH, "./span")
            price = ''.join([part.text for part in price_parts])
        except NoSuchElementException:
            price = '0'

        # Extract the sale price by concatenating the spans (if available)
        try:
            price_sale_container = product.find_element(By.XPATH, ".//span[contains(@class,'sellingPriceValue')]//span[contains(@class,'currencyContainer')]")
            price_sale_parts = price_sale_container.find_elements(By.XPATH, "./span")
            price_sale = ''.join([part.text for part in price_sale_parts])
        except NoSuchElementException:
            price_sale = price  # If no sale price, use normal price

        # Fallback for price if both normal and sale prices are missing
        if price == '0' and price_sale == '0':
            sku = 'No SKU'
            try:
                price = product.find_element(By.XPATH, ".//div[contains(@class, 'priceWithoutStock')]//span").text
                price_sale = price
            except NoSuchElementException:
                price = '0'

        price_benef = '0'  # Adjust this XPath to retrieve benefit price if available
        brand = self.name
        return brand, product_url, product_name, price, price_sale, price_benef, sku

    def closed(self, reason):
        self.driver.quit()
