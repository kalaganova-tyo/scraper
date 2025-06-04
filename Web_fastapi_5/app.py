from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
import sqlite3
from typing import List, Optional

app = FastAPI()

DATABASE = 'cars.db'
USERS_DB = 'users.db'
HTML_FILE = 'index.html'


class UserRegister(BaseModel):
    name: str
    email: EmailStr


class UserResponse(BaseModel):
    id: int
    name: str
    email: str



def get_cars_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def get_users_db():
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn


@app.post("/api/register", response_model=UserResponse)
def register_user(user: UserRegister):
    try:
        db = get_users_db()
        cursor = db.cursor()

        # Проверка существующего пользователя
        cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

        # Добавление нового пользователя
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            (user.name, user.email)
        )
        db.commit()

        # Получение данных нового пользователя
        cursor.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,))
        new_user = cursor.fetchone()

        return dict(new_user)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail="Ошибка базы данных")
    finally:
        db.close()


@app.get("/api/users", response_model=List[UserResponse])
def get_users():
    try:
        db = get_users_db()
        users = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
        return [dict(user) for user in users]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail="Ошибка базы данных")
    finally:
        db.close()


@app.get("/api/cars")
def get_cars(year: Optional[str] = None, mileage: Optional[str] = None):
    try:
        db = get_cars_db()
        query = "SELECT * FROM cars"
        conditions = []
        params = []

        if year:
            conditions.append("title LIKE ?")
            params.append(f"%{year}%")

        if mileage:
            try:
                mileage = int(mileage)
                cars = db.execute(query, params).fetchall()
                result = []

                for car in cars:
                    try:
                        title = car['title']
                        parts = [p.strip() for p in title.split(',')]
                        if len(parts) >= 3:
                            mileage_str = parts[2].split(' км')[0].replace(' ', '')
                            car_mileage = int(mileage_str) if mileage_str.isdigit() else 0
                        else:
                            car_mileage = 0

                        if car_mileage > mileage:
                            continue

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

                return result

            except ValueError:
                pass

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY datetime DESC"

        cars = db.execute(query, params).fetchall()
        result = []
        for car in cars:
            try:
                price_str = car['price'].replace(' ₽', '').replace(' ', '')
                price = int(price_str) if price_str.isdigit() else 0

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

        return result

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail="Ошибка базы данных")
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
async def serve_html():
    try:
        with open(HTML_FILE, 'r', encoding='utf-8') as file:
            return HTMLResponse(content=file.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="HTML файл не найден")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)