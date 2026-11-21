import re
import json
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

def detect_store_from_url(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    if "shopee" in domain:
        return "Shopee"
    elif "mercadolivre" in domain or "mercado livre" in domain or "mercadolivre.com" in domain or "ml.com" in domain:
        return "Mercado Livre"
    elif "amazon" in domain:
        return "Amazon"
    elif "aliexpress" in domain:
        return "AliExpress"
    elif "temu" in domain:
        return "Temu"
    elif "tiktok" in domain:
        return "TikTok Shop"
    elif "magalu" in domain or "magazineluiza" in domain:
        return "Magalu"
    elif "shein" in domain:
        return "Shein"
    else:
        # Extrai nome legível do domínio
        parts = domain.replace("www.", "").split(".")
        return parts[0].capitalize() if parts else "Loja Online"

def clean_price_string(price_str: str) -> float | None:
    if not price_str:
        return None
    try:
        # Remove caracteres indesejados exceto números, vírgulas e pontos
        cleaned = re.sub(r'[^\d,\.]', '', str(price_str).strip())
        if not cleaned:
            return None
        # Formato brasileiro comum: 1.250,50 -> 1250.50
        if ',' in cleaned and '.' in cleaned:
            if cleaned.rfind(',') > cleaned.rfind('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            cleaned = cleaned.replace(',', '.')
        
        val = float(cleaned)
        return round(val, 2)
    except Exception:
        return None

async def extract_product_metadata(url: str) -> dict:
    result = {
        "title": "",
        "image_url": "",
        "current_price": None,
        "original_price": None,
        "store": detect_store_from_url(url),
        "affiliate_url": url,
        "category": "Achadinhos",
        "discount_percent": 0
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=HEADERS) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return result

            html = response.text
            soup = BeautifulSoup(html, "html.parser")

            # 1. Metatags Open Graph (og:) e Twitter
            og_title = (
                soup.find("meta", property="og:title") or
                soup.find("meta", attrs={"name": "twitter:title"}) or
                soup.find("title")
            )
            if og_title:
                content = og_title.get("content") or og_title.text
                if content:
                    result["title"] = content.strip().split(" | ")[0].split(" - ")[0]

            og_image = (
                soup.find("meta", property="og:image") or
                soup.find("meta", property="og:image:secure_url") or
                soup.find("meta", attrs={"name": "twitter:image"})
            )
            if og_image:
                result["image_url"] = og_image.get("content", "").strip()

            # Preço via Open Graph
            og_price = (
                soup.find("meta", property="product:price:amount") or
                soup.find("meta", property="og:price:amount")
            )
            if og_price:
                price_val = clean_price_string(og_price.get("content", ""))
                if price_val:
                    result["current_price"] = price_val

            # 2. Dados estruturados JSON-LD (Schema.org / Product)
            json_ld_tags = soup.find_all("script", type="application/ld+json")
            for script in json_ld_tags:
                try:
                    if not script.string:
                        continue
                    data = json.loads(script.string.strip())
                    
                    # Pode ser lista ou dict
                    items = data if isinstance(data, list) else [data]
                    
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        
                        # Pode estar encapsulado em @graph
                        sub_items = item.get("@graph", [item])
                        for obj in sub_items:
                            if not isinstance(obj, dict):
                                continue
                            
                            type_val = obj.get("@type", "")
                            if type_val in ["Product", "IndividualProduct"]:
                                if not result["title"] and obj.get("name"):
                                    result["title"] = obj.get("name").strip()
                                
                                if not result["image_url"] and obj.get("image"):
                                    img = obj.get("image")
                                    if isinstance(img, list) and img:
                                        result["image_url"] = img[0] if isinstance(img[0], str) else img[0].get("url", "")
                                    elif isinstance(img, dict):
                                        result["image_url"] = img.get("url", "")
                                    elif isinstance(img, str):
                                        result["image_url"] = img
                                
                                # Offers
                                offers = obj.get("offers")
                                if offers:
                                    offer_list = offers if isinstance(offers, list) else [offers]
                                    for offer in offer_list:
                                        if isinstance(offer, dict):
                                            p = offer.get("price") or offer.get("lowPrice")
                                            price_val = clean_price_string(p)
                                            if price_val:
                                                result["current_price"] = price_val
                                                break
                except Exception:
                    continue

            # Cálculo de desconto se houver preço antigo e atual
            if result["original_price"] and result["current_price"]:
                if result["original_price"] > result["current_price"]:
                    disc = int(((result["original_price"] - result["current_price"]) / result["original_price"]) * 100)
                    result["discount_percent"] = disc

    except Exception as e:
        # Em caso de timeout ou restrição de conexão, retorna o esqueleto preenchido
        pass

    return result
