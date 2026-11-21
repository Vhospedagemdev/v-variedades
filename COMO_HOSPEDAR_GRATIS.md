# 🚀 Guia Passo a Passo: Hospedagem 100% Gratuita na Nuvem

Este guia ensina a colocar o projeto **V Variedades** no ar na internet com link público permanente com HTTPS (cadeado verde) e sem gastar nada.

---

## 📋 Método Mais Rápido: Render.com (Gratuito)

### PASSO 1: Criar um Repositório no GitHub
1. Acesse [github.com](https://github.com) e entre na sua conta (ou crie uma gratuita).
2. Clique no botão verde **"New"** (ou **"Novo Repositório"**).
3. Nome do repositório: `v-variedades`.
4. Deixe como **Public** ou **Private** (ambos funcionam gratuitamente).
5. Clique em **"Create repository"**.
6. Na página que abrir, clique em **"uploading an existing file"** (enviar arquivos existentes).
7. Selecione e envie os arquivos da sua pasta `C:\Users\SERVIDOR\Downloads\bio`:
   - Pasta `app` (com todos os arquivos dentro)
   - `requirements.txt`
   - `Procfile`
   - `render.yaml`
   - `.gitignore`
   - `README.md`
8. Clique no botão verde **"Commit changes"**.

---

### PASSO 2: Conectar no Render.com
1. Acesse [render.com](https://render.com) e crie uma conta (você pode entrar direto com o seu GitHub com 1 clique).
2. No painel principal, clique no botão azul **"New +"** no topo e selecione **"Web Service"**.
3. Escolha **"Build and deploy from a Git repository"** e clique em **Next**.
4. Localize o seu repositório `v-variedades` e clique em **"Connect"**.
5. Preencha as configurações simples:
   - **Name:** `v-variedades` (ou o nome que preferir)
   - **Region:** Escolha `Oregon (US West)` ou `Ohio (US East)`
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Selecione **Free** ($0/month)
6. Role a página até o final e clique no botão azul **"Create Web Service"**.

---

### PASSO 3: Pegar o Link da Bio!
1. O Render iniciará a instalação dos pacotes e ligará o servidor (leva cerca de 2 minutos).
2. Assim que aparecer o status **"Live"** em verde, o seu link público estará no topo da tela, por exemplo:
   👉 `https://v-variedades.onrender.com`
3. Pronto! Esse é o link oficial para colocar na bio do Instagram, TikTok, Facebook ou WhatsApp.

---

## 🔒 Dica Bônus: Banco de Dados 100% Persistente em Nuvem (Supabase Grátis)
O Render desliga a máquina se ela ficar sem visitas por mais de 15 minutos e arquivos locais do disco podem ser resetados em novos deploys.

Se quiser que os produtos cadastrados nunca sejam perdidos, você pode ligar um banco PostgreSQL gratuito em nuvem:
1. Crie uma conta no [supabase.com](https://supabase.com) (gratuito).
2. Crie um projeto novo.
3. Em **Project Settings** -> **Database**, copie a linha de conexão **URI** (`postgresql://postgres:...`).
4. No painel do seu Web Service no **Render**, vá na aba **"Environment"** e adicione uma variável:
   - **Key:** `DATABASE_URL`
   - **Value:** Cole a URL do seu Supabase.
5. O sistema do **V Variedades** já foi programado para detectar essa variável e se conectar automaticamente!
