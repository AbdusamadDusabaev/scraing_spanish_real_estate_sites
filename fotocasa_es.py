# На сайте нет фильтра по particular, поэтому фильтр реализуется принципом "Нет логотипа компании - значит частное лицо"
# Собрать данные из каталога возможно в обоих случаях

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import time
import re
from database import insert_data


options = webdriver.ChromeOptions()
options.add_argument(f"user-agent={UserAgent().chrome}")
options.add_argument("--headless")

timeout = 60
domain = "https://www.fotocasa.es"
card_class = re.compile(r"^re-CardPack.*")
title_class = re.compile(r"^re-CardTitle.*")
description_class = re.compile(r"^re-CardDescription.*")
characteristics_class = re.compile(r"^re-CardFeatures.*")


def get_response_from_catalog_page(browser, url):
    for _ in range(5):
        try:
            browser.get(url)
            start = 0
            stop = 1080
            for scroll in range(20):
                browser.execute_script(f"window.scrollTo({start}, {stop})")
                time.sleep(0.1)
                start += 1080
                stop += 1080
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            response = browser.page_source
            if response and len(response) > 0:
                return response
        except TimeoutException:
            continue
    return None


def get_info_from_site(start_url, mode, object_type):
    browser = webdriver.Chrome(options=options)
    browser.set_page_load_timeout(timeout)
    result = list()
    try:
        browser.get(url=start_url)
        accept_with_cookie = browser.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/div/footer/div/button[2]")
        accept_with_cookie.click()
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        response = browser.page_source
        bs_object = BeautifulSoup(response, "lxml")
        max_page = int(bs_object.find_all(name="li", class_='sui-MoleculePagination-item')[-2].text.strip())
        page = 1
        while page <= max_page:
            if "?" in start_url:
                index = start_url.index("?")
                url = f"{start_url[:index]}/{page}{start_url[index:]}"
            else:
                if start_url[-1] == '/':
                    url = f"{start_url}{page}"
                else:
                    url = f"{start_url}/{page}"
            page += 1
            response = get_response_from_catalog_page(browser=browser, url=url)
            if response is not None:
                try:
                    bs_object = BeautifulSoup(response, "lxml")
                    cards = bs_object.find_all(name="article", class_=card_class)
                    for card in cards:
                        link = domain + card.a["href"]
                        image_url = card.find(name="img", class_="re-CardMultimediaSlider-image")["src"]
                        title = card.h3.find(name="span", class_=title_class).text.strip()
                        price = card.h3.find(name="span", class_="re-CardPriceContainer").text.strip()
                        description = card.find(name="p", class_=description_class).text.strip()

                        bedrooms, bathes, square = "No information", "No information", "No information"
                        characteristics = card.find(name="ul", class_=characteristics_class).find_all(name="li")
                        for characteristic in characteristics:
                            if "baños" in characteristic.text.strip():
                                bathes = characteristic.text.strip()
                            elif "habs" in characteristic.text.strip():
                                bedrooms = characteristic.text.strip()
                            elif "m²" in characteristic.text.strip():
                                square = characteristic.text.strip()

                        sub_result = {"title": title, "object_type": object_type, "price": price, "square": square,
                                      "bedrooms": bedrooms, "bathes": bathes, "description": description,
                                      "url": link, "image_url": image_url}

                        if mode == "rent":
                            logo = card.find(name="a", class_="re-CardPromotionLogo-link")
                            if logo is None:
                                result.append(sub_result)
                                print(sub_result)
                        else:
                            result.append(sub_result)
                            print(sub_result)
                    print(f"[INFO] Страница {url} обработана")
                except AttributeError as ex:
                    print(ex)
                    page -= 1
            else:
                print(f"[ERROR] Не удалось получить ответ от страницы {url}")

        correct_result = list()
        for element in result:
            if element not in correct_result:
                correct_result.append(element)
        return correct_result
    finally:
        browser.close()
        browser.quit()


def get_mode(url):
    if "alquiler" in url:
        mode = "rent"
    else:
        mode = "buy"
    return mode


def get_object_type(url):
    if ("apartamentos" in url or "estudios" in url or "propertySubtypeIds=2" in url or "propertySubtypeIds=6" in url
       or "propertySubtypeIds=54" in url or "aticos" in url or "lofts" in url or "propertySubtypeIds=8"):
        object_type = "Piso"
    else:
        object_type = "Casa"
    return object_type


def main():
    example = "https://www.fotocasa.es/es/alquiler/viviendas/malaga-provincia/todas-las-zonas/l?propertySubtypeIds=54"
    text = "Выберете город и укажите фильтры поиска на сайте fotocasa.es."
    input_text = f"{text} Вставьте полученный URL ({example}):\n[INPUT] >>>   "
    url = input(input_text).strip()
    start = time.time()
    print("[INFO] Программа запущена")
    mode = get_mode(url=url)
    object_type = get_object_type(url=url)
    result = get_info_from_site(start_url=url, mode=mode, object_type=object_type)
    print(f"[INFO] Программа собрала {len(result)} объектов")
    print("[INFO] Идет запись объектов в базу данных")
    insert_data(objects=result)
    stop = time.time()
    print(f"[INFO] Программа работала {stop - start} секунд")


if __name__ == "__main__":
    main()
