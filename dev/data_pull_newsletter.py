from sqlalchemy import create_engine
import pandas as pd
import os

# establish connections
user = os.environ.get("postgres-user")
password = os.environ.get("postgres-pass")
host = os.environ.get("postgres-host")
conn_string = 'postgresql://{user}:{password}@{host}:25060/defaultdb'.format(password=password, user=user, host=host)
db = create_engine(conn_string)

price_drops = pd.read_sql("Select * from car_gurus_formatted_view where difference_in_price > 0", db)



print(price_drops)