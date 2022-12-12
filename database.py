import pathlib
import os
import shutil
import pymysql
from pymysql import cursors
from config import user, password, port, host, db_name, table_objects, table_urls
from fake_useragent import UserAgent
import requests


def create_photo_dir():
    if os.path.isdir("photos"):
        shutil.rmtree("photos")
        os.mkdir("photos")
    else:
        os.mkdir("photos")
    print("[INFO] Папка для фотографий photos успешно создана")


def correct_number(number):
    result = list()
    if len(number) > 0:
        for symbol in number:
            if symbol.isdigit():
                result.append(symbol)
        if len(result) > 0:
            result = int(("".join(result)).replace("²", ""))
        else:
            result = 0
        return result
    else:
        return 0


def correct_seller_type(seller_type):
    if seller_type == "particular":
        return 1
    else:
        return 0


def correct_mode(mode):
    if mode == "rent":
        return 1
    else:
        return 0


def correct_object_type(object_type):
    if object_type == "Piso":
        return 1
    else:
        return 0


def correct_text(text):
    text = text.replace('"', "'")
    return f'"{text}"'


def get_object_type(url):
    if "https://www.yaencontre.com/" in url:
        if "pisos" in url or "apartamentos" in url or "aticos" in url or "estudios" in url or "loft" in url:
            return 1
        else:
            return 0
    elif "https://www.pisos.com/" in url:
        if "piso-" in url or "aticos-" in url or "estudios-" in url or "lofts-" in url:
            return 1
        else:
            return 0
    elif "https://www.idealista.com/" in url:
        if "pisos" in url or "aticos" in url or "lofts" in url:
            return 1
        else:
            return 0
    elif "https://www.habitaclia.com/" in url:
        if "pisos" in url or "aticos" in url:
            return 1
        else:
            return 0
    elif "https://www.fotocasa.es/" in url:
        if ("apartamentos" in url or "estudios" in url or "propertySubtypeIds=2" in url or "propertySubtypeIds=6" in url
                or "propertySubtypeIds=54" in url or "aticos" in url or "lofts" in url or "propertySubtypeIds=8"):
            return 1
        else:
            return 0
    elif "https://www.enalquiler.com/" in url:
        if "tipo=2" in url or "tipo=6" in url or "tipo=3" in url or "tipo=5" in url:
            return 1
        else:
            return 0
    else:
        return "NULL"


def clean_photos():
    count = 0
    print("[INFO] Удаляем ненужные фотографии")
    favorite_photos = get_favorite_photos()
    for photo in os.listdir(path="photos"):
        path_to_photo = pathlib.Path("photos", photo)
        if photo not in favorite_photos:
            os.remove(path_to_photo)
            count += 1
    print("[INFO] Лишние фотографии удалены")
    print(f"[INFO] Было удалено {count} фотографий")


def get_seller_type(url):
    if "https://www.yaencontre.com/" in url:
        if "particular" in url:
            return 1
        else:
            return 0
    elif "https://www.enalquiler.com/" in url:
        return 1
    else:
        return "NULL"


def get_transaction_type(url):
    if "https://www.enalquiler.com/" not in url:
        if "alquiler" in url:
            return 1
        else:
            return 0
    else:
        return 1


def download_photo(url, title):
    url = url.replace("https:https://", "https://")
    correct_title = list()
    for symbol in title:
        if symbol.isalnum() or symbol == "-" or symbol == " ":
            correct_title.append(symbol)
    correct_title = "".join(correct_title)
    response = requests.get(url=url, headers={"user-agent": UserAgent().chrome})
    path = pathlib.Path("photos", f"{correct_title}.jpg")
    with open(path, "wb") as file:
        file.write(response.content)
    print(f"[INFO] Фотография объекта {title} успешно загружена")
    return f"{correct_title}.jpg"


