import json
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import time

class LigaFarmaciaSpider(scrapy.Spider):
    name = 'ligafarmacia'
    allowed_domains = ['ligafarmacia.cl']
    start_urls = ['https://ligafarmacia.cl/medicamentos/']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Uncomment for headless execution
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def parse(self, response):
        self.driver.get(response.url)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            # Extract cookies and set them for subsequent requests
            cookies = self.driver.get_cookies()
            for cookie in cookies:
                self.driver.add_cookie(cookie)

            # Make an API call
            api_url = "https://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel?gsessionid=tor616kGmxDQJf-Bd4nv_GGshHOpEitSLmZFWywDduY&VER=8&database=projects%2Ffarmstore-744f9%2Fdatabases%2F(default)&RID=rpc&SID=7Ktx25Pmb_KxUOJ4T8k1KQ&AID=10&CI=1&TYPE=xmlhttp&zx=4ugg7ozfyql0&t=1"
            self.driver.get(api_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            data = json.loads(self.driver.find_element(By.TAG_NAME, 'body').text)

            # Process data from API
            for doc_change in data[1][1]:
                if 'documentChange' in doc_change:
                    doc = doc_change['documentChange']['document']
                    fields = doc['fields']
                    yield {
                        'sku': fields['sku']['arrayValue']['values'][0]['mapValue']['fields']['kinf2']['stringValue'],
                        'product_name': fields['sku']['arrayValue']['values'][0]['mapValue']['fields']['nombre_medicamento']['stringValue'],
                        'stock': fields['sku']['arrayValue']['values'][0]['mapValue']['fields']['stock']['integerValue'],
                        'descripcion': fields['sku']['arrayValue']['values'][0]['mapValue']['fields']['descripcion']['stringValue'],
                        'precio': fields['sku']['arrayValue']['values'][0]['mapValue']['fields']['precio']['integerValue']
                    }
        except Exception as e:
            self.logger.error(f"Error loading page: {str(e)}")
        finally:
            self.driver.quit()

    def closed(self, reason):
        if self.driver.service.is_running:
            self.driver.quit()
