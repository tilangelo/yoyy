from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

password = quote_plus("Uc~FXtxYWP")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+psycopg2://postgres:{password}@db:5432/Cosmetics"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
@app.get("/search", response_class=HTMLResponse)
def search(
    request: Request,
    q: str = "",
    sort: str = "",
    price_from: str = "",
    price_to: str = "",
    brand: str = ""
):
    price_from = int(price_from) if price_from.isdigit() else None
    price_to = int(price_to) if price_to.isdigit() else None

    order_by = "min_price ASC"

    if sort == "price_desc":
        order_by = "min_price DESC"
    elif sort == "rating_asc":
        order_by = "max_rating ASC"
    elif sort == "rating_desc":
        order_by = "max_rating DESC"

    # ---------- УСЛОВИЯ ----------
    conditions = []
    params = {"q": f"%{q}%"}

    conditions.append("""
        (p.canonical_name ILIKE :q
         OR p.description ILIKE :q
         OR p.brand ILIKE :q)
    """)

    if brand:
        conditions.append("LOWER(p.brand) = LOWER(:brand)")
        params["brand"] = brand

    having = []

    if price_from is not None:
        having.append("MIN(o.price) >= :price_from")
        params["price_from"] = price_from

    if price_to is not None:
        having.append("MAX(o.price) <= :price_to")
        params["price_to"] = price_to

    # ---------- SQL ----------
    query = f"""
        SELECT
            p.id,
            p.canonical_name,
            p.brand,
            p.image_url,
            MIN(o.price) AS min_price,
            MAX(o.rating) AS max_rating
        FROM products p
        JOIN offers o ON o.product_id = p.id
        WHERE {" AND ".join(conditions)}
        GROUP BY p.id
    """

    if having:
        query += " HAVING " + " AND ".join(having)

    query += f" ORDER BY {order_by}"

    # ---------- ВЫПОЛНЕНИЕ ----------
    with engine.connect() as conn:
        products = conn.execute(text(query), params).fetchall()

        brands = conn.execute(text("""
            SELECT DISTINCT brand
            FROM products
            WHERE brand IS NOT NULL
            ORDER BY brand
        """)).scalars().all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "products": products,
            "query": q,
            "sort": sort,
            "price_from": price_from,
            "price_to": price_to,
            "brand": brand,
            "brands": brands
        }
    )


@app.get("/product/{product_id}", response_class=HTMLResponse)
def product_detail(request: Request, product_id: int):
    with engine.connect() as conn:
        product = conn.execute(text("""
            SELECT * FROM products WHERE id = :id
        """), {"id": product_id}).fetchone()

        offers = conn.execute(text("""
            SELECT *
            FROM offers
            WHERE product_id = :id
            ORDER BY price ASC
        """), {"id": product_id}).fetchall()

        attributes = conn.execute(text("""
            SELECT attribute_name, attribute_value
            FROM attributes
            WHERE product_id = :id
        """), {"id": product_id}).fetchall()

    return templates.TemplateResponse(
        "product.html",
        {
            "request": request,
            "product": product,
            "offers": offers,
            "attributes": attributes
        }
    )
