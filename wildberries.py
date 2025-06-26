from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import logging
import time

logger = logging.getLogger(__name__)

class WildberriesParser:

    def __init__(self):
        logger.info("Инициализация парсера Wildberries")

    def _setup_driver(self) -> webdriver.Chrome:
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver

    def parse_product(self, url: str):
        driver = None
        try:
            logger.info(f"Начинаем парсинг товара: {url}")

            if "wildberries.ru" not in url.lower():
                logger.error("URL не является ссылкой на Wildberries")
                return None, None

            driver = self._setup_driver()

            driver.get("https://global.wildberries.ru")
            self._change_currency_to_kzt(driver)

            driver.get(url)
            logger.info("Ожидаем загрузку страницы товара...")
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            WebDriverWait(driver, 10).until(
                lambda d: "₸" in d.page_source
            )
            time.sleep(1)

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

    def _change_currency_to_kzt(self, driver):
        try:
            wait = WebDriverWait(driver, 15)

            currency_button = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.simple-menu__link--country"))
            )
            ActionChains(driver).move_to_element(currency_button).perform()
            logger.info("Навели мышку на меню валюты")
            time.sleep(1)

            kzt_label = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@name='currency' and @value='KZT']/parent::label"))
            )
            driver.execute_script("arguments[0].click();", kzt_label)
            logger.info("Клик по KZT выполнен")

            wait.until(lambda d: "₸" in d.page_source)

        except Exception as e:
            logger.error(f"Не удалось изменить валюту на KZT: {str(e)}", exc_info=True)
            with open("debug_currency_hover.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logger.warning("Сохранён HTML в debug_currency_hover.html")

    def _extract_price(self, driver):
        selectors = [
            "ins.price-block__final-price",
            '[class*="price"]',
        ]

        for selector in selectors:
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                text = element.text.strip()
                if '₸' in text:
                    logger.info(f"Цена найдена селектором '{selector}': {text}")
                    return text
            except Exception as e:
                logger.warning(f"Ошибка с селектором '{selector}': {e}")
                continue

        logger.warning("Цена не найдена")
        return None

    def _extract_title(self, driver):
        selectors = [
            "h1.product-page__title",
            '[class*="title"]'
        ]

        for selector in selectors:
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                text = element.text.strip()
                if text:
                    logger.info(f"Название найдено селектором '{selector}': {text[:50]}...")
                    return text
            except Exception as e:
                logger.warning(f"Ошибка с селектором '{selector}': {e}")
                continue

        logger.warning("Название не найдено")
        return None

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = WildberriesParser()
    url = "https://global.wildberries.ru/catalog/343068062/detail.aspx"
    price, title = parser.parse_product(url)

    if price and title:
        print(f"Product: {title}")
        print(f"Price: {price}")
    else:
        print("Failed to parse product details.")
