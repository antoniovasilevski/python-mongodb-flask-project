from flask import Flask, render_template, url_for, request 
import sqlite3
from re import sub
import pandas as pd
from cleanco import basename
import pymongo

def clean_company_name(name_arg, remove_list):
    
    if "COMMERCE" in name_arg:
        modified = name_arg.split('COMMERCE', maxsplit=1)
        modified[1] = ' COMMERCE' + modified[1]
        name_arg = ' '.join(modified)
        
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
    
    modified = name_arg.split(' ')
    if len(modified[0]) < 4:
        for id in range(1, len(modified)):
            modified[id] = modified[id].title()
        name_arg = ' '.join(modified)
        return name_arg
            
    name_arg = ' '.join(modified)
    
    return name_arg.title() if len(name_arg) > 4 else name_arg

def update_db():
    remove_list = ("\(.*?\)", r"\(.*\)", "LIMITED", " LTD.", " LTD")
    
    sql_database = 'semos_companies_data.db'
    conn = sqlite3.connect(sql_database)
    cursor = conn.cursor()
    df = pd.read_sql_query("SELECT * FROM companies", conn, dtype=object)
    
    try:
        cursor.execute("ALTER TABLE companies DROP COLUMN company_name_cleaned, nace")
    except:
        pass
    
    company_data = dict(df)
    company_data['company_name_cleaned'] = []
        
    for name in df.name:
        
        cleaned_name = clean_company_name(name, remove_list)
        company_data['company_name_cleaned'].append(cleaned_name)

    company_data['nace'] = company_data['nace'].astype('Int64')
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
    headers = ['Company Name Cleaned', 'ID', 'Name', 'Country Iso', 'City', 'Nace', 'Website']
    
    with open("templates/content.html", "w") as html_file:
    
        html_table_header = "{% extends 'index.html' %}\n{% block content %}\n<table>\n"
        html_table_footer = '</table>\n{% endblock %}'
        body = ''
    
        for header in headers:
            html_table_header += '<th>' + header + '</th>'
    
        for id in range(1, 21):
            myquery = {'_id': id}
            data = mycol.find_one(myquery)
            
            for key, value in data.items():
                if key != '_id':
                    body += f'<tr>\n<td>{key}</td>'
                try:
                    if isinstance(value, dict):
                        body+= ''.join([f'<td>{elem}</td>' for elem in value.values()]) + '</tr>\n'
                except:
                    pass
                
        html = html_table_header + body + html_table_footer
        html_file.write(html)
    
    html_file.close()
        
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
            try:
                write_to_mongodb()
                return render_template('index.html')
            except:
                return render_template('index.html')  
        if request.form['mongodb'] == "Output MongoDB Objects":
            mongodb_to_html()
            
            return render_template('content.html')
            
if __name__ == '__main__':
    app.debug=True
    app.run()

####################################################