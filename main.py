from enalquiler_com import main as enalquiler
from fotocasa_es import main as fotocasa
from habitaclia_com import main as habitaclia
from idealista_com import main as idealista
from pisos_com import main as pisos
from yaencontre_com import main as yaencontre


def main():
    parsers = {1: enalquiler, 2: fotocasa, 3: habitaclia, 4: idealista, 5: pisos, 6: yaencontre}
    variants = ["1 - парсер сайта enalquiler.com", "2 - парсер сайта fotocasa.es", "3 - парсер сайта habitaclia.com",
                "4 - парсер сайта idealista.com", "5 - парсер сайта pisos.com", "6 - парсер сайта yaencontre.com"]
    print("Выберете, какой парсер вы хотите запустить")
    print("\n".join(variants))
    variant = int(input("[INPUT] Введите номер парсера: "))
    parsers[variant]()


if __name__ == "__main__":
    main()
