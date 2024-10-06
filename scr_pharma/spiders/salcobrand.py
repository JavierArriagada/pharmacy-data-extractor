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
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select
import urllib.parse

class SalcobrandSpider(scrapy.Spider):
    name = 'salcobrand'
    allowed_domains = ['salcobrand.cl']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Descomentar para ejecución en modo headless
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.categories = []
        self.start_urls = ['https://salcobrand.cl/']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        # Navegar al sitio principal
        self.driver.get(response.url)
        time.sleep(5)  # Esperar a que cargue la página

        # Extract the hrefs of the categories
        try:
            category_elements = self.driver.find_elements(By.XPATH, "//ul[contains(@id, 'categories-menu')]//a")
            for element in category_elements:
                href = element.get_attribute('href')
                if href and href not in self.categories:
                    self.categories.append(href)
            print(f"Extracted {len(self.categories)} category URLs.")
        except NoSuchElementException:
            print("No category elements found.")

        # Iterar sobre cada URL de categoría extraída
        for category_url in self.categories:
            self.driver.get(category_url)
            time.sleep(5)  # Esperar a que cargue el contenido por JavaScript

            # Extraer el nombre de la categoría
            category_name = self.extract_category_name(category_url)

            # Seleccionar el máximo número de resultados por página
            self.select_max_results_per_page()

            while True:
                try:
                    products = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'product clickable')]")

                    if not products:
                        print(f"No products found for category {category_url}, breaking the loop.")
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
                        loader.add_value('category', category_name)
                        loader.add_value('timestamp', datetime.now())
                        loader.add_value('spider_name', self.name)
                        yield loader.load_item()

                except NoSuchElementException:
                    print(f"No products found due to NoSuchElementException for category {category_url}, breaking the loop.")
                    break

                # Desplazar hasta el final antes de buscar el botón de la próxima página
                self.scroll_to_pagination()

                # Lógica de paginación
                next_page_button = self.get_next_page_button()
                if next_page_button:
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", next_page_button)
                        WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable(next_page_button)
                        )
                        self.driver.execute_script("arguments[0].click();", next_page_button)
                        time.sleep(5)  # Esperar a que la página se cargue
                    except Exception as e:
                        print(f"Error al hacer clic en el botón de siguiente página: {str(e)}")
                        break
                else:
                    print("No más páginas para navegar.")
                    break

    def extract_category_name(self, category_url):
        parsed_url = urllib.parse.urlparse(category_url)
        path_parts = parsed_url.path.strip('/').split('/')
        category_parts = [part.replace('-', ' ').title() for part in path_parts if part and part != 't']
        return ' > '.join(category_parts)

    def select_max_results_per_page(self):
        try:
            select_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//select[contains(@class, 'ais-HitsPerPage-select')]"))
            )
            select = Select(select_element)
            select.select_by_index(len(select.options) - 1)
            time.sleep(5)
            print("Seleccionado el máximo número de resultados por página.")
        except Exception as e:
            print(f"Error al seleccionar el máximo número de resultados por página: {str(e)}")

    def scroll_to_pagination(self):
        try:
            pagination_element = self.driver.find_element(By.XPATH, "//nav[contains(@class, 'paginator')]")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", pagination_element)
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of(pagination_element)
            )
        except NoSuchElementException:
            print("Pagination element not found, maybe it's a single page without pagination.")
        except TimeoutException:
            print("Pagination element not visible after 10 seconds.")

    def extract_product_details(self, product):
        try:
            brand = product.find_element(By.XPATH, ".//div[contains(@class, 'info')]//a//span[contains(@class, 'product-name truncate')]").text
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
            price_benef = product.find_element(By.XPATH, ".//div[contains(@class, 'info')]//a//div[contains(@class, 'product-prices')]//div[contains(@class, 'internet-sale-price')]//span").text
        except NoSuchElementException:
            price_benef = '0'

        if price_benef != '0':
            try:
                price_sale = product.find_element(By.XPATH, ".//div[contains(@class, 'info')]//a//div[contains(@class, 'product-prices')]//div[contains(@class, 'sale-price secondary-price')]//span").text
            except NoSuchElementException:
                price_sale = '0'
            try:
                price = product.find_element(By.XPATH, ".//div[contains(@class, 'info')]//a//div[contains(@class, 'product-prices')]//div[contains(@class, 'original-price')]//span").text
            except NoSuchElementException:
                price = '0'
        else:
            try:
                price_sale = product.find_element(By.XPATH, ".//div[contains(@class, 'info')]//a//div[contains(@class, 'product-prices')]//div[contains(@class, 'sale-price')]//span").text
            except NoSuchElementException:
                price_sale = '0'
            if price_sale == '0':
                try:
                    price = product.find_element(By.XPATH, ".//div[contains(@class, 'info')]//a//div[contains(@class, 'product-prices')]//div[contains(@class, 'sale-price')]//span").text
                except NoSuchElementException:
                    price = '0'
            else:
                try:
                    price = product.find_element(By.XPATH, ".//div[contains(@class, 'info')]//a//div[contains(@class, 'product-prices')]//div[contains(@class, 'original-price')]//span").text
                except NoSuchElementException:
                    price = '0'

        if price == '0' and price_sale != '0':
            price = price_sale

        if price_sale == '0':
            price_sale = price

        return brand, product_url, product_name, price, price_sale, price_benef, sku

    def get_next_page_button(self):
        try:
            active_page = self.driver.find_element(By.XPATH, "//nav[contains(@class, 'paginator')]//ul//li[contains(@class, 'active')]")
            next_page = active_page.find_element(By.XPATH, "following-sibling::li[1]//a")
            return next_page
        except NoSuchElementException:
            return None

    def closed(self, reason):
        self.driver.quit()