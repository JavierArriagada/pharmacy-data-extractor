# farmex_spider.py

import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import time
from scrapy.loader import ItemLoader
from datetime import datetime
from ..items import ScrPharmaItem  # Asegúrate de que la ruta es correcta

class FarmexSpider(scrapy.Spider):
    name = 'farmex'
    allowed_domains = ['farmex.cl']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        options = Options()
        options.headless = True
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.categories = ['analgesicos']

    def start_requests(self):
        yield scrapy.Request(url='https://farmex.cl', callback=self.parse, dont_filter=True)

    def parse(self, response):
        self.driver.get(response.url)
        for category in self.categories:
            start_page = 1
            while True:
                url = f"https://farmex.cl/collections/{category}?page={start_page}"
                self.driver.get(url)
                time.sleep(3)  # Wait for JavaScript to load contents

                # Utilizamos BeautifulSoup para parsear el HTML
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                script = soup.find('script', text=lambda t: 'window.insider_object' in t)
                if not script:
                    print(f"No more items found for category {category}, moving to next category.")
                    break

                # Extraemos y procesamos la información del script
                json_text = script.string.split('window.insider_object =')[1].strip().rstrip(';')
                data = json.loads(json_text)
                items = data['listing']['items']

                if not items:
                    break

                for item in items:
                    loader = ItemLoader(item=ScrPharmaItem(), response=response)
                    loader.add_value('name', item['name'])
                    loader.add_value('url', item['url'])
                    loader.add_value('category', category)
                    loader.add_value('price', item['unit_price'])
                    loader.add_value('price_sale', item['unit_sale_price'])
                    loader.add_value('timestamp', datetime.now())
                    loader.add_value('spider_name', self.name)
                    yield loader.load_item()

                start_page += 1

    def closed(self, reason):
        self.driver.quit()
