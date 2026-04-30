import pymysql
import time
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def get_db():
    for i in range(5):  # retry 5 times
        try:
            return pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                cursorclass=pymysql.cursors.DictCursor
            )
        except:
            time.sleep(2)
    raise Exception("Database not ready")