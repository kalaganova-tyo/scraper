import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import datetime
from model import Car


def scrape_with_selenium(url):
    # Настройка Chrome
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)

    try:
        driver.get(url)
        time.sleep(5)

        # Закрываем всплывающие окна
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Закрыть') or contains(@class, 'popup-close')]"))
            ).click()
        except:
            pass

        # Ожидаем загрузки карточек
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'iva-item-root')]"))
        )

        cars = driver.find_elements(By.XPATH, "//div[contains(@class, 'iva-item-root')]")
        print(f'Найдено объявлений: {len(cars)}')

        engine = create_engine('sqlite:///cars.db')
        Session = sessionmaker(bind=engine)
        session = Session()

        for car in cars:
            try:
                title = car.find_element(By.XPATH, ".//div[contains(@class, 'iva-item-title-CdRX')]").text
                price = car.find_element(By.XPATH, ".//span[contains(@class, 'price-root-IfnJI')]").text

                new_car = Car(
                    title=title,
                    price=price,
                    datetime=datetime.datetime.now()  # Исправлено: передаем datetime объект
                )
                session.add(new_car)

            except Exception as e:
                print(f"Ошибка при обработке карточки: {e}")
                continue

        session.commit()
        session.close()

    except Exception as e:
        print(f"Ошибка в основном потоке: {e}")
    finally:
        driver.quit()


if __name__ == '__main__':
    # Создаем структуру БД
    from sqlalchemy import create_engine
    from model import Base

    engine = create_engine('sqlite:///cars.db')
    Base.metadata.create_all(engine)

    # Запускаем парсинг
    target_url = 'https://www.avito.ru/moskva/avtomobili/hyundai/solaris-ASgBAgICAkTgtg2imzHitg3kmzE?cd=1&radius=0&searchRadius=0'
    scrape_with_selenium(target_url)