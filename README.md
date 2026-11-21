# 🛍️ V Variedades - Landing Page & Vitrine de Afiliados

Landing page moderna, responsiva e mobile-first projetada para ser utilizada como página de **link na bio** do Instagram, TikTok, Facebook e redes sociais, funcionando como uma mini loja/vitrine de ofertas afiliadas.

---

## 🚀 Como Iniciar

Basta dar dois cliques no arquivo executável `start.bat` ou executar via terminal:

```bash
start.bat
```

Ou diretamente com Python:

```bash
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 🌐 Endereços de Acesso

- **Vitrine Pública (Link na Bio):** [http://localhost:8000](http://localhost:8000)
- **Painel Administrativo:** [http://localhost:8000/admin](http://localhost:8000/admin)
  - **Usuário padrão:** `admin`
  - **Senha padrão:** `admin123`

---

## 🌟 Recursos Implementados

### 1. Vitrine Pública (Mobile-First)
- **Identidade Visual:** Paleta em roxo, azul e branco (`#6366f1`, `#8b5cf6`, `#3b82f6`) com sombras suaves, gradientes discretos e tipografia moderna *Plus Jakarta Sans*.
- **Cabeçalho Compacto:** Avatar com o logotipo "V", título "V Variedades", slogan, subtítulo e botões de redes sociais configuráveis (Instagram, TikTok, WhatsApp, Facebook).
- **Destaque Principal:** Banner animado com chamada para ação e botão para rolar até as ofertas.
- **Busca Instantânea:** Barra *"🔎 O que você está procurando?"* que filtra em tempo real por nome e loja sem recarregar a página.
- **Filtro de Categorias:** Barra horizontal deslizante com botões interativos:
  - 🌟 Todos
  - 🔥 Ofertas
  - 🏠 Casa
  - 📱 Tecnologia
  - 👗 Moda
  - 💄 Beleza
  - 🐶 Pets
  - 🎮 Games
  - 🎁 Achadinhos
- **Seção ⭐ Mais Procurados:** Destaques configurados pelo administrador que aparecem no topo da vitrine.
- **Cards de Produtos:**
  - Imagem nítida centralizada com transição de zoom no hover
  - Badge de desconto em porcentagem (ex: `-53%`)
  - Badge de destaque (`⭐ Top`)
  - Badge com o nome da loja (Shopee, Amazon, Mercado Livre, AliExpress, Temu, etc.)
  - Título do produto limitado com elipse elegante
  - Preço riscado (antigo) e preço atual em destaque
  - Botão de alta conversão **“VER OFERTA”** que direciona para o link de afiliado cadastrado.
- **Rodapé Completo:** Redes sociais, termos, aviso legal obrigatório sobre monetização de afiliados (*compliance* de plataformas).

### 2. Cadastro Inteligente de Produtos & Metadados
- **Extração Automática:** Ao colar qualquer URL de produto (Shopee, Amazon, Mercado Livre, AliExpress, Temu, Magalu, etc.), o sistema inspeciona:
  - Metatags Open Graph (`og:title`, `og:image`, `product:price:amount`, etc.)
  - Metatags Twitter Card
  - Dados estruturados Schema.org / JSON-LD (`Product`, `Offer`)
  - Detecção inteligente da loja pelo domínio
- **Preenchimento Manual / Fallback:** Caso a plataforma bloqueie o acesso direto à página ou não tenha metadados públicos, o administrador pode preencher ou ajustar qualquer campo manualmente no modal.

### 3. Painel Administrativo Completo
- **Autenticação Segura:** Protegido por login com hash de senha SHA-256 + salt único criptográfico e tokens de sessão `HttpOnly` com validade.
- **Dashboard com Métricas:**
  - Total de produtos cadastrados
  - Produtos ativos na vitrine
  - Produtos em destaque
  - Categorias ativas
- **Gestão da Tabela:**
  - Ativar / Desativar produto instantaneamente
  - Marcar / Desmarcar como destaque
  - Editar qualquer informação do produto
  - Excluir produto com confirmação
- **Gestão de Configurações da Loja:** Edição rápida do nome da marca, slogan, redes sociais e aviso legal.

### 4. Arquitetura & Segurança
- **Backend:** FastAPI + Uvicorn de alta performance.
- **Banco de Dados:** SQLite (`data/v_variedades.db`) com integridade referencial, índices e persistência local.
- **SEO & Metadados:** Configurações de Open Graph prontas para exibição de thumbnail ao compartilhar no WhatsApp, Instagram, Telegram ou Facebook.
