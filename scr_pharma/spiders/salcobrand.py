import json
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class SalcobrandSpider(scrapy.Spider):
    name = 'salcobrand'
    allowed_domains = ['salcobrand.cl', 'gm3rp06hjg-dsn.algolia.net']
    start_urls = ['https://salcobrand.cl/t/medicamentos']
    api_base_url = 'https://gm3rp06hjg-dsn.algolia.net/1/indexes/*/queries'
    api_params = '?x-algolia-agent=Algolia%20for%20JavaScript%20(4.14.3)%3B%20Browser%20(lite)&x-algolia-api-key=0259fe250b3be4b1326eb85e47aa7d81&x-algolia-application-id=GM3RP06HJG'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        #chrome_options.add_argument("--headless")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def start_requests(self):
        self.driver.get(self.start_urls[0])
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}
        self.driver.quit()
        yield scrapy.Request(f"{self.api_base_url}{self.api_params}&page=0", cookies=cookies, callback=self.parse_api)

    def parse_api(self, response):
        data = json.loads(response.text)
        for hit in data['results'][0]['hits']:
            yield {
                'id': hit['id'],
                'name': hit['name'],
                'brand': hit['brand'],
                'price': hit['normal_price'],
                'image_url': hit['catalog_image_url']
            }
        # Check for more pages
        if 'nbPages' in data['results'][0] and data['results'][0]['page'] < data['results'][0]['nbPages'] - 1:
            next_page = data['results'][0]['page'] + 1
            yield scrapy.Request(f"{self.api_base_url}{self.api_params}&page={next_page}", callback=self.parse_api)

    def closed(self, reason):
        # Clean up Selenium driver
        if self.driver.service.is_running:
            self.driver.quit()
