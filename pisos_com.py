# На сайте нет фильтра по particular, поэтому фильтр реализуется принципом "Нет логотипа компании - значит частное лицо"
# Собрать данные из каталога не получится, поэтому в обоих случаях алгоритм сбора данных одинаковый

from fake_useragent import UserAgent
import requests
from requests.exceptions import ConnectTimeout, ConnectionError, ReadTimeout
from bs4 import BeautifulSoup
import time
import re
from database import insert_data, download_photo


domain = "https://www.pisos.com"
headers = {"user-agent": UserAgent().chrome}

timeout = 5
errors = 0
max_local_errors = 5

record_class_first = re.compile(r"^ad-preview .*")
records_class_second = "ad-preview"


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


def get_link_from_page(url, page, check_link):
    result = list()
    response = get_response(url=url)
    bs_object = BeautifulSoup(response.content, "lxml")

    if "No encontramos lo que buscas" in bs_object.text:
        return "break"

    current_check_link = bs_object.find(name="div", class_=record_class_first)["data-lnk-href"]
    if check_link == current_check_link and page != 1:
        return "break"

    records = bs_object.find_all(name="div", class_=record_class_first)
    records.extend(bs_object.find_all(name="div", class_=records_class_second))
    for record in records:
        sub_result = domain + record["data-lnk-href"]
        result.append(sub_result)
    print(f"[INFO] Программа собрала ссылки со страницы {page}")

    return result


def get_links_from_site(start_url):
    print("[INFO] Идет сбор ссылок...")
    page = 0
    response = requests.get(url=start_url, headers=headers)
    bs_object = BeautifulSoup(response.content, 'lxml')
    check_link = bs_object.find(name="div", class_=record_class_first)["data-lnk-href"]
    result = list()

    while True:
        page += 1
        url = f"{start_url}{page}/"
        sub_result = get_link_from_page(url=url, page=page, check_link=check_link)
        if sub_result == "break":
            break
        else:
            result.extend(sub_result)
    print("[INFO] Сбор ссылок закончен")
    print(f"[INFO] При сборе ссылок сервер выдал ошибку {errors} раз")
    print(f"[INFO] Программа собрала {len(set(result))} ссылок с сайта")

    return set(result)


def get_data_from_object(object_url, object_type, mode):
    response = get_response(url=object_url)
    if response:
        bs_object = BeautifulSoup(response.content, "lxml")
        logo = bs_object.find(name="img", class_="logo", title=True)
        if mode == "rent":
            if logo is None:
                check = True
            else:
                check = False
        else:
            check = True

        if check:
            title = bs_object.find(name="h1", class_="title")
            if title is not None:
                title = title.text.strip()
                price = bs_object.find(name="div", class_="priceBox-price").text.strip()
                description = bs_object.find(name="div", id="descriptionBody").text.strip()

                image_url = bs_object.find(name="img", id="mainPhotoPrint")
                if image_url is None:
                    image_url = "No information"
                    print(f"[INFO] У объекта {title} нет фотографии")
                    image_path = ""
                else:
                    image_url = image_url["data-source"].replace("https:https://", "https://")
                    image_path = download_photo(url=image_url, title=title)

                characteristics = bs_object.find_all(name="div", class_='basicdata-item')
                square = "No information"
                bedrooms = "No information"
                bathes = "No information"
                for characteristic in characteristics[:3]:
                    if "habs" in characteristic.text:
                        bedrooms = characteristic.text
                    elif "baños" in characteristic.text:
                        bathes = characteristic.text
                    elif "²" in characteristic.text:
                        square = characteristic.text
                    else:
                        continue
                if mode == "rent":
                    seller_type = "particular"
                else:
                    if logo is None:
                        seller_type = "particular"
                    else:
                        seller_type = "agency"

                result = {"mode": mode, "title": title, "object_type": object_type, "price": price,
                          "square": square, "bedrooms": bedrooms, "bathes": bathes, "description": description,
                          "url": object_url, "image_url": image_url, "seller_type": seller_type,
                          "image_path": image_path}

                return result


def get_mode(url):
    if "alquiler" in url:
        mode = "rent"
    else:
        mode = "buy"
    return mode


def get_object_type(url):
    if "piso-" in url or "aticos-" in url or "estudios-" in url or "lofts-" in url:
        object_type = "Piso"
    else:
        object_type = "Casa"
    return object_type


def correct_url(url):
    if url[-1] != "/":
        url = f"{url}/"
    return url


def main(url=None, without_delete=False):
    result = list()
    if url is None:
        example = "https://www.pisos.com/venta/duplexs-a_coruna/"
        text = "Выберете город и укажите фильтры поиска на сайте pisos.com."
        input_text = f"{text} Вставьте полученный URL ({example}):\n[INPUT] >>>   "
        url = input(input_text).strip()
        url = correct_url(url=url)
    start_time = time.time()
    print("[INFO] Программа запущена")
    object_type = get_object_type(url=url)
    mode = get_mode(url=url)
    links = get_links_from_site(start_url=url)
    for link in links:
        print(f"[INFO] Обрабатывается страница {link}")
        object_data = get_data_from_object(object_url=link, object_type=object_type, mode=mode)
        if object_data is not None:
            print(f"[INFO] Получен объект: {object_data}")
            result.append(object_data)
    print(f"[INFO] Программа собрала {len(result)} объектов")
    print("[INFO] Идет запись в базу данных")
    insert_data(objects=result, without_delete=without_delete)
    stop_time = time.time()
    print(f"[INFO] На работу программы потребовалось {stop_time - start_time} секунд")
    print(f"[INFO] Количество ошибок сервера: {errors}")


if __name__ == "__main__":
    main()
