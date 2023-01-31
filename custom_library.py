from re import sub
from numpy import int64, isnan, int32
import pandas as pd
from cleanco import basename
from cryptography.fernet import Fernet
from config import connect_to_sqldb, connect_to_mongodb


def encrypt(message: bytes, key: bytes) -> bytes:
    return Fernet(key).encrypt(message)


def decrypt(token: bytes, key: bytes) -> bytes:
    return Fernet(key).decrypt(token)


def clean_company_name(name_arg):
    """
    Cleans a given company name from different substrings.
    Args:
        name_arg (str): base company name

    Returns:
        str: company name cleaned
    """
    remove_list = ("\(.*?\)", r"\(.*\)", "LIMITED", " LTD.", " LTD", "‰", "Ã", '""', '"')
    
    if "COMMERCE" in name_arg:
        modified = name_arg.split('COMMERCE', maxsplit=1)
        modified[1] = ' COMMERCE' + modified[1]
        name_arg = ' '.join(modified)
        
    for substring in remove_list:
        name_arg = sub(substring, "", name_arg)
    
    while r"\(.*\)" in name_arg:    
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
    
    # Checks for company names that start with an abbreviation
    modified = name_arg.split(' ')
    if len(modified[0]) < 4 and modified[0] != "THE":
        for id in range(1, len(modified)):
            modified[id] = modified[id].title()
        name_arg = ' '.join(modified)
        return name_arg
            
    name_arg = ' '.join(modified)
    
    return name_arg.title() if len(name_arg) > 4 else name_arg


def update_db():
    """
    Gets SQLite db connection, reads the database, 
    iterates and cleans company names, then writes the data to the SQL db.
    """
    
    # Get SQLite database connection
    conn = connect_to_sqldb()
    cursor = conn.cursor()
    
    # Read SQL database to a pandas DataFrame
    df = pd.read_sql_query("SELECT * FROM companies", conn, dtype=object)
    
    # Drop the company_name_cleaned table if it already exists
    try:
        cursor.execute("ALTER TABLE companies DROP COLUMN company_name_cleaned")
    except:
        pass
    
    company_data = dict(df)
    company_data['company_name_cleaned'] = []

    for name in df.name:
        
        # Read through the names in the companies database, clean them and append them to a list.
        cleaned_name = clean_company_name(name)
        company_data['company_name_cleaned'].append(cleaned_name)

    # Managing NaN, floats
    company_data['nace'] = company_data['nace'].astype('Int64')
    
    # Converting the dictionary back to a pandas df and write it to the sql db.
    company_data = pd.DataFrame(company_data)
    company_data.to_sql('companies', conn, if_exists='replace', index=False)
    
    conn.close()


def write_to_mongodb(secret_key):
    """
    Reads the updated SQL database, encrypts the data and writes it to a MongoDB collection.
    """

    # Connect to a MongoDB client, get collection and drop it if it exists.
    mycol = connect_to_mongodb()
    mycol.drop()
    
    # Get SQL db connection and load it in chunks, for a database this small (20k rows),
    # there is no reason to do this, the data doesn't load in a dataframe format,
    # so its harder to work with and it takes longer to write to MongoDB.
    # With larger datasets memory management is important.
    conn = connect_to_sqldb()
    df = pd.read_sql_query("SELECT * FROM companies", conn, chunksize=10000)

    for chunk in df:
        companies = []
        
        # Iterates through elements in the columns, encrypts them and writes them to the MongoDB collection.
        for company_name_cleaned, id, name, country_iso, city, nace, website in zip(
            chunk['company_name_cleaned'], chunk['id'], chunk['name'], chunk['country_iso'], chunk['city'], chunk['nace'], chunk['website']):

            company = dict()
            columns = dict()
            columns['id'] = encrypt(str(id).encode(), secret_key)
            columns['name'] = encrypt(name.encode(), secret_key)
            columns['country_iso'] = encrypt(country_iso.encode(), secret_key)
            
            # Handle None and NaN, they made a problem when encrypting/decrypting.
            columns['city'] = encrypt('None'.encode(), secret_key) if city == None else encrypt(city.encode(), secret_key)
            columns['nace'] = encrypt('None'.encode(), secret_key) if isnan(nace) else encrypt(str(nace).encode(), secret_key)
            
            columns['website'] = encrypt(website.encode(), secret_key)
            
            # This is a _id object that MongoDB adds to each object, makes for easy query since it's not encrypted.
            company['_id'] = id
            
            # Encrypted company name to string, dictionary doesn't allow bytes format as key
            company[str(encrypt(company_name_cleaned.encode(), secret_key))] = columns
            
            # Apppend company dictionary to companies list, one at a time 
            # then insert the whole chunk to the collection with insert_many.
            companies.append(company)
        mycol.insert_many(companies)
    
    conn.close()
    
    
def mongodb_to_html(secret_key, min, max):
    """
    Gets 2 integers in output range, gets all the MongoDB objects with _id in that range.
    Decrypts the data and writes it in a html table.
    """
    
    # Format output_range string into 2 integers.
    # Get MongoDB collection
    mycol = connect_to_mongodb()
    
    headers = ['ID', 'Name', 'Country Iso', 'City', 'Nace', 'Website', 'Company Name Cleaned']
    
    # Open html file in write mode.
    with open("templates/content.html", "w") as html_file:
        
        # Write html table file header and footer.
        html_table_header = "{% extends 'input.html' %}\n{% block table %}\n<table class='mongodb-data'>\n"
        html_table_footer = '</table>\n{% endblock %}'
        body = ''

        # Iterate through the headers list and add a header element for each.
        for header in headers:
            
            html_table_header += '<th>' + header + '</th>'

        # Iterate through the output range that the function gets as an argument.
        for id in range(min, max+1):
            
            # Get each object within range.
            myquery = {'_id': id}
            data = mycol.find_one(myquery)
            
            for key, value in data.items():
                
                # Check if value is dictionary, we get 2 key:value sets, _id:id and company_name:company_data.
                if isinstance(value, dict):
                    
                    # Iterate throught company data, decrypting each element and create a table data cell for each.
                    # Add class = "right" for numbers.
                    body += ''.join([ f'<td class="right">{ decrypt(elem, secret_key).decode() }</td>' 
                                     if isinstance(elem, bytes) and col in ['id', 'nace']
                                     
                                     else f'<td>{ decrypt(elem, secret_key).decode() }</td>' 
                                     if isinstance(elem, bytes)
                                     
                                     else f'<td>{ elem }</td>' 
                                     
                                     for col, elem in value.items() ])
                    
                # if key != '_id':
                    # Decrypt company name. Need to turn it back to bytes in order to decrypt.
                    key = key[2:-1]
                    dictkey_decoded = decrypt(key.encode(), secret_key).decode()
                    
                    body += f'<td>{ dictkey_decoded }</td>\n</tr>\n'
        
        # Concatenate all the elements of the html table file and then write to the file.        
        html_table = html_table_header + '\n<tr>' + body + html_table_footer
        html_file.write(html_table)
    
    html_file.close()