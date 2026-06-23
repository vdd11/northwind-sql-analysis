import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv("NEON_DATABASE_URL")
engine = create_engine(DATABASE_URL)
table_urls = {
    'customers': 'https://raw.githubusercontent.com/neo4j-contrib/northwind-neo4j/master/data/customers.csv',
    'products': 'https://raw.githubusercontent.com/neo4j-contrib/northwind-neo4j/master/data/products.csv',
    'orders': 'https://raw.githubusercontent.com/neo4j-contrib/northwind-neo4j/master/data/orders.csv',
    'order_details': 'https://raw.githubusercontent.com/neo4j-contrib/northwind-neo4j/master/data/order-details.csv'
}

for table_name, url in table_urls.items():
    try:
        print("Downloading {table_name} data from {url}...".format(table_name=table_name, url=url))
        df = pd.read_csv(url, on_bad_lines='skip')

        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print("Successfully loaded {table_name} data into the database.".format(table_name=table_name))
    except Exception as e:
        print("Error loading {table_name} data: {error}".format(table_name=table_name, error=str(e)))
print("All tables have been processed.")