import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from urllib.parse import urljoin

BASE_URL = "https://chudodey.com/"
START_URL = "https://chudodey.com/async_catalog/makiyazh/sort/field_name/title/sort/sort_type/возрастание/pager/page_number/{}"
OUTPUT_CSV = "chudodey.csv"

PAGE_SLEEP = 1.0
PRODUCT_SLEEP = 0.5

def get_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")

def parse_product_page(url):
    try:
        soup = get_page(url)
    except Exception:
        return {
            "description": "",
            "barcode": "",
            "size": "",
            "rating": "",
            "reviews_count": "",
            "images": []
        }

    text = soup.get_text(" \n ", strip=True)

    price_el = soup.select_one(".product-price")
    price = price_el.get_text(strip=True) if price_el else None

    # --- описание ---
    desc = ""
    desc_el = soup.select_one(".content, .annex__desc")
    if desc_el:
        desc = desc_el.get_text(" ", strip=True)

    # --- штрихкод ---
    barcode = ""
    info = soup.select(".card__data-val")
    if info:
        barcode = info[0].get_text(" ", strip=True)

    # --- размер (мл, г) ---
    size = ""
    if info:
        size = info[1].get_text(" ", strip=True)

    # --- рейтинг ---
    rating = ""
    rating_el = soup.select_one(".rating, .product-rating")
    if rating_el:
        m = re.search(r"(\d[\d.,]*)", rating_el.get_text(strip=True))
        if m:
            rating = m.group(1).replace(",", ".")

    # --- отзывы ---
    reviews = ""
    m = re.search(r"Отзывы\s*\(?(\d+)\)?", text, flags=re.IGNORECASE)
    if m:
        reviews = m.group(1)

    # --- изображения ---
    images = []
    for img in soup.select("img"):
        src = img.get("src") or img.get("data-src")
        if src and "placeholder" not in src:
            src = urljoin(BASE_URL, src)
            if src not in images:
                images.append(src)

    return {
        "price": price,
        "description": desc,
        "barcode": barcode,
        "size": size,
        "rating": rating,
        "reviews_count": reviews,
        "images": images
    }

def parse_product(card):
    a = card.select_one("a.block-row.product.unit")
    if not a:
        return None

    name = a.select_one(".product-title")
    if name:
        name = name.get_text(strip=True)
    else:
        name = ""

    url = a["href"]

    img_el = card.select_one("img")
    image = img_el.get("src") if img_el and img_el.get("src") else (img_el.get("data-src") if img_el else "")

    # price_el = card.select_one(".product-price")
    # price = price_el.get_text(strip=True) if price_el else None

    brand_el = card.select_one(".unit__name-brand")
    brand = brand_el.get_text(strip=True) if brand_el else name.split()[0]

    details = parse_product_page(url)
    time.sleep(PRODUCT_SLEEP)

    return [
        "chudodey",
        name,
        brand,
        details["price"],
        url,
        image,
        details["description"],
        details["barcode"],
        details["size"],
        details["rating"],
        details["reviews_count"],
        "|".join(details["images"])
    ]


def parse_chudodey(max_pages=173):
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "source",
            "name",
            "brand",
            "price",
            "url",
            "image",
            "description",
            "barcode",
            "size",
            "rating",
            "reviews_count",
            "image_all"
        ])

        for page in range(0, max_pages + 1):
            url = START_URL.format(page)
            print(f"[ChudoDey] Парсинг страницы {page}")

            soup = get_page(url)
            cards = soup.select(".product, .catalog__unit, .block-row.product.unit")

            if not cards:
                print("Товары не найдены. Остановка.")
                break

            for card in cards:
                product = parse_product(card)
                if product:
                    writer.writerow(product)

            time.sleep(1)

    print("Файл сохранён:", OUTPUT_CSV)


if __name__ == "__main__":
    parse_chudodey()
