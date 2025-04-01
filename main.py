from fastapi import FastAPI, Query, HTTPException
import random
import math

app = FastAPI()

@app.get("/about")
def about():
    return {
        "ФИО": "Иванов Иван Иванович",
        "Группа": "ББ-01",
        "Описание": "Разработчик API"
    }

@app.get("/rnd")
def get_random():
    return {"Случайное число": random.randint(1, 10)}

@app.post("/t_square")
def calculate_triangle(
    a: float = Query(..., gt=0, description="Длина стороны a, должна быть > 0"),
    b: float = Query(..., gt=0, description="Длина стороны b, должна быть > 0"),
    c: float = Query(..., gt=0, description="Длина стороны c, должна быть > 0")
):
    if a + b <= c or a + c <= b or b + c <= a:
        raise HTTPException(status_code=400, detail="Неверные размеры треугольника: не выполняется неравенство треугольника")
    
    perimeter = a + b + c
    s = perimeter / 2
    area = math.sqrt(s * (s - a) * (s - b) * (s - c))
    return {"Периметр": perimeter, "Площадь": area}
