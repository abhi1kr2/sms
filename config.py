
import os
class Config:
    SECRET_KEY = "mysecret123"
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "abhi")   # your local password
DB_NAME = os.getenv("DB_NAME", "rkdf_pro")