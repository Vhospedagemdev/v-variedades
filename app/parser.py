import re
import json
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

COMMON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

def detect_store_from_url(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    if "shopee" in domain or "shp.ee" in domain:
        return "Shopee"
    elif "mercadolivre" in domain or "mercado livre" in domain or "mercadolivre.com" in domain or "ml.com" in domain:
        return "Mercado Livre"
    elif "amazon" in domain or "amzn.to" in domain:
        return "Amazon"
    elif "aliexpress" in domain or "ali.ski" in domain:
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
        parts = domain.replace("www.", "").split(".")
        return parts[0].capitalize() if parts else "Loja Online"

def clean_price_string(price_str) -> float | None:
    if price_str is None or price_str == "":
        return None
    try:
        cleaned = re.sub(r'[^\d,\.]', '', str(price_str).strip())
        if not cleaned:
            return None
        # Formato brasileiro com vírgula de centavos: 1.250,50 ou 49,90
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

def clean_title(title: str) -> str:
    if not title:
        return ""
    # Remove sufixos como "| Mercado Livre", "- Shopee Brasil", etc.
    t = title.strip()
    separators = [" | ", " - MercadoLivre", " - Mercado Livre", " | Mercado Livre", " | Shopee", " - Shopee"]
    for sep in separators:
        if sep in t:
            t = t.split(sep)[0]
    return t.strip()

async def extract_mercado_livre(soup: BeautifulSoup, html: str, result: dict) -> dict:
    """Extração cirúrgica para Mercado Livre"""
    # 1. Título
    h1 = soup.find("h1", class_=re.compile(r"ui-pdp-title"))
    if h1 and h1.text.strip():
        result["title"] = h1.text.strip()
    
    # 2. Imagem
    # Tenta imagem principal em alta resolução
    img = soup.find("img", class_=re.compile(r"ui-pdp-image|ui-pdp-gallery__figure__image"))
    if img:
        src = img.get("data-zoom") or img.get("src") or img.get("data-src")
        if src and not src.startswith("data:"):
            result["image_url"] = src
    
    # 3. Preços no Mercado Livre
    # Preço atual
    price_container = soup.find("span", class_=re.compile(r"ui-pdp-price__second-line|price-tag-amount"))
    if price_container:
        fraction = price_container.find("span", class_=re.compile(r"andes-money-amount__fraction"))
        cents = price_container.find("span", class_=re.compile(r"andes-money-amount__cents"))
        if fraction:
            val_str = fraction.text.strip()
            if cents:
                val_str += f".{cents.text.strip()}"
            result["current_price"] = clean_price_string(val_str)
            
    # Preço antigo / original (riscado)
    old_price_container = soup.find("s", class_=re.compile(r"ui-pdp-price__original-value|andes-money-amount--previous"))
    if old_price_container:
        fraction = old_price_container.find("span", class_=re.compile(r"andes-money-amount__fraction"))
        cents = old_price_container.find("span", class_=re.compile(r"andes-money-amount__cents"))
        if fraction:
            val_str = fraction.text.strip()
            if cents:
                val_str += f".{cents.text.strip()}"
            result["original_price"] = clean_price_string(val_str)

    # Desconto
    discount_span = soup.find("span", class_=re.compile(r"ui-pdp-price__second-line__label|andes-money-amount__discount"))
    if discount_span and "%" in discount_span.text:
        disc_num = re.sub(r'[^\d]', '', discount_span.text)
        if disc_num:
            result["discount_percent"] = int(disc_num)

    return result

async def extract_shopee(soup: BeautifulSoup, html: str, final_url: str, result: dict) -> dict:
    """Extração cirúrgica para Shopee (incluindo links curtos shp.ee e API interna quando disponível)"""
    # Tenta extrair itemid e shopid da URL final
    # URLs da Shopee comuns: /product/shopid/itemid ou -i.shopid.itemid
    match_ids = re.search(r'-i\.(\d+)\.(\d+)', final_url) or re.search(r'/product/(\d+)/(\d+)', final_url)
    
    if match_ids:
        shop_id = match_ids.group(1)
        item_id = match_ids.group(2)
        try:
            api_url = f"https://shopee.com.br/api/v4/item/get?itemid={item_id}&shopid={shop_id}"
            headers_api = {
                "User-Agent": COMMON_HEADERS["User-Agent"],
                "Accept": "application/json",
                "Referer": final_url,
                "x-api-source": "rweb"
            }
            async with httpx.AsyncClient(timeout=6.0, headers=headers_api) as client:
                resp = await client.get(api_url)
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    if data.get("name"):
                        result["title"] = data["name"]
                    if data.get("image"):
                        result["image_url"] = f"https://down-br.img.susercontent.com/file/{data['image']}"
                    
                    # Preço na Shopee vem multiplicado por 100000
                    p_min = data.get("price") or data.get("price_min")
                    p_before = data.get("price_before_discount")
                    if p_min:
                        result["current_price"] = round(p_min / 100000, 2)
                    if p_before and p_before > 0:
                        result["original_price"] = round(p_before / 100000, 2)
                    return result
        except Exception:
            pass

    # Se não obteve via API, busca nos scripts embutidos na página
    for script in soup.find_all("script"):
        text = script.string or ""
        if '"price":' in text and '"name":' in text:
            m_title = re.search(r'"name"\s*:\s*"([^"]+)"', text)
            if m_title and not result["title"]:
                result["title"] = m_title.group(1)

            m_image = re.search(r'"image"\s*:\s*"([^"]+)"', text)
            if m_image and not result["image_url"]:
                img = m_image.group(1)
                if not img.startswith("http"):
                    img = f"https://down-br.img.susercontent.com/file/{img}"
                result["image_url"] = img

            m_price = re.search(r'"price"\s*:\s*(\d+)', text)
            if m_price and not result["current_price"]:
                pval = int(m_price.group(1))
                if pval > 10000:
                    result["current_price"] = round(pval / 100000, 2)
                else:
                    result["current_price"] = float(pval)

    return result

async def extract_product_metadata(url: str) -> dict:
    url = url.strip()
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
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, headers=COMMON_HEADERS) as client:
            response = await client.get(url)
            final_url = str(response.url)
            result["store"] = detect_store_from_url(final_url)
            
            html = response.text
            soup = BeautifulSoup(html, "html.parser")

            # 1. Estratégias especializadas por loja
            if result["store"] == "Mercado Livre":
                result = await extract_mercado_livre(soup, html, result)
            elif result["store"] == "Shopee":
                result = await extract_shopee(soup, html, final_url, result)

            # 2. Metatags Open Graph (OG) e Twitter (Fallback ou dados complementares)
            if not result["title"]:
                og_title = (
                    soup.find("meta", property="og:title") or
                    soup.find("meta", attrs={"name": "twitter:title"}) or
                    soup.find("title")
                )
                if og_title:
                    content = og_title.get("content") or og_title.text
                    result["title"] = clean_title(content)

            if not result["image_url"]:
                og_image = (
                    soup.find("meta", property="og:image") or
                    soup.find("meta", property="og:image:secure_url") or
                    soup.find("meta", attrs={"name": "twitter:image"}) or
                    soup.find("meta", attrs={"name": "twitter:image:src"})
                )
                if og_image:
                    result["image_url"] = og_image.get("content", "").strip()

            if not result["current_price"]:
                og_price = (
                    soup.find("meta", property="product:price:amount") or
                    soup.find("meta", property="og:price:amount") or
                    soup.find("meta", attrs={"name": "twitter:data1"})
                )
                if og_price:
                    result["current_price"] = clean_price_string(og_price.get("content", ""))

            # 3. JSON-LD estruturado Schema.org
            json_ld_tags = soup.find_all("script", type="application/ld+json")
            for script in json_ld_tags:
                try:
                    if not script.string:
                        continue
                    data = json.loads(script.string.strip())
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        sub_items = item.get("@graph", [item])
                        for obj in sub_items:
                            if not isinstance(obj, dict):
                                continue
                            if obj.get("@type") in ["Product", "IndividualProduct", "ItemPage"]:
                                if not result["title"] and obj.get("name"):
                                    result["title"] = clean_title(obj.get("name"))
                                
                                if not result["image_url"] and obj.get("image"):
                                    img = obj.get("image")
                                    if isinstance(img, list) and img:
                                        result["image_url"] = img[0] if isinstance(img[0], str) else img[0].get("url", "")
                                    elif isinstance(img, dict):
                                        result["image_url"] = img.get("url", "")
                                    elif isinstance(img, str):
                                        result["image_url"] = img
                                
                                offers = obj.get("offers")
                                if offers and not result["current_price"]:
                                    offer_list = offers if isinstance(offers, list) else [offers]
                                    for offer in offer_list:
                                        if isinstance(offer, dict):
                                            p = offer.get("price") or offer.get("lowPrice")
                                            pval = clean_price_string(p)
                                            if pval:
                                                result["current_price"] = pval
                                                break
                except Exception:
                    continue

            # 4. Cálculo de desconto se houver preço original e atual
            if result["original_price"] and result["current_price"]:
                if result["original_price"] > result["current_price"]:
                    disc = int(((result["original_price"] - result["current_price"]) / result["original_price"]) * 100)
                    result["discount_percent"] = disc

    except Exception:
        pass

    return result
