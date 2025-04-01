from fastapi import FastAPI, Query, Path, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

items = [
    {
        "id": 1,
        "name": "Тостер",
        "price": 150.0,
        "description": "Качественный тостер для приготовления завтрака."
    },
    {
        "id": 2,
        "name": "Ноутбук",
        "price": 600.0,
        "description": "Мощный ноутбук для игр."
    },
    {
        "id": 3,
        "name": "Телевизор",
        "price": 300.0,
        "description": "Высокий и широкий."
    }
]

class Item(BaseModel):
    id: int = Field(..., example=2)
    name: str = Field(..., min_length=2, max_length=100, example="Ноутбук")
    price: float = Field(..., gt=0, example=999.99)
    description: Optional[str] = Field(None, max_length=500, example="Мощный ноутбук для игр.")

#1
@app.get("/items/", response_model=List[Item])
def get_items(
        name: str|None = Query(None, min_length=2, example="Ноутбук"),
        min_price: float|None = Query(None, gt=0, example=100),
        max_price: float|None = Query(None, gt=0, example=1000),
        limit: Optional[int] = Query(10, le=100, example=5)):

    filtered_items = items

    if name:
        filtered_items = [item for item in filtered_items if name.lower() in item["name"].lower()]

    if min_price:
        filtered_items = [item for item in filtered_items if item["price"] >= min_price]

    if max_price:
        filtered_items = [item for item in filtered_items if item["price"] <= max_price]

    if min_price and max_price and min_price > max_price:
        raise HTTPException(status_code=400, detail="min_price не может быть больше max_price")
    
    if not filtered_items:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    return filtered_items[:limit]

#2
@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int = Path(..., gt=0, example=42)):
    for item in items:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Товар не найден")

#3
@app.post("/items/", response_model=Item, status_code=201)
def create_item(item: Item):
    new_id = max(item["id"] for item in items) + 1
    new_item = {"id": new_id, **item.dict()}
    items.append(new_item)
    return new_item
