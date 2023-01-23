from re import sub
from timeit import timeit
from bson import Int64
from numpy import NaN, int32, int64, isnan
import pandas as pd
from cleanco import basename
from cryptography.fernet import Fernet
from config import connect_to_sqldb, connect_to_mongodb



def encrypt(message: bytes, key: bytes) -> bytes:
    return Fernet(key).encrypt(message)


def decrypt(token: bytes, key: bytes) -> bytes:
    return Fernet(key).decrypt(token)


def clean_company_name(name_arg):
    remove_list = ("\(.*?\)", r"\(.*\)", "LIMITED", " LTD.", " LTD")
    
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
    if len(modified[0]) < 4 and modified[0] != "THE":
        for id in range(1, len(modified)):
            modified[id] = modified[id].title()
        name_arg = ' '.join(modified)
        return name_arg
            
    name_arg = ' '.join(modified)
    
    return name_arg.title() if len(name_arg) > 4 else name_arg


def update_db():
    timeit()
    conn = connect_to_sqldb()
    cursor = conn.cursor()
    df = pd.read_sql_query("SELECT * FROM companies", conn, dtype=object)
    
    try:
        cursor.execute("ALTER TABLE companies DROP COLUMN company_name_cleaned")
    except:
        pass
    
    company_data = dict(df)
    company_data['company_name_cleaned'] = []

    for name in df.name:
        
        cleaned_name = clean_company_name(name)
        company_data['company_name_cleaned'].append(cleaned_name)

    company_data['nace'] = company_data['nace'].astype('Int64')
    company_data = pd.DataFrame(company_data)
    company_data.to_sql('companies', conn, if_exists='replace', index=False)
    
    conn.close()


def write_to_mongodb(decrypt_key):

    mycol = connect_to_mongodb()
    mycol.drop()
    
    conn = connect_to_sqldb()
    df = pd.read_sql_query("SELECT * FROM companies", conn, chunksize=1000)

    for chunk in df:
        
        companies = []
        
        for company_name_cleaned, id, name, country_iso, city, nace, website in zip(
            chunk['company_name_cleaned'], chunk['id'], chunk['name'], chunk['country_iso'], chunk['city'], chunk['nace'], chunk['website']):

            company = {}
            columns = {}
            columns['id'] = encrypt(str(id).encode(), decrypt_key)
            columns['name'] = encrypt(name.encode(), decrypt_key)
            columns['country_iso'] = encrypt(country_iso.encode(), decrypt_key)
            columns['city'] = city if city == None else encrypt(city.encode(), decrypt_key)
            columns['nace'] = nace if isnan(nace) else encrypt(str(nace).encode(), decrypt_key)
            columns['website'] = encrypt(website.encode(), decrypt_key)
            
            company['_id'] = id
            company[str(encrypt(company_name_cleaned.encode(), decrypt_key))] = columns
            companies.append(company)
            
        
        mycol.insert_many(companies)
    
    conn.close()
    
    
def mongodb_to_html(decode_key):
    timeit()
    mycol = connect_to_mongodb()
    
    headers = ['Company Name Cleaned', 'ID', 'Name', 'Country Iso', 'City', 'Nace', 'Website']
    
    with open("templates/content.html", "w") as html_file:
    
        html_table_header = "{% extends 'index.html' %}\n{% block content %}\n<table class='mongodb-data'>\n"
        html_table_footer = '</table>\n{% endblock %}'
        body = ''

        for header in headers:
            
            html_table_header += '<th>' + header + '</th>'
    
        for id in range(1, 21):
            
            myquery = {'_id': id}
            data = mycol.find_one(myquery)
            
            for key, value in data.items():
                
                if key != '_id':
                    key = key[2:-1]
                    key_decoded = decrypt(key.encode(), decode_key).decode()
                    body += f'<tr>\n<td>{ key_decoded }</td>'
                    
                if isinstance(value, dict):
                    body += ''.join([ f'<td>{ decrypt(elem, decode_key).decode() }</td>' if isinstance(elem, bytes)
                                    #  else f'<td>{ decrypt(elem, decode_key).decode() }</td>'
                                     else f'<td>{ elem }</td>' 
                                     for elem in value.values() ]) + '</tr>\n'

                
        html_table = html_table_header + body + html_table_footer
        html_file.write(html_table)
    
    html_file.close()