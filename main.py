from flask import Flask
import sqlite3
from re import sub
import pandas as pd
from cleanco import basename


def clean_name(name_arg, remove_list):
    
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


# app = Flask(__name__)

# @app.route("/")
# def connect_to_sqlite():
#     con = sqlite3.connect("semos_companies_data.db")
#     cur = con.cursor()

#     return "success"
        
# app.run(debug=True)

conn = sqlite3.connect('semos_companies_data.db')

remove_list = ("\(.*?\)", r"\(.*\)", "LIMITED", " LTD.", " LTD")

df = pd.read_sql_query("SELECT * FROM companies", conn, chunksize=1000)

for chunk in df:
    
    for name, id in zip(chunk['name'], chunk['id']):
        
        cleaned_name = clean_name(name, remove_list)
        
        conn.execute("UPDATE companies SET company_name_cleaned = ? WHERE id = ? ", (cleaned_name, id))
        
    conn.commit()
    
conn.close()