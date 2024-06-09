import scrapy
import time
import random
from urllib.parse import urlparse, unquote, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

class ProfarSpider(scrapy.Spider):
    name = 'profar'
    allowed_domains = ['profar.cl']
    #start_urls = ['https://www.profar.cl/medicamentos','https://www.profar.cl/dermocosmetica', 'https://www.profar.cl/belleza', 'https://www.profar.cl/cuidado-personal', 'https://www.profar.cl/salud-animal']
    #start_urls = ['https://www.profar.cl/belleza', 'https://www.profar.cl/cuidado-personal', 'https://www.profar.cl/salud-animal']
    start_urls = ['https://www.profar.cl/cuidado-personal']
    '''
    start_urls = [
        'https://www.profar.cl/medicamentos/Antibioticos-y-Antivirales', 
        'https://www.profar.cl/medicamentos/Antidiabeticos-y-Tiroides', 
        'https://www.profar.cl/medicamentos/bienestar-sexual',
        'https://www.profar.cl/medicamentos/Cardiovascular', 
        'https://www.profar.cl/medicamentos/Coagulacion', 
        'https://www.profar.cl/medicamentos/dermatologicos', 
        'https://www.profar.cl/medicamentos/Dolor-y-Fiebre', 
        'https://www.profar.cl/medicamentos/Enfermedades-especificas', 
        'https://www.profar.cl/medicamentos/Gastrointestinal',
        'https://www.profar.cl/medicamentos/Huesos-y-Articulaciones', 
        'https://www.profar.cl/medicamentos/Oftalmicos-y-Oidos', 
        'https://www.profar.cl/medicamentos/Respiratorio', 
        'https://www.profar.cl/medicamentos/Salud-Femenina', 
        'https://www.profar.cl/medicamentos/Salud-Masculina', 
        'https://www.profar.cl/medicamentos/Vacunas', 
        'https://www.profar.cl/medicamentos/Vitaminas-y-Minerales', 
        'https://www.profar.cl/medicamentos/Otros'
    ]
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ua = UserAgent()
        options = Options()
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(f'user-agent={self.ua.random}')
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def start_requests(self):
        for url in self.start_urls:
            user_agent = self.ua.random  # Get a new user agent for each request
            self.driver.execute_script(f"navigator.__defineGetter__('userAgent', function(){{return '{user_agent}';}});")
            yield scrapy.Request(url=url, callback=self.parse, meta={'page_count': 0, 'user_agent': user_agent})

    def parse(self, response):
        self.driver.get(response.url)
        category = urlparse(response.url).path.lstrip('/').replace('https://www.profar.cl/', '')
        page_count = response.meta['page_count']
        click_count = 0

        try:
            while click_count < 5:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                time.sleep(random.uniform(0.5, 2))

                try:
                    load_more_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'pa0 lh-solid br2 min-h-small')]"))
                    )
                    load_more_button.click()  # Direct click without ActionChains
                    click_count += 1
                    time.sleep(random.uniform(0.5, 1.5))  # Wait a bit before the next operation
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].click();", load_more_button)
                except TimeoutException:
                    break

            sections = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//section[contains(@class, 'product-summary')]"))
            )
            for section in sections:
                product_name = self.get_text_or_default(section, ".//article//div[12]//span")
                selling_price = self.get_text_or_default(section, ".//article//div[14]//span[contains(@class,'sellingPriceValue')]")
                list_price = self.get_text_or_default(section, ".//article//div[14]//span[contains(@class,'listPriceValue')]")
                product_url = self.get_attribute_or_default(section, ".//a", 'href')
                product_prescription = self.get_text_or_default(section, ".//article//div[13]//span")

                yield {
                    'product_name': product_name,
                    'selling_price': selling_price,
                    'list_price': list_price,
                    'product_url': product_url,
                    'product_prescription': product_prescription,
                    'category': category
                }

            if click_count == 5:
                next_page = urljoin(response.url, f"?page={page_count + 5}")
                yield scrapy.Request(url=next_page, callback=self.parse, meta={'page_count': page_count + 5})

        except TimeoutException:
            self.logger.error("Tiempo de espera excedido para la carga de la página")
        finally:
            self.driver.quit()

    def get_text_or_default(self, element, xpath, default='No disponible'):
        try:
            return element.find_element(By.XPATH, xpath).text
        except NoSuchElementException:
            return default

    def get_attribute_or_default(self, element, xpath, attribute, default='No disponible'):
        try:
            return element.find_element(By.XPATH, xpath).get_attribute(attribute)
        except NoSuchElementException:
            return default
