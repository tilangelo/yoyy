import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from urllib.parse import urljoin

BASE_URL = "https://www.proficosmetics.ru"
START_URL = "https://www.proficosmetics.ru/catalog/make-up/p{}"
OUTPUT_CSV = "proficosmetics.csv"

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
            "name": "",
            "description": "",
            "barcode": "",
            "size": "",
            "rating": "",
            "reviews_count": "",
            "images": []
        }

    name_el = soup.select_one("h1.h1")
    name = name_el.get_text(strip=True)

    # --- описание ---
    desc = ""
    desc_el = soup.select_one(".b-goods-content__body")
    if desc_el:
        desc = desc_el.get_text(" ", strip=True)

    # --- штрихкод/артикул/код товара---
    barcode = ""
    bar = soup.select_one(".ms-4.d-none.d-md-block")
    if bar:
        barcode = bar.get_text(" ", strip=True).replace("Артикул: ", "")

    # --- размер (мл, г) ---
    size = ""
    size_match = re.search(r'(\d+(?:[.,]\d+)?\s*(?:мл|г|гр|ml|g))', name, re.IGNORECASE)
    size = size_match.group(1) if size_match else ""

    # --- рейтинг ---
    rating = ""
    rating_el = soup.select_one(".b-reviews-2-rate__total")
    if rating_el:
        rating = rating_el.get_text(strip=True)
        # if m:
        #     rating = m.group(1).replace(",", ".")

    # --- отзывы ---
    reviews = ""
    m = soup.select_one(".mt-1")
    if m:
        reviews = m.get_text(" ", strip=True)

    # --- изображения ---
    images = []
    for img in soup.select("img"):
        src = img.get("src") or img.get("data-src")
        if src and "placeholder" not in src:
            src = urljoin(BASE_URL, src)
            if src not in images:
                images.append(src)

    return {
        "name": name,
        "description": desc,
        "barcode": barcode,
        "size": size,
        "rating": rating,
        "reviews_count": reviews,
        "images": images
    }

def parse_product(card):
    a = card #.select_one("div.b-goods.kr_product_list")
    if not a:
        return None

    name_el = a.select_one("a.b-goods__name")
    # name = name_el.get_text(strip=True)

    url = BASE_URL + name_el["href"]

    img_el = card.select_one("img")
    image_tmp = img_el.get("src") if img_el and img_el.get("src") else (img_el.get("data-src") if img_el else "")
    image = BASE_URL + image_tmp

    price_el = card.select_one(".b-goods__price-new")
    price = price_el.get_text(strip=True).replace("\xa0", "").replace("&nbsp;", "").replace(" ", "").replace("₽", "") if price_el else None

    brand_el = card.select_one("a.b-goods__brand")
    brand = brand_el.get_text(strip=True)

    details = parse_product_page(url)
    time.sleep(PRODUCT_SLEEP)

    return [
        "proficosmetics",
        details["name"],
        brand,
        price,
        url,
        image,
        details["description"],
        details["barcode"],
        details["size"],
        details["rating"],
        details["reviews_count"],
        "|".join(details["images"])
    ]


def parse_proficosmetics(max_pages=56):
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

        for page in range(1, max_pages + 1):
            url = START_URL.format(page)
            print(f"[ProfiCosmetics] Парсинг страницы {page}")

            soup = get_page(url)
            cards = soup.select(".b-goods.kr_product_list")

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
    parse_proficosmetics()
