import re
import json
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote

# Headers especiais de crawler social (Mercado Livre e lojas permitem Facebook/WhatsApp bot para gerar preview)
SOCIAL_CRAWLER_HEADERS = {
    "User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
    "Cache-Control": "no-cache"
}

STANDARD_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
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
    t = title.strip()
    separators = [
        " | Mercado Livre", " - Mercado Livre", " | MercadoLivre", 
        " | Shopee Brasil", " - Shopee Brasil", " | Shopee", " - Shopee"
    ]
    for sep in separators:
        if sep in t:
            t = t.split(sep)[0]
    return t.strip()

def extract_slug_title(url: str, store: str) -> str:
    """Extrai o nome do produto legível diretamente do link amigável da URL"""
    try:
        path = unquote(urlparse(url).path)
        slug = path.rstrip("/").split("/")[-1]
        
        if store == "Mercado Livre":
            # Ex: MLB-3575971441-fone-de-ouvido-sem-fio-bluetooth-tws-_JM
            parts = slug.split("-")
            clean_parts = [p for p in parts if not re.match(r'^(MLB|\d+|_JM)$', p, re.I)]
            if clean_parts:
                return " ".join(clean_parts).capitalize()
        elif store == "Shopee":
            # Ex: Fone-De-Ouvido-Sem-Fio-Bluetooth-5.3-Tws-i.314545233.22791494883
            slug_clean = slug.split("-i.")[0]
            clean_parts = slug_clean.replace("-", " ").strip()
            if len(clean_parts) > 5 and not clean_parts.startswith("product"):
                return clean_parts
    except Exception:
        pass
    return ""

async def extract_product_metadata(url: str) -> dict:
    url = url.strip()
    store = detect_store_from_url(url)
    
    result = {
        "title": "",
        "image_url": "",
        "current_price": None,
        "original_price": None,
        "store": store,
        "affiliate_url": url,
        "category": "Achadinhos",
        "discount_percent": 0
    }

    # 1. Tenta nome baseado no slug da URL imediatamente como base
    slug_title = extract_slug_title(url, store)
    if slug_title:
        result["title"] = slug_title

    # 2. Requisição HTTP - Tenta primeiro com User-Agent de Crawler (bypassa bot-check em ML e gera meta-tags)
    html = ""
    try:
        headers_to_try = [SOCIAL_CRAWLER_HEADERS, STANDARD_BROWSER_HEADERS]
        for headers in headers_to_try:
            try:
                async with httpx.AsyncClient(timeout=8.0, follow_redirects=True, headers=headers) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200 and len(resp.text) > 1000:
                        html = resp.text
                        final_url = str(resp.url)
                        result["store"] = detect_store_from_url(final_url)
                        # Se a URL redirecionou para o produto final, tenta o slug da URL final também
                        new_slug_title = extract_slug_title(final_url, result["store"])
                        if new_slug_title:
                            result["title"] = new_slug_title
                        break
            except Exception:
                continue

        if html:
            soup = BeautifulSoup(html, "html.parser")

            # Metatags Open Graph (og:) e Twitter
            og_title = (
                soup.find("meta", property="og:title") or
                soup.find("meta", attrs={"name": "twitter:title"}) or
                soup.find("title")
            )
            if og_title:
                content = og_title.get("content") or og_title.text
                c_clean = clean_title(content)
                # Ignora títulos genéricos da página inicial
                if c_clean and c_clean.lower() not in ["mercado livre", "shopee brasil", "shopee", "mercado libre"]:
                    result["title"] = c_clean

            og_image = (
                soup.find("meta", property="og:image") or
                soup.find("meta", property="og:image:secure_url") or
                soup.find("meta", attrs={"name": "twitter:image"}) or
                soup.find("meta", attrs={"name": "twitter:image:src"})
            )
            if og_image:
                img_url = og_image.get("content", "").strip()
                # Não usar o logo da plataforma como imagem do produto
                if img_url and "pt_logo_large" not in img_url and "logo" not in img_url.lower():
                    result["image_url"] = img_url

            # Preço por Open Graph
            og_price = (
                soup.find("meta", property="product:price:amount") or
                soup.find("meta", property="og:price:amount") or
                soup.find("meta", attrs={"name": "twitter:data1"})
            )
            if og_price:
                result["current_price"] = clean_price_string(og_price.get("content", ""))

            # JSON-LD estruturado Schema.org
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

            # Fallback de busca no HTML por valores monetários se preço ainda não foi encontrado
            if not result["current_price"]:
                # Procura padrões R$ xx,xx ou $ xx.xx
                prices_found = re.findall(r'R\$\s*([\d\.,]+)', html)
                if prices_found:
                    valid_prices = []
                    for pf in prices_found[:10]:
                        val = clean_price_string(pf)
                        if val and 1.0 <= val <= 20000.0:
                            valid_prices.append(val)
                    if valid_prices:
                        result["current_price"] = valid_prices[0]
                        if len(valid_prices) > 1 and valid_prices[1] > valid_prices[0]:
                            result["original_price"] = valid_prices[1]

            # Desconto
            if result["original_price"] and result["current_price"]:
                if result["original_price"] > result["current_price"]:
                    disc = int(((result["original_price"] - result["current_price"]) / result["original_price"]) * 100)
                    result["discount_percent"] = disc

    except Exception:
        pass

    return result
