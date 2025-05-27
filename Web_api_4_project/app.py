import sqlite3
from flask import Flask, render_template, request, jsonify, g

app = Flask(__name__)
DATABASE = 'cars.db'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/cars', methods=['GET'])
def get_cars():
    year = request.args.get('year')
    mileage = request.args.get('mileage')

    db = get_db()
    query = "SELECT * FROM cars"
    conditions = []
    params = []

    if year:
        conditions.append("title LIKE ?")
        params.append(f"%{year}%")

    if mileage:
        try:
            mileage = int(mileage)
            # Получаем все автомобили и фильтруем их уже в Python
            cars = db.execute(query, params).fetchall()
            result = []

            for car in cars:
                try:
                    # Извлекаем пробег из заголовка
                    title = car['title']
                    # Формат: "Hyundai Solaris, 2020, 100 000 км"
                    parts = [p.strip() for p in title.split(',')]
                    if len(parts) >= 3:
                        mileage_str = parts[2].split(' км')[0].replace(' ', '')
                        car_mileage = int(mileage_str) if mileage_str.isdigit() else 0
                    else:
                        car_mileage = 0

                    # Фильтруем по пробегу
                    if car_mileage > mileage:
                        continue

                    # Преобразуем цену
                    price_str = car['price'].replace(' ₽', '').replace(' ', '')
                    price = int(price_str) if price_str.isdigit() else 0

                    result.append({
                        'id': car['id'],
                        'title': car['title'],
                        'price': price,
                        'mileage': car_mileage,
                        'datetime': car['datetime']
                    })

                except Exception as e:
                    print(f"Error processing car {car['id']}: {str(e)}")
                    continue

            return jsonify(result)

        except ValueError:
            pass

    # Если фильтр по пробегу не применялся, выполняем обычный запрос
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY datetime DESC"

    try:
        cars = db.execute(query, params).fetchall()
        result = []
        for car in cars:
            try:
                # Преобразуем цену
                price_str = car['price'].replace(' ₽', '').replace(' ', '')
                price = int(price_str) if price_str.isdigit() else 0

                # Извлекаем пробег
                mileage_km = 0
                title = car['title']
                parts = [p.strip() for p in title.split(',')]
                if len(parts) >= 3:
                    mileage_str = parts[2].split(' км')[0].replace(' ', '')
                    if mileage_str.isdigit():
                        mileage_km = int(mileage_str)

                result.append({
                    'id': car['id'],
                    'title': car['title'],
                    'price': price,
                    'mileage': mileage_km,
                    'datetime': car['datetime']
                })
            except Exception as e:
                print(f"Error processing car {car['id']}: {str(e)}")
                continue

        return jsonify(result)

    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=True)