# На сайте нет фильтра по particular, поэтому фильтр реализуется принципом "Нет логотипа компании - значит частное лицо"
# Собрать данные из каталога не получится, поэтому в обоих случаях алгоритм сбора данных одинаковый

import re
import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from database import insert_data


options = webdriver.ChromeOptions()
options.add_argument(f"user-agent={UserAgent().chrome}")
options.add_argument("--disable-blink-features=AutomationControlled")
timeout = 60

domain = "https://www.idealista.com"
card_class = re.compile(r"^item.*")
errors = 0


def get_response(browser, url):
    for _ in range(5):
        try:
            browser.get(url)
            time.sleep(0.2)
            response = browser.page_source
            if response and len(response) > 0:
                return response
        except TimeoutException:
            continue
    return None


def get_link_from_site(browser, start_url, mode):
    global errors
    links = list()
    response = get_response(browser=browser, url=start_url)
    if response is None:
        print("[ERROR] Ошибка сервера, невозможно получить доступ")
        errors += 1
        return False
    bs_object = BeautifulSoup(response, "lxml")
    card_id = bs_object.find(name="article", class_=card_class)["data-adid"]
    check_link = f"https://www.idealista.com/inmueble/{card_id}/"
    page = 0
    while True:
        page += 1
        url = f"{start_url}pagina-{page}.htm"
        response = get_response(browser=browser, url=url)
        if response is None:
            print("[ERROR] Ошибка сервера, пробуем еще раз")
            errors += 1
            page -= 1
        else:
            bs_object = BeautifulSoup(response, 'lxml')
            card_id = bs_object.find(name="article", class_=card_class)
            if card_id is None:
                errors += 1
                page -= 1
            else:
                card_id = card_id["data-adid"]
                current_link = f"https://www.idealista.com/inmueble/{card_id}/"
                if current_link == check_link and page != 1:
                    break
                cards = bs_object.find_all(name="article", class_=card_class)
                if mode == "buy":
                    cards_ids = [card["data-adid"] for card in cards]
                    cards_links = [f"https://www.idealista.com/inmueble/{card_id}/" for card_id in cards_ids]
                    links.extend(cards_links)
                    print(*cards_links, sep="\n")
                else:
                    for card in cards:
                        logo = card.find(name="picture", class_='logo-branding')
                        if logo is None:
                            card_id = card["data-adid"]
                            card_link = f"https://www.idealista.com/inmueble/{card_id}/"
                            links.append(card_link)
                            print(card_link)
                print(f"[INFO] Данные со страницы {url} собраны")

    return set(links)


def get_info_from_object(browser, url, object_type, mode):
    response = get_response(browser=browser, url=url)
    bs_object = BeautifulSoup(response, "lxml")
    if mode == "rent" and "particular" not in bs_object.text.lower():
        return "Invalid"
    card = bs_object.find(name="main", class_="detail-container")
    if card is None:
        return False
    image_url = card.img
    if image_url is not None:
        image_url = image_url["src"]
    else:
        image_url = "No information"
    title = card.find(name="div", class_="main-info__title").h1.text.strip()
    price = card.find(name="span", class_='info-data-price').text.strip()
    description = card.find(name="div", class_='comment')
    if description is not None:
        description = description.text.strip()
    else:
        description = "No information"
    characteristics = card.find(name="div", class_='details-property-feature-one').ul.find_all(name="li")
    square, bedrooms, bathes = "No information", "No information", "No information"
    for characteristic in characteristics:
        if "m²" in characteristic.text:
            square = characteristic.text.strip()
        elif "habitaciones" in characteristic.text:
            bedrooms = characteristic.text.strip()
        elif "baños" in characteristic.text:
            bathes = characteristic.text.strip()

    result = {"title": title, "object_type": object_type, "price": price, "square": square, "bedrooms": bedrooms,
              "bathes": bathes, "description": description, "url": url, "image_url": image_url}
    return result


def get_mode(url):
    if "alquiler" in url:
        mode = "rent"
    else:
        mode = "buy"
    return mode


def get_object_type(url):
    if "pisos" in url or "aticos" in url or "lofts" in url:
        object_type = "Piso"
    else:
        object_type = "Casa"
    return object_type


def get_info_from_link(browser, link, mode, object_type):
    try:
        print(f"[INFO] Идет сбор информации со страницы {link}")
        sub_result = get_info_from_object(browser=browser, url=link, object_type=object_type, mode=mode)
        if sub_result == "Invalid":
            print(f"[INFO] Объект {link} не подходит по условиям фильтрации")
            return False
        elif sub_result:
            print(f"[INFO] Данные собраны со страницы {link}")
            return sub_result
        else:
            print(f"[ERROR] Не удалось собрать данные со страницы {link}")
            return False
    except KeyError:
        print(f"[ERROR] При сборе данных на странице {link} произошла ошибка. Пробуем еще раз")
        for index in range(5):
            try:
                print(f"[INFO] Идет сбор информации со страницы {link}")
                sub_result = get_info_from_object(browser=browser, url=link, object_type=object_type, mode=mode)
                if sub_result:
                    print(f"[INFO] Данные собраны со страницы {link}")
                    return sub_result
                else:
                    print(f"[ERROR] Не удалось собрать данные со страницы {link}")
                    return False
            except KeyError:
                continue
        return False


def main():
    result = list()
    proxy_server = input('Введите прокси сервер в формате (127.0.0.1:8080): ')
    example = "https://www.idealista.com/alquiler-viviendas/malaga-malaga/con-solo-pisos,aticos/"
    text = "Выберете город и укажите фильтры поиска на сайте idealista.com."
    input_text = f"{text}\nВставьте полученный URL ({example}):\n[INPUT] >>>   "
    url = input(input_text).strip()
    print("[INFO] Не уходите далеко. Нужно будет еще пройти капчу")
    mode = get_mode(url=url)
    object_type = get_object_type(url=url)
    options.add_argument(f"--proxy-server={proxy_server}")
    browser = webdriver.Chrome(options=options)
    browser.set_page_load_timeout(timeout)
    try:
        browser.get(url=url)
        print("[INFO] Пройдите капчу и введите YES")
        input("[INPUT] >>>   ")
        start_time = time.time()
        links = get_link_from_site(browser=browser, start_url=url, mode=mode)
        for link in links:
            sub_result = get_info_from_link(browser=browser, link=link, mode=mode, object_type=object_type)
            if sub_result:
                result.append(sub_result)

        print(f"[INFO] Собрано {len(result)} объектов")
        print("[INFO] Идет запись в базу данных")
        insert_data(objects=result)
        stop_time = time.time()
        print(f"[INFO] На работу программы потребовалось {stop_time - start_time} секунд")
        print(f"[INFO] Количество ошибок сервера: {errors}")
    finally:
        browser.close()
        browser.quit()


if __name__ == "__main__":
    main()
