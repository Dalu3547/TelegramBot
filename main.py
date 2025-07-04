from fastapi import FastAPI
from .db import init_db, add_product, get_all_products

app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()

@app.get("/products")
def list_products():
    return get_all_products()

@app.post("/track/")
def track_product(user_id: int, source: str, url: str):
    add_product(user_id, source, url)
    return {"status": "added"}

@app.get("/all/")
def read_products():
    return get_all_products()