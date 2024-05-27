import scrapy
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

class ProfarSpider(scrapy.Spider):
    name = 'profar'
    allowed_domains = ['profar.cl']
    #start_urls = ['https://www.profar.cl/medicamentos','https://www.profar.cl/dermocosmetica', 'https://www.profar.cl/belleza', 'https://www.profar.cl/cuidado-personal', 'https://www.profar.cl/salud-animal']
    start_urls = ['https://www.profar.cl/dermocosmetica']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        self.driver.get(response.url)
        try:
            while True:
                # Scroll suavemente hacia abajo para simular el comportamiento humano
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                time.sleep(random.uniform(0.5, 2))  # Pausa aleatoria para emular la lectura humana

                try:
                    load_more_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'pa0 lh-solid br2 min-h-small')]"))
                    )
                    # Scroll hasta el botón antes de intentar hacer clic
                    ActionChains(self.driver).move_to_element(load_more_button).perform()
                    time.sleep(random.uniform(0.5, 1.5))  # Breve pausa antes de hacer clic
                    load_more_button.click()
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].click();", load_more_button)
                except TimeoutException:
                    break  # Salir del bucle si el botón no está presente

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
                    'product_prescription': product_prescription
                }

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
