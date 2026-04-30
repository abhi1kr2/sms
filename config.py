import os

class Config:
    SECRET_KEY = "mysecret123"

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "abhi")
    DB_NAME = os.getenv("DB_NAME", "rkdf_pro")

# expose for db.py
DB_HOST = Config.DB_HOST
DB_USER = Config.DB_USER
DB_PASSWORD = Config.DB_PASSWORD
DB_NAME = Config.DB_NAME