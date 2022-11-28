import pymysql
from pymysql import cursors
from config import user, password, port, host, db_name, table


def database(query):
    try:
        connection = pymysql.connect(port=port, host=host, user=user, password=password,
                                     database=db_name, cursorclass=cursors.DictCursor)
        try:
            cursor = connection.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            connection.commit()
            return result
        except Exception as ex:
            print(f"Something Wrong: {ex}")
            return "Error"
        finally:
            connection.close()
    except Exception as ex:
        print(f"Connection was not completed because {ex}")
        return "Error"


def create_table():
    query = f"""CREATE TABLE {table.lower()} (title VARCHAR(500),  object_type VARCHAR(10), price VARCHAR(50), 
    square VARCHAR(50), bedrooms VARCHAR(50), bathes VARCHAR(50),  description VARCHAR(5000), url VARCHAR(500), 
    image_url VARCHAR(500));"""
    database(query=query)


def delete_data():
    query = f"""DELETE FROM {table};"""
    database(query=query)


def insert_data(objects):
    delete_data()
    for object_dict in objects:
        object_dict["description"] = object_dict["description"].replace('"', "'")
        query = f"""INSERT INTO {table}(title, object_type, price, square, bedrooms, bathes, description, url, image_url)
        VALUES ("{object_dict['title']}", "{object_dict['object_type']}", "{object_dict['price']}", 
        "{object_dict['square']}", "{object_dict['bedrooms']}", "{object_dict['bathes']}", 
        "{object_dict['description']}", "{object_dict['url']}", "{object_dict['image_url']}");"""
        database(query=query)


if __name__ == "__main__":
    create_table()
