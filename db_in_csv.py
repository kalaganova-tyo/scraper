import sqlite3
import pandas as pd

conn = sqlite3.connect('cars.db')

df = pd.read_sql_query("SELECT * FROM cars", conn)

df.to_csv('cars.csv', index=False, encoding='utf-8-sig')

conn.close()
print("Данные успешно экспортированы в cars.csv")
