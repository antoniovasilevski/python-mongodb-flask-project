from flask import Flask, render_template, url_for, request 
import sqlite3
from re import sub
import pandas as pd
from cleanco import basename
import pymongo
import jinja2

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
        
    if "THE" in name_arg:
        modified = name_arg.split(" ")
        
        if "THE" == modified[-1]:
            modified.pop(-1)
            name_arg = ' '.join(modified)
        
    name_arg = basename(name_arg)
    
    return name_arg.title() if len(name_arg) > 4 else name_arg

def update_db():
    remove_list = ("\(.*?\)", r"\(.*\)", "LIMITED", " LTD.", " LTD")
    
    sql_database = 'semos_companies_data.db'
    conn = sqlite3.connect(sql_database)
    cursor = conn.cursor()
    df = pd.read_sql_query("SELECT * FROM companies", conn)
    
    try:
        cursor.execute("ALTER TABLE companies DROP COLUMN company_name_cleaned")
    except:
        pass
    
    company_data = dict(df)
    company_data['company_name_cleaned'] = []
        
    for name in df.name:
            
        cleaned_name = clean_company_name(name, remove_list)
        company_data['company_name_cleaned'].append(cleaned_name)
    
    company_data = pd.DataFrame(company_data)
    company_data.to_sql('companies', conn, if_exists='replace', index=False)
        
    conn.close()
    
def write_to_mongodb():
    sql_database = 'semos_companies_data.db'
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["test_db"]
    mycol = mydb["companies"]
    
    conn = sqlite3.connect(sql_database)
    df = pd.read_sql_query("SELECT * FROM companies", conn, chunksize=1000)

    for chunk in df:
        
        for company_name_cleaned, id, name, country_iso, city, nace, website in zip(
            chunk['company_name_cleaned'], chunk['id'], chunk['name'], chunk['country_iso'], chunk['city'], chunk['nace'], chunk['website']):

            company = {}
            columns = {}
            columns['id'] = id
            columns['name'] = name
            columns['country_iso'] = country_iso
            columns['city'] = city
            columns['nace'] = nace
            columns['website'] = website
            
            company['_id'] = id
            company[company_name_cleaned] = columns
            mycol.insert_one(company)
            
    conn.close()    

def mongodb_to_html():
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["test_db"]
    mycol = mydb["companies"]
    
    with open("templates/index.html", "w") as html_file:
        html_file.write("{% block body%}<div class="">{% endblock %}")
        
    
    for id in range(1, 21):
        myquery = {'_id': id}
        data = mycol.find_one(myquery)
        print(data)


##################### Flask ########################

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    """ 
    Displays the index page accessible at '/'
    """
    return render_template('index.html')


@app.route('/update_sql', methods=['GET', 'POST'])
def read_update_sql():
    if request.method == 'POST':
        if request.form['sqldb'] == "Update the SQL database":
            update_db()
    return render_template('index.html')

@app.route('/write_to_mongodb', methods=['GET', 'POST'])
def writing_to_mongodb():
    if request.method == 'POST':
        if request.form['mongodb'] == "Create a MongoDB":
            write_to_mongodb()   
    return render_template('index.html')

if __name__ == '__main__':
    app.debug=True
    app.run()

####################################################