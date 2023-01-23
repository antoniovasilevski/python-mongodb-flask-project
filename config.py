import sqlite3
from cryptography.fernet import Fernet
import pymongo


def connect_to_sqldb():
    sql_database = 'semos_companies_data.db'
    conn = sqlite3.connect(sql_database)
    
    return conn


def connect_to_mongodb():
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["test_db"]
    mycol = mydb["companies"]
    
    return mycol