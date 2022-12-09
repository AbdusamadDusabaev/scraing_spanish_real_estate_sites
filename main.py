from enalquiler_com import main as enalquiler
from fotocasa_es import main as fotocasa
from habitaclia_com import main as habitaclia
from idealista_com import main as idealista
from pisos_com import main as pisos
from yaencontre_com import main as yaencontre
from database import record_urls, get_urls, clean_photos, delete_data


variants = ["1 - парсер сайта enalquiler.com", "2 - парсер сайта fotocasa.es",
            "3 - парсер сайта habitaclia.com", "4 - парсер сайта idealista.com",
            "5 - парсер сайта pisos.com", "6 - парсер сайта yaencontre.com",
            "0 - Парсинг часто используемых url"]
parsers = {1: enalquiler, 2: fotocasa, 3: habitaclia, 4: idealista, 5: pisos, 6: yaencontre}


def parsing_urls():
    start_data = get_urls()
    for element in start_data:
        url = element["url"]
        if "https://www.pisos.com/" in url:
            print(f"[INFO] Парсер сайта pisos.com обрабатывает ссылку {url}")
            parsers[5](url=url, without_delete=True)
        elif "https://www.yaencontre.com/" in url:
            print(f"[INFO] Парсер сайта yaencontre.com обрабатывает ссылку {url}")
            parsers[6](url=url, without_delete=True)
        elif "https://www.habitaclia.com/" in url:
            print(f"[INFO] Парсер сайта habitaclia.com обрабатывает ссылку {url}")
            parsers[3](url=url, without_delete=True)
        elif "https://www.fotocasa.es/" in url:
            print(f"[INFO] Парсер сайта fotocasa.es обрабатывает ссылку {url}")
            parsers[2](url=url, without_delete=True)
        elif "https://www.enalquiler.com/" in url:
            print(f"[INFO] Парсер сайта enalquiler.com обрабатывает ссылку {url}")
            parsers[1](url=url, without_delete=True)
        else:
            print("[INFO] Ссылки на сайт idealista.com не обрабатываются")
            print(f"[ERROR] Сбор данных по ссылке {url} прерван")


def main():
    while True:
        mode_text = "(Введите 1 - включить парсер, 2 - добавить url в часто используемые)"
        mode = input(f"[INPUT] Выберете режим работы программы {mode_text}: >>> ")

        if mode == "1":
            print("[INFO] Выберете, какой парсер вы хотите запустить")
            print("\n".join(variants))
            while True:
                variant = input("[INPUT] Введите номер парсера: >>> ")
                if variant not in "1 2 3 4 5 6 0":
                    print("[ERROR] Вы ввели что-то не то. Попробуйте еще раз")
                elif variant == "0":
                    print("[INFO] Учтите, что ссылки на сайт idealista.com обрабатываться в таком режиме не будут")
                    print("[INFO] Это связанно с необходимостью проходить капчу в начале парсинга сайта idealista.com")
                    print("[INFO] Если вам нужно спарсить ссылки на сайт idealista.com, используйте 4 парсер напрямую")
                    go_command = input("Начинаем парсинг по часто используемым? (y/n): >>> ")
                    if go_command == "y":
                        delete_data()
                        clean_photos()
                        parsing_urls()
                else:
                    delete_data()
                    clean_photos()
                    variant = int(variant)
                    parsers[variant]()
                    break
            break
        elif mode == "2":
            print("[INFO] Для записи url адресов в часто используемые, необходимо записать их в файле urls.txt")
            print('[INFO] Обратите внимание, что в файле urls.txt url должны быть каждый с новой строки.', end=" ")
            print("Без каких либо разделительных знаков")
            start = input("[INPUT] Начать запись url-адресов ? (y/n): >>> ")
            if start == "y":
                record_urls()
            break
        else:
            print('[ERROR] Извините, похоже вы ввели неверные данные. Попробуйте еще раз')


if __name__ == "__main__":
    main()
