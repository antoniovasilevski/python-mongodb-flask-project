from flask import Flask, flash, render_template, request, url_for, redirect
from custom_library import update_db, write_to_mongodb, mongodb_to_html
from cryptography.fernet import Fernet
from config import get_key
import js2py

app = Flask(__name__)

# Generating fernet key, harcoded for easier debuging
# app.secret_key = get_key()
app.secret_key = b'eqfQr4AywieA6IchMDPBh5vaYAC_GKjvPwNc3ss-EtM='

@app.route('/', methods=['GET', 'POST'])
def index():
    """ 
    Displays the index page accessible at '/'
    """
    return render_template('index.html')

@app.route('/update_sql', methods=['GET', 'POST'])
def read_update_sql():
    """
    Calls a function that reads and updates the SQL db when 
    'Update the SQL database' button is pressed.
    """
    if request.method == 'POST':
        if request.form['sqldb'] == "Update the SQL database":
            update_db()
            flash("Finished cleaning data!", "success")
            return render_template('index.html')

@app.route('/write_to_mongodb', methods=['GET', 'POST'])
def writing_to_mongodb():
    """
    Waits for a 'mongodb' post method
    """
    if request.method == 'POST':
        # Waits for a "Create a MongoDB" request, calls a function that reads the SQL db,
        # encrypts it and writes it to a MongoDB collection.

        if request.form.get('mongodb-write') == "Create a MongoDB":
            write_to_mongodb(app.secret_key)
            flash("Your encryted MongoDB database is done!", "success")
            return render_template('input.html')

        # Wait for a value in the input field and a "Output MongoDB Objects" request.
        # Then call a function that reads, decrypts the MongoDB and outputs it to an HTML table.
        if request.form.get('mongodb-read') == "Output MongoDB Objects" :

            # Default value is 1-20 if no output range in form
            min_range = int(request.form['min-range']) if request.form['min-range'] else 1
            max_range = int(request.form['max-range']) if request.form['max-range'] else 20
            
            # Check if range values are valid
            if min_range > max_range:
                flash('Maximum value cannot be lower than the minimum value', 'error')
            else:
                mongodb_to_html(app.secret_key, min_range, max_range) 
                return render_template('content.html')
            return render_template('input.html')

            
if __name__ == '__main__':
    app.debug=True
    app.run()
