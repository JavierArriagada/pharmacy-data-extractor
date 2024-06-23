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
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select


class LigaFarmaciaSpider(scrapy.Spider):
    name = 'ligafarmacia'
    allowed_domains = ['ligafarmacia.cl']
    start_urls = ['https://ligafarmacia.cl']
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Uncomment for headless execution
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.categories = [
            'medicamentos'           
            ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        self.driver.get(response.url)
        base_url = 'https://ligafarmacia.cl/'
        time.sleep(5)  # Wait for JavaScript to load contents
        for category in self.categories:
            url = f"{base_url}{category}"
            self.driver.get(url)
            time.sleep(5)  # Wait for JavaScript to load contents
            
            # Selecciona el máximo número de resultados por página
            
            #self.select_max_results_per_page()
            while True:
                try:
                    products = self.driver.find_elements(By.XPATH, "//div[@class='product-wrap mb-25']")
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

                '''self.scroll_to_pagination()

                next_page_button = self.get_next_page_button()
                if next_page_button:
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable(next_page_button)
                        )
                        self.driver.execute_script("arguments[0].click();", next_page_button)
                        time.sleep(5)  # Wait for the page to load
                    except Exception as e:
                        print(f"Error clicking next page button: {str(e)}")
                        break
                else:
                    print("No more pages to navigate.")
                    break'''

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
        price_benef = '0'  # Adjust this XPath to retrieve benefit price if available
        price_sale = '0'  # Adjust this XPath to retrieve benefit price if available
        sku = '0' # Adjust this XPath to retrieve sku price if available
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

    def get_next_page_button(self):
        try:
            active_page = self.driver.find_element(By.XPATH, "//li[@class='page-item active']")
            next_page = active_page.find_element(By.XPATH, "following-sibling::li[1]//a")
            return next_page
        except NoSuchElementException:
            return None
    '''
    def closed(self, reason):
        self.driver.quit()
