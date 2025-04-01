from fastapi import FastAPI, HTTPException, Query
import random
import math

app = FastAPI()

@app.get("/about")
async def about():
    return {
        "ФИО": "Иванов Иван Иванович",
        "Группа": "Группа 101",
        "Возраст": "21 год"
    }

@app.get("/rnd")
async def get_random():
    return {"Случайное_число": random.randint(1, 10)}

@app.post("/t_square")
async def triangle(
    a: float = Query(..., gt=0, description="Длина стороны a (больше 0)"),
    b: float = Query(..., gt=0, description="Длина стороны b (больше 0)"),
    c: float = Query(..., gt=0, description="Длина стороны c (больше 0)")
):
    if (a + b <= c) or (a + c <= b) or (b + c <= a):
        raise HTTPException(status_code=400, detail="Треугольник с такими сторонами не может существовать.")
    
    perimeter = a + b + c
    
    s = perimeter / 2
    area = math.sqrt(s * (s - a) * (s - b) * (s - c))
    
    return {"Периметр": perimeter, "Площадь": area}
