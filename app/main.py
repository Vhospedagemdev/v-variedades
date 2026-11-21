import os
import secrets
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

from app.database import get_db, init_db, verify_password, hash_password
from app.parser import extract_product_metadata

# Inicializa banco de dados
init_db()

app = FastAPI(title="V Variedades - Vitrine de Afiliados")

# Arquivos Estáticos e Templates
BASE_DIR = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# --- MODELOS PYDANTIC ---
class ScrapeRequest(BaseModel):
    url: str

class ProductCreateUpdate(BaseModel):
    title: str
    category: str
    store: str
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    image_url: str
    affiliate_url: str
    is_featured: int = 0
    is_active: int = 1

class StatusUpdate(BaseModel):
    is_active: int

class FeaturedUpdate(BaseModel):
    is_featured: int

# --- SEGURANÇA E SESSÕES ---
def get_current_admin(request: Request):
    token = request.cookies.get("admin_session")
    if not token:
        return None
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT admin_id FROM sessions WHERE session_token = ? AND expires_at > ?",
        (token, datetime.utcnow())
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return row["admin_id"]

def require_admin(request: Request):
    admin_id = get_current_admin(request)
    if not admin_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autorizado")
    return admin_id

def get_site_settings() -> dict:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}

# ==========================================
# ROTAS PÚBLICAS (VITRINE / LANDING PAGE)
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def public_index(request: Request):
    settings = get_site_settings()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "settings": settings,
            "request_url": str(request.url)
        }
    )

@app.get("/api/products")
async def list_public_products():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, category, store, original_price, current_price,
               discount_percent, image_url, affiliate_url, is_featured
        FROM products
        WHERE is_active = 1
        ORDER BY is_featured DESC, id DESC
    """)
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products

# ==========================================
# PAINEL ADMINISTRATIVO (VIEWS)
# ==========================================

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    if get_current_admin(request):
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse(request=request, name="admin_login.html", context={"error": None})

@app.post("/admin/login")
async def admin_login_action(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash, password_salt FROM admins WHERE username = ?", (username.strip(),))
    admin = cursor.fetchone()

    if not admin or not verify_password(password, admin["password_hash"], admin["password_salt"]):
        conn.close()
        return templates.TemplateResponse(
            request=request,
            name="admin_login.html",
            context={"error": "Usuário ou senha inválidos."},
            status_code=400
        )

    # Cria sessão segura
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(days=7)
    cursor.execute(
        "INSERT INTO sessions (session_token, admin_id, expires_at) VALUES (?, ?, ?)",
        (token, admin["id"], expires)
    )
    conn.commit()
    conn.close()

    res = RedirectResponse(url="/admin", status_code=302)
    res.set_cookie(key="admin_session", value=token, httponly=True, max_age=7*24*3600, samesite="lax")
    return res

@app.get("/admin/logout")
async def admin_logout(request: Request):
    token = request.cookies.get("admin_session")
    if token:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE session_token = ?", (token,))
        conn.commit()
        conn.close()
    res = RedirectResponse(url="/admin/login", status_code=302)
    res.delete_cookie(key="admin_session")
    return res

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    admin_id = get_current_admin(request)
    if not admin_id:
        return RedirectResponse(url="/admin/login", status_code=302)

    conn = get_db()
    cursor = conn.cursor()

    # Estatísticas
    cursor.execute("SELECT COUNT(*) as total FROM products")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as active FROM products WHERE is_active = 1")
    active = cursor.fetchone()["active"]

    cursor.execute("SELECT COUNT(*) as featured FROM products WHERE is_featured = 1")
    featured = cursor.fetchone()["featured"]

    cursor.execute("SELECT COUNT(DISTINCT category) as cat_count FROM products")
    categories_count = cursor.fetchone()["cat_count"]

    # Produtos
    cursor.execute("SELECT * FROM products ORDER BY id DESC")
    products = [dict(row) for row in cursor.fetchall()]

    settings = get_site_settings()
    conn.close()

    stats = {
        "total": total,
        "active": active,
        "featured": featured,
        "categories_count": categories_count
    }

    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "stats": stats,
            "products": products,
            "settings": settings
        }
    )

@app.post("/admin/settings")
async def save_settings(
    request: Request,
    brand_name: str = Form(...),
    slogan: str = Form(...),
    instagram_url: str = Form(""),
    tiktok_url: str = Form(""),
    whatsapp_url: str = Form(""),
    facebook_url: str = Form(""),
    disclaimer: str = Form("")
):
    admin_id = get_current_admin(request)
    if not admin_id:
        return RedirectResponse(url="/admin/login", status_code=302)

    conn = get_db()
    cursor = conn.cursor()
    updates = {
        "brand_name": brand_name,
        "slogan": slogan,
        "instagram_url": instagram_url,
        "tiktok_url": tiktok_url,
        "whatsapp_url": whatsapp_url,
        "facebook_url": facebook_url,
        "disclaimer": disclaimer
    }
    for k, v in updates.items():
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/admin", status_code=302)

# ==========================================
# APIS ADMINISTRATIVAS (PRODUTOS & SCRAPER)
# ==========================================

@app.post("/api/admin/scrape")
async def api_scrape_url(payload: ScrapeRequest, admin_id: int = Depends(require_admin)):
    data = await extract_product_metadata(payload.url)
    return data

@app.post("/api/admin/products")
async def api_create_product(payload: ProductCreateUpdate, admin_id: int = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()

    discount = 0
    if payload.original_price and payload.current_price and payload.original_price > payload.current_price:
        discount = int(((payload.original_price - payload.current_price) / payload.original_price) * 100)

    cursor.execute("""
        INSERT INTO products (
            title, category, store, original_price, current_price, discount_percent,
            image_url, affiliate_url, is_featured, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        payload.title, payload.category, payload.store, payload.original_price,
        payload.current_price, discount, payload.image_url, payload.affiliate_url,
        payload.is_featured, payload.is_active
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"status": "success", "id": new_id}

@app.get("/api/admin/products/{product_id}")
async def api_get_product(product_id: int, admin_id: int = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return dict(row)

@app.put("/api/admin/products/{product_id}")
async def api_update_product(product_id: int, payload: ProductCreateUpdate, admin_id: int = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()

    discount = 0
    if payload.original_price and payload.current_price and payload.original_price > payload.current_price:
        discount = int(((payload.original_price - payload.current_price) / payload.original_price) * 100)

    cursor.execute("""
        UPDATE products SET
            title = ?, category = ?, store = ?, original_price = ?, current_price = ?,
            discount_percent = ?, image_url = ?, affiliate_url = ?, is_featured = ?, is_active = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        payload.title, payload.category, payload.store, payload.original_price,
        payload.current_price, discount, payload.image_url, payload.affiliate_url,
        payload.is_featured, payload.is_active, product_id
    ))
    conn.commit()
    conn.close()
    return {"status": "updated"}

@app.patch("/api/admin/products/{product_id}/status")
async def api_toggle_status(product_id: int, payload: StatusUpdate, admin_id: int = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET is_active = ? WHERE id = ?", (payload.is_active, product_id))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.patch("/api/admin/products/{product_id}/featured")
async def api_toggle_featured(product_id: int, payload: FeaturedUpdate, admin_id: int = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET is_featured = ? WHERE id = ?", (payload.is_featured, product_id))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.delete("/api/admin/products/{product_id}")
async def api_delete_product(product_id: int, admin_id: int = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}
