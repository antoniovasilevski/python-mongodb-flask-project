from flask import Flask, render_template, url_for, request 
import sqlite3
from re import sub
import pandas as pd
from cleanco import basename
import pymongo

# app = Flask(__name__)

sql_database = 'semos_companies_data.db'

def clean_company_name(name_arg, remove_list):
    
    for substring in remove_list:
        name_arg = sub(substring, "", name_arg)
        
    name_arg = str.replace(name_arg, r"\(.*\)","")
        
    if  "- " in name_arg:
        name_arg = sub("- ", " ", name_arg)
            
    if  " -" in name_arg:
        name_arg = sub(" -", " ", name_arg)
        
    if "," in name_arg:
        name_arg = name_arg.split(",")
        name_arg = name_arg[0]
            
    while "  " in name_arg:
        name_arg = sub("  ", " ", name_arg)
    
    while " AND " in name_arg:
        name_arg = sub("AND", "&", name_arg)
        
    if "THE" in name_arg:
        modified = name_arg.split(" ")
        
        if "THE" == modified[-1]:
            modified.pop(-1)
            name_arg = ' '.join(modified)
        
    name_arg = basename(name_arg)
    
    return name_arg.title() if len(name_arg) > 4 else name_arg

def update_db(sql_db, chunksize):
    conn = sqlite3.connect(sql_db)
    
    remove_list = ("\(.*?\)", r"\(.*\)", "LIMITED", " LTD.", " LTD")

    df = pd.read_sql_query("SELECT * FROM companies", conn, chunksize=chunksize)

    for chunk in df:
    
        for name, id in zip(chunk['name'], chunk['id']):
        
            cleaned_name = clean_company_name(name, remove_list)
        
            conn.execute("UPDATE companies SET company_name_cleaned = ? WHERE id = ? ", (cleaned_name, id))
        
        conn.commit()

    conn.close()


##################### Flask ########################

# @app.route("/", methods=['POST', 'GET'])
# def index():
#     return render_template('index.html')
        
# app.run(debug=True)

####################################################

db_values = ['id', 'name', 'country_iso', 'city', 'nace', 'website']

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["mydatabase"]
mycol = mydb["companies"]

conn = sqlite3.connect(sql_database)
df = pd.read_sql_query("SELECT * FROM companies", conn, chunksize=1000)

for chunk in df:
    
    for company_name_cleaned, id, name, country_iso, city, nace, website in zip(chunk['company_name_cleaned'], chunk['id'], chunk['name'], chunk['country_iso'], chunk['city'], chunk['nace'], chunk['website']):
        mydict = { company_name_cleaned: {'id': id, 'name': name, 'country_iso': country_iso, 'city': city, 'nace': nace, 'website': website}}
        
    # for index in range(len(chunk)):
    #     mydict = { chunk['company_name_cleaned'][index]: [{x: f'{chunk[x][index]}'} for x in db_values]}
        
        mycol.insert_one(mydict)

conn.close()
