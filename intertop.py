from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import time

logger = logging.getLogger(__name__)

class IntertopParser:

    def __init__(self):
        logger.info("Инициализация Intertop парсера")

    def _setup_driver(self) -> webdriver.Chrome:
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--headless")

        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver

    def parse_product(self, url: str):
        driver = None

        try:
            logger.info(f"Начинаем парсинг товара: {url}")

            if "intertop.kz" not in url:
                logger.error("Ссылка не является ссылкой на Intertop.kz")
                return None, None

            driver = self._setup_driver()
            driver.get(url)
            logger.info("Загружаем страницу...")

            time.sleep(3)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            price = self._extract_price(driver)
            title = self._extract_title(driver)

            return price, title

        except Exception as e:
            logger.error(f"Ошибка при парсинге {url}: {str(e)}", exc_info=True)
            return None, None

        finally:
            if driver:
                driver.quit()
                logger.info("Браузер закрыт")

    def _extract_price(self, driver):
        price_selectors = [
            ".price-contain.current-price-value",
            ".price-value",  
            '[class*="price"]',
        ]

        for selector in price_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if "₸" in text:
                        return text
            except Exception as e:
                logger.warning(f"Ошибка с селектором '{selector}': {e}")
                continue

        logger.warning("Цена не найдена")
        return None

    def _extract_title(self, driver):
        title_selectors = [
            ".user-product-name",
            "h1",
            '[class*="title"]',
        ]

        for selector in title_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                title = element.text.strip()
                if title:
                    return title
            except Exception as e:
                logger.warning(f"Ошибка с селектором '{selector}': {e}")
                continue

        logger.warning("Название не найдено")
        return None


if __name__ == "__main__":
    parser = IntertopParser()
    url = "https://intertop.kz/ru-kz/product/boots-and-ankle-boots-boss-8340490"

    price, title = parser.parse_product(url)

    if price and title:
        print(f"Product: {title}")
        print(f"Price: {price}")
    else:
        print("Failed to parse product details.")
