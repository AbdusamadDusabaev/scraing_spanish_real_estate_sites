# На сайте нет фильтра по particular, поэтому фильтр реализуется по условиям заказчика
# Если режим аренды, то скрипт заходит в карточки объектов.
# Если режим покупки, то информация берется из каталога объектов

import time
import requests
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from database import insert_data


headers = {"user-agent": UserAgent().chrome}
errors = 0
max_local_errors = 5
timeout = 5


def get_response(url):
    global errors
    local_errors = 0
    while True:
        try:
            response = requests.get(url=url, headers=headers, timeout=timeout)
            break
        except ConnectTimeout:
            errors += 1
            local_errors += 1
            print(f"[ERROR] Сервер не дает ответ более {timeout} секунд на странице {url}")
            if local_errors == max_local_errors:
                print(f"[ERROR] Превышено максимальное количество попыток ({max_local_errors})")
                return False
            else:
                print("[INFO] Пробуем еще раз")
        except ConnectionError:
            errors += 1
            local_errors += 1
            print(f"[ERROR] Ошибка подключения на странице {url}")
            if local_errors == max_local_errors:
                return False
            else:
                print("[INFO] Пробуем еще раз")
        except ReadTimeout:
            errors += 1
            local_errors += 1
            print(f"[ERROR] Сервер выдал сломанные данные на странице {url}")
            if local_errors == max_local_errors:
                return False
            else:
                print("[INFO] Пробуем еще раз")

    return response


def get_data_from_site(start_url, object_type, mode):
    result = list()
    response = requests.get(url=start_url, headers=headers)
    bs_object = BeautifulSoup(response.content, "lxml")
    max_page = bs_object.find(name="div", class_="w-100 bg-white margin-y pagination")
    max_page = int(max_page.find_all(name="li")[-3].text.strip())
    for page in range(0, max_page):
        index = start_url.index(".htm")
        url = f"{start_url[:index]}-{page}{start_url[index:]}"
        print(f"[INFO] Идет сбор со страницы {url}")
        response = get_response(url=url)
        bs_object = BeautifulSoup(response.content, "lxml")
        cards = bs_object.find_all(name="article",
                                   class_="js-list-item list-item-container js-item-with-link gtmproductclick")
        for card in cards:
            title = card.h3.text.strip()
            link = card.h3.a["href"]
            image_url = "https:" + card.find(name="div", class_="image").img["src"]
            description = card.find(name="p", class_="list-item-description").text.strip()

            price = card.find(name="span", itemprop="price")
            if price is not None:
                price = price.text.strip()
            else:
                price = "No information"

            characteristics = card.find(name="p", class_="list-item-feature").text.strip().split("-")
            if len(characteristics) == 4:
                square = characteristics[0].strip()
                bedrooms = characteristics[1].strip()
                bathes = characteristics[2].strip()
            elif len(characteristics) == 3:
                square = characteristics[0].strip()
                bedrooms = characteristics[1].strip()
                bathes = "No information"
            elif len(characteristics) == 2:
                square = characteristics[0].strip()
                bedrooms = "No information"
                bathes = "No information"
            else:
                square = "No information"
                bedrooms = "No information"
                bathes = "No information"

            sub_result = {"mode": mode, "title": title, "object_type": object_type, "price": price,
                          "square": square, "bedrooms": bedrooms, "bathes": bathes, "description": description,
                          "url": url, "image_url": image_url}
            result.append(sub_result)
            print(f"[INFO] Получен объект: {sub_result}")
    return result


def get_links_from_site(start_url):
    links = list()
    response = requests.get(url=start_url, headers=headers)
    bs_object = BeautifulSoup(response.content, "lxml")
    max_page = bs_object.find(name="div", class_="w-100 bg-white margin-y pagination")
    max_page = int(max_page.find_all(name="li")[-3].text.strip())
    for page in range(0, max_page):
        index = start_url.index(".htm")
        url = f"{start_url[:index]}-{page}{start_url[index:]}"
        response = get_response(url=url)
        bs_object = BeautifulSoup(response.content, "lxml")
        cards = bs_object.find_all(name="div", class_="list-item")
        card_links = [card.h3.a["href"] for card in cards]
        links.extend(card_links)
        print(f"[INFO] Страница {url} обработана")
    return set(links)


def get_info_from_object(url, object_type, mode):
    response = get_response(url=url)
    if response:
        bs_object = BeautifulSoup(response.content, "lxml")
        logo = bs_object.find(name="aside", id="js-contact-top").img
        if logo is None:
            title = bs_object.h1.text.strip()
            price = bs_object.find(name="div", class_='price').find(name="span", class_="font-2").text.strip()
            characteristics = bs_object.find(name="article", id='js-feature-container').ul.find_all(name="li")
            if len(characteristics) == 0:
                square = "No information"
                bedrooms = "No information"
                bathes = "No information"
            elif len(characteristics) < 3:
                square = characteristics[0].text.strip()
                bedrooms = "No information"
                bathes = "No information"
            else:
                square = characteristics[0].text.strip()
                bedrooms = characteristics[1].text.strip()
                bathes = characteristics[2].text.strip()

            description = bs_object.find(name="article", id="js-translate").p.text.strip()
            image_url = bs_object.find(name="div", id="js-cover-less")
            if image_url is None:
                image_url = "No information"
            else:
                image_url = image_url.find(name="img", class_="print-xl")["src"]

            result = {"mode": mode, "title": title, "object_type": object_type, "price": price,
                      "square": square, "bedrooms": bedrooms, "bathes": bathes,
                      "description": description, "url": url, "image_url": image_url}

            return result


def get_object_type(url):
    if "pisos" in url or "aticos" in url:
        object_type = "Piso"
    else:
        object_type = "Casa"
    return object_type


def get_mode(url):
    if "alquiler" in url:
        mode = "rent"
    else:
        mode = "buy"
    return mode


def correct_url(url):
    if url[-1] != "/":
        url = f"{url}/"
    return url


def main():
    example = "https://www.habitaclia.com/pisos-en-alt_penedes.htm"
    text = "Выберете город и укажите фильтры поиска на сайте habitaclia.com."
    input_text = f"{text} Вставьте полученный URL ({example}):\n[INPUT] >>>   "
    url = input(input_text).strip()
    url = correct_url(url=url)
    start_time = time.time()
    print("[INFO] Программа запущена")
    object_type = get_object_type(url)
    mode = get_mode(url)

    if mode == "rent":
        result = list()
        links = get_links_from_site(start_url=url)
        for link in links:
            print(f"[INFO] Обрабатывается страница {link}")
            sub_result = get_info_from_object(url=link, object_type=object_type, mode=mode)
            if sub_result is not None:
                print(f"[INFO] Получен объект: {sub_result}")
                result.append(sub_result)
    else:
        result = get_data_from_site(start_url=url, object_type=object_type, mode=mode)
    print(f"[INFO] Программа собрала {len(result)} объектов")
    print("[INFO] Идет запись в базу данных")
    insert_data(objects=result)
    stop_time = time.time()
    print(f"[INFO] На работу программы потребовалось {stop_time - start_time} секунд")
    print(f"[INFO] Количество ошибок сервера: {errors}")


if __name__ == "__main__":
    main()
