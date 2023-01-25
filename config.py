import sqlite3
import pymongo
from cryptography.fernet import Fernet


def connect_to_sqldb():
    """
    Connect to SQLite database.
    Returns:
        SQLite connection
    """
    sql_database = 'semos_companies_data.db'
    conn = sqlite3.connect(sql_database)
    
    return conn


def connect_to_mongodb():
    """
    Connect to a local MongoDB
    Returns:
        MongoDB collection
    """
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["test_db"]
    mycol = mydb["companies"]
    
    return mycol


def get_key():
    """
    Generate Fernet encryption key
    Returns:
        encryption key
    """
    secret_key = Fernet.generate_key()
    return secret_key
    