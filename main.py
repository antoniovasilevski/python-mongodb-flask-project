from flask import Flask, render_template, url_for, request 
from custom_library import update_db, write_to_mongodb, mongodb_to_html

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