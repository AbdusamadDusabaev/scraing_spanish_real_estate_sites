# На сайте есть фильтр по particular, поэтому дополнительную фильтрацию можно не применять
# В обоих случаях данные получаем из каталога объектов

import time
import requests
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from database import insert_data, download_photo


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
            if len(response.content) > 0:
                break
            else:
                errors += 1
                local_errors += 1
                if local_errors == max_local_errors:
                    print(f"[ERROR] Превышено максимальное количество попыток ({max_local_errors})")
                    return False
                else:
                    print("[INFO] Пробуем еще раз")
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


def get_info_from_site(start_url, object_type):
    page = 1
    result = list()
    url = f"{start_url}&page={page}"
    response = get_response(url=url)
    bs_object = BeautifulSoup(response.content, "lxml")
    max_page = int(bs_object.find(name="ul", class_='pagination pull-right').find_all(name="li")[-2].text.strip())

    for page in range(1, max_page + 1):
        url = f"{start_url}&page={page}"
        response = get_response(url=url)
        if response:
            bs_object = BeautifulSoup(response.content, "lxml")
            cards = bs_object.find_all(name="li", id=True)
            for card in cards:
                price = card.find(name="span", class_='propertyCard__price--value').text.strip().replace("\x80", " €")
                image_url = card.div.picture
                if image_url is None:
                    image_url = "No information"
                else:
                    image_url = image_url.find(name="source", attrs={"image-extension": "or"})["srcset"]
                characteristics = card.find(name="ul", class_="propertyCard__details").find_all(name="li")
                square = characteristics[0].text.strip()
                bedrooms = characteristics[1].text.strip()
                if bedrooms == "Piso":
                    bedrooms = "No information"
                if len(characteristics) > 2:
                    bathes = characteristics[2].text.strip()
                else:
                    bathes = "No information"
                title = card.find(name="div", class_='propertyCard__description hidden-xs').a.text.strip()
                object_url = card.find(name="div", class_='propertyCard__description hidden-xs').a["href"]
                description = card.find(name="p", class_='propertyCard__description--txt').text.strip()
                if image_url != "No information":
                    image_path = download_photo(url=image_url, title=title)
                else:
                    print(f"[INFO] У объекта {title} нет фотографии")
                    image_path = ""
                data = {"mode": "rent", "title": title, "object_type": object_type, "price": price,
                        "square": square, "bedrooms": bedrooms, "bathes": bathes, "description": description,
                        "url": object_url, "image_url": image_url, "seller_type": "particular",
                        "image_path": image_path}
                result.append(data)
                print(data)

            print(f"[INFO] Страница {url} обработана. Было собрано {len(cards)} объектов")

    return result


def get_object_type(url):
    if "tipo=2" in url or "tipo=6" in url or "tipo=3" in url or "tipo=5" in url:
        object_type = "Pico"
    else:
        object_type = "Casa"
    return object_type


def main(url=None, without_delete=False):
    if url is None:
        example = "https://www.enalquiler.com/search?tipo=2&query_string=Malaga"
        text = "Выберете город и укажите фильтры поиска на сайте enalquiler.com."
        input_text = f"{text} Вставьте полученный URL ({example}):\n[INPUT] >>>   "
        url = input(input_text).strip()
    object_type = get_object_type(url=url)
    start_time = time.time()
    result = get_info_from_site(start_url=url, object_type=object_type)
    print(f"[INFO] Программа собрала {len(result)} объектов")
    print("[INFO] Идет запись в базу данных")
    insert_data(objects=result, without_delete=without_delete)
    stop_time = time.time()
    print(f"[INFO] На работу программы потребовалось {stop_time - start_time} секунд")
    print(f"[INFO] Количество ошибок сервера: {errors}")


if __name__ == "__main__":
    main()
