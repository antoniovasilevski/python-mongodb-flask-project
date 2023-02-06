<!-- PROJECT LOGO -->
<br />

<h1 align="center">Data Cleaning</h1>

  <p align="center">
    Flask based web application used to normalizes company names and export the data to a MongoDB database.
    <br />
    <a href="https://github.com/antoniovasilevski/python-mongodb-flask-project"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/antoniovasilevski/python-mongodb-flask-project">View Demo</a>
    ·
    <a href="https://github.com/antoniovasilevski/python-mongodb-flask-project/issues">Report Bug</a>
    ·
    <a href="https://github.com/antoniovasilevski/python-mongodb-flask-project/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

This is a basic web application made in Flask, it takes an SQL database, reads and updates it with normalized company names.
Then it encrypts the company data and writes it to a MongoDB database.
Finally it reads the MongoDB database, decrypts the data and displays it in a html table.


<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running follow these simple example steps.

### Prerequisites

* Python 3.10+
* MongoDB
* SQLite

### Packages

* sqlite3
* Flask
* Pandas
* Cryptography
* Cleanco
* PyMongo
* Jinja

### Installation

1. Clone the repo

   ```sh
   git clone https://github.com/antoniovasilevski/python-mongodb-flask-project
   ```

2. Install PIP packages

   ```sh
   pip install sqlite3 pandas cryptography pymongo cleanco flask jinja2
   ```

3. Enter your SQLite database in `config.py`

   ```py
   sql_database = "your_sqldb.db"
   ```

4. Configure your MongoDB collection in `config.py`

   ```py
   mydb = myclient["your-mongodb"]
   mycol = mydb["your-collection"]
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage 

### SQLite Database

The sqlite database has one table - companies which consists of 7 columns (id, name, country_iso, city, nace, website, company_name_cleaned) and 20 000 rows.

1. Using `read_sql_query()` from the Pandas library to read the database.

  1.1. To change table name, replace `companies` in `update_db()` from `utils.py`.

     ```py
     df = pd.read_sql_query("SELECT * FROM companies", conn, dtype=object)
     ```

  1.2. To change column name that you want to update, replace `company_name_cleaned` in `update_db()` from `utils.py`.

     ```py
     company_data['company_name_cleaned']
     ```

2. For data cleaning, a combination of a custom module - `clean_company_name()` and the Cleanco library is used.

  In each row, the name is passed through the function and written to the `company_name_cleaned` column.

  For further cleaning, add additional substrings to `remove_list` in `clean_company_name()` from `utils.py`.

### MongoDB Database

1. Using the `write_to_mongodb()` module from `utils.py`, a new `companies` collection is created.

  Read the  SQLite database in chunks with a `pandas` SQL query, then encrypt it with a Fernet key and write it by chunks to the MongoDB collection.

  1.1. Load SQLite database in chunks

   ```py
   df = pd.read_sql_query("SELECT * FROM companies", conn, chunksize=10000)
   ```

  1.2. Write to MongoDB with `insert_many`

   ```py
   mycol.insert_many(companies)
   ```

2. Exporting the MongoDB `companies` collection to a HTML table with `mongodb_to_html()` from `utils.py`

  After the user inputs a range in the html form, find each row with a `find_one` query, decrypt the data using the Fernet secret key and write it to a HTML file.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [ ] Safer long term encryption key management solution
- [ ] Working with cloud-based databases

See the [open issues](https://github.com/antoniovasilevski/python-mongodb-flask-project/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Antonio Vasilevski - antonio99vas@gmail.com

Project Link: [https://github.com/antoniovasilevski/python-mongodb-flask-project](https://github.com/antoniovasilevski/python-mongodb-flask-project)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/github_username/repo_name.svg?style=for-the-badge
[contributors-url]: https://github.com/antoniovasilevski/python-mongodb-flask-project/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/github_username/repo_name.svg?style=for-the-badge
[forks-url]: https://github.com/antoniovasilevski/python-mongodb-flask-project/network/members
[stars-shield]: https://img.shields.io/github/stars/github_username/repo_name.svg?style=for-the-badge
[stars-url]: https://github.com/antoniovasilevski/python-mongodb-flask-project/stargazers
[issues-shield]: https://img.shields.io/github/issues/github_username/repo_name.svg?style=for-the-badge
[issues-url]: https://github.com/antoniovasilevski/python-mongodb-flask-project/issues
[product-screenshot]: /images/project-example.png