def database(query, object_name=None):
    try:
        connection = pymysql.connect(port=port, host=host, user=user, password=password,
                                     database=db_name, cursorclass=cursors.DictCursor)
        try:
            cursor = connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            connection.commit()
            return result
        except Exception as ex:
            if "Duplicate entry" in str(ex):
                print(f"[INFO] Объект {object_name} дублируется в базе данных, поэтому он не будет записан")
            else:
                print(f"Something Wrong: {ex}")
            return "Error"
        finally:
            connection.close()
    except Exception as ex:
        print(f"Connection was not completed because {ex}")
        return "Error"


def get_urls():
    query = f"""SELECT * FROM {table_urls} WHERE active = 1;"""
    result = database(query=query)
    return result


def create_table_objects():
    query = f"""CREATE TABLE {table_objects.lower()} (favorite INT, transaction_type INT, 
    seller_type INT, title VARCHAR(500), object_type INT, price VARCHAR(50), square VARCHAR(50), 
    bedrooms VARCHAR(50), bathes VARCHAR(50), description VARCHAR(5000), url VARCHAR(500) UNIQUE, 
    image_url VARCHAR(500), image_title VARCHAR(500));"""
    database(query=query)
    print('[INFO] Таблица объектов недвижимости успешно создана')


def create_table_urls():
    query = f"""CREATE TABLE {table_urls.lower()} (url VARCHAR(500) UNIQUE, transaction_type INT, 
                                                   seller_type INT, object_type INT, active INT);"""
    database(query=query)
    print("[INFO] Таблица url-адресов успешно создана")


def get_favorite_photos():
    query = f"SElECT image_path FROM {table_objects} WHERE favorite = 1;"
    records = database(query=query)
    result = list()
    for record in records:
        result.append(record["image_path"])
    return result


def delete_data():
    query = f"""DELETE FROM {table_objects.lower()} WHERE favorite = 0;"""
    database(query=query)
    print("[INFO] База данных очищена")


def record_urls():
    with open("urls.txt", "r", encoding="utf-8") as file:
        urls_text = file.read()
    urls = urls_text.split("\n")
    for url in urls:
        if len(url) > 0:
            print(f"[INFO] Добавляем {url} базу данных")
            url = correct_text(text=url)
            transaction_type = get_transaction_type(url=url)
            seller_type = get_seller_type(url=url)
            object_type = get_object_type(url=url)
            active = 1
            query = f"""INSERT INTO {table_urls.lower()}(url, transaction_type, seller_type, object_type, active)
                        VALUES({url}, {transaction_type}, {seller_type}, {object_type}, {active});"""
            database(query=query, object_name=url)
    print("[INFO] Запись url-адресов успешно завершена")


def insert_data(objects, without_delete):
    if not without_delete:
        delete_data()
    for object_dict in objects:
        mode = correct_mode(mode=object_dict["mode"])
        seller_type = correct_seller_type(seller_type=object_dict["seller_type"])
        title = correct_text(text=object_dict["title"])
        object_type = correct_object_type(object_type=object_dict["object_type"])
        price = correct_number(number=object_dict["price"])
        square = correct_number(number=object_dict["square"])
        bedrooms = correct_number(number=object_dict["bedrooms"])
        bathes = correct_number(number=object_dict["bathes"])
        description = correct_text(text=object_dict["description"])
        url = correct_text(text=object_dict["url"])
        image_url = correct_text(text=object_dict["image_url"])
        if object_dict["image_path"] != "":
            image_path = f'"{object_dict["image_path"]}"'
        else:
            image_path = f'"У этого объекта нет фотографии"'
        query = f"""INSERT INTO {table_objects.lower()}(favorite, transaction_type, seller_type, title, object_type, 
                                                        price, square, bedrooms, bathes, description, url, 
                                                        image_url, image_title)
                    VALUES (0, {mode}, {seller_type}, {title}, {object_type}, {price}, {square}, 
                            {bedrooms}, {bathes}, {description}, {url}, {image_url}, {image_path});"""
        database(query=query, object_name=object_dict["title"])


if __name__ == "__main__":
    create_table_objects()
    create_table_urls()
    create_photo_dir()