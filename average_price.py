import sqlite3


conn = sqlite3.connect('cars.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT 
        AVG(
            CAST(REPLACE(REPLACE(price, ' ', ''), '₽', '') AS INTEGER)
        ) as average_price,
        COUNT(*) as total_ads
    FROM cars
    WHERE price != ''
""")

result = cursor.fetchone()
average_price = result[0]
total_ads = result[1]

print(f"Средняя цена: {average_price:,.0f} ₽")
print(f"На основе {total_ads} объявлений")

conn.close()
