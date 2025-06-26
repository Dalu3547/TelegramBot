from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re

import logging

logger = logging.getLogger(__name__)

class KaspiParser:
    
    def __init__(self):
        logger.info("Инициализация Kaspi парсера")
        
    
    def _setup_driver(self) -> webdriver.Chrome:
        options = Options()
        
        options.add_argument("--no-sandbox")                           # Отключает sandbox
        options.add_argument("--disable-dev-shm-usage")                # Использует /tmp вместо /dev/shm
        options.add_argument("--disable-blink-features=AutomationControlled")  # Скрывает автоматизацию
        options.add_experimental_option("excludeSwitches", ["enable-automation"])  # Убирает флаги автоматизации
        options.add_experimental_option('useAutomationExtension', False)  # Отключает расширение автоматизации
        
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Запуск в фоновом режиме (без открытия окна браузера)
        options.add_argument("--headless")
        
        driver = webdriver.Chrome(options=options)
        
        # Дополнительно скрываем признаки автоматизации
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def parse_product(self, url: str):
        driver = None
        
        try:
            logger.info(f"Начинаем парсинг товара: {url}")
            
            if "kaspi.kz" not in url:
                logger.error("Ссылка не является ссылкой на Kaspi.kz")
                return None, None
            
            driver = self._setup_driver()
            
            driver.get(url)
            logger.info("Загружаем страницу...")
            
            time.sleep(3)
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            price = self._extract_price(driver)
            logger.info(f"Найденная цена: {price}")
            
            title = self._extract_title(driver)
            logger.info(f"Найденное название: {title}")
            
            return price, title
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге {url}: {str(e)}")
            return None, None
            
        finally:
            if driver:
                driver.quit()
                logger.info("Браузер закрыт")
    
    def _extract_price(self, driver):
        price_selectors = [
            '.item__price-once',
            '[class*="price"]',
            '.item__price',
        ]
        
        for selector in price_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    text = element.text.strip()
                    
                    if '₸' in text:
                        # Извлекаем числа из текста
                        price_match = re.search(r'([\d\s]+)', text.replace('₸', '').strip())
                        
                        if price_match:
                            price_str = price_match.group(1).replace(' ', '')
                            
                            if price_str.isdigit():
                                price = float(price_str)
                                logger.info(f"Цена найдена селектором '{selector}': {price}")
                                return price
                                
            except Exception as e:
                logger.warning(f"Ошибка с селектором '{selector}': {e}")
                continue
        
        logger.warning("Цена не найдена")
        return None
    
    def _extract_title(self, driver):
        title_selectors = [
            'h1',
            '.item__title',
            '[class*="title"]'
        ]
        
        for selector in title_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                title = element.text.strip()
                
                if title:
                    logger.info(f"Название найдено селектором '{selector}': {title[:50]}...")
                    return title
                    
            except Exception as e:
                logger.warning(f"Ошибка с селектором '{selector}': {e}")
                continue
        
        logger.warning("Название не найдено")
        return None
    

if __name__ == "__main__":
    parser = KaspiParser()

    url = "https://kaspi.kz/shop/p/apple-iphone-14-128gb-chernyi-102298404/?c=750000000" 

    price, title = parser.parse_product(url)

    if price and title:
        print(f"Product: {title}")
        print(f"Price: {price} ₸")
    else:
        print("Failed to parse product details.")