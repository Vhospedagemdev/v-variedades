// Funções do Painel Administrativo
const modal = document.getElementById('productModal');
const productForm = document.getElementById('productForm');
const modalTitle = document.getElementById('modalTitle');
const prodImageUrl = document.getElementById('prodImageUrl');
const imagePreviewBox = document.getElementById('imagePreviewBox');
const imagePreview = document.getElementById('imagePreview');
const urlFetchForm = document.getElementById('urlFetchForm');
const btnFetchData = document.getElementById('btnFetchData');
const btnManualAdd = document.getElementById('btnManualAdd');

// Atualização de preview da imagem ao digitar URL
if (prodImageUrl) {
  prodImageUrl.addEventListener('input', () => {
    if (prodImageUrl.value.trim().length > 5) {
      imagePreview.src = prodImageUrl.value.trim();
      imagePreviewBox.style.display = 'block';
    } else {
      imagePreviewBox.style.display = 'none';
    }
  });
}

function openModal() {
  modal.classList.add('active');
}

function closeProductModal() {
  modal.classList.remove('active');
  productForm.reset();
  document.getElementById('prodId').value = '';
  imagePreviewBox.style.display = 'none';
}

if (btnManualAdd) {
  btnManualAdd.addEventListener('click', () => {
    productForm.reset();
    document.getElementById('prodId').value = '';
    modalTitle.textContent = 'Adicionar Novo Produto';
    openModal();
  });
}

// Extração Inteligente de Texto Colado (Smart Paste)
const btnSmartParse = document.getElementById('btnSmartParse');
const smartPasteText = document.getElementById('smartPasteText');

if (btnSmartParse && smartPasteText) {
  btnSmartParse.addEventListener('click', () => {
    const raw = smartPasteText.value.trim();
    if (!raw) {
      alert('Por favor, cole um texto com título, preço ou link antes.');
      return;
    }

    productForm.reset();
    document.getElementById('prodId').value = '';
    modalTitle.textContent = 'Adicionar Produto (Extraído do Texto)';

    // Extrai URLs
    const urls = raw.match(/https?:\/\/[^\s"'<>]+/gi) || [];
    let imgUrl = '';
    let affUrl = '';

    urls.forEach(u => {
      if (u.match(/\.(jpg|jpeg|png|webp|avif)/i) || u.includes('mlstatic.com') || u.includes('susercontent.com')) {
        if (!imgUrl) imgUrl = u;
      } else {
        if (!affUrl) affUrl = u;
      }
    });

    // Detecta loja
    let storeName = 'Shopee';
    if (raw.toLowerCase().includes('mercado livre') || (affUrl && affUrl.includes('mercadolivre'))) {
      storeName = 'Mercado Livre';
    } else if (raw.toLowerCase().includes('amazon') || (affUrl && affUrl.includes('amazon'))) {
      storeName = 'Amazon';
    } else if (raw.toLowerCase().includes('aliexpress') || (affUrl && affUrl.includes('aliexpress'))) {
      storeName = 'AliExpress';
    } else if (raw.toLowerCase().includes('shopee') || (affUrl && affUrl.includes('shopee'))) {
      storeName = 'Shopee';
    }

    // Extrai preços (R$ xx,xx ou xx.xx)
    const priceMatches = raw.match(/R\$\s*[\d\.,]+/gi) || [];
    let prices = [];
    priceMatches.forEach(p => {
      let num = p.replace(/[^\d,\.]/g, '').trim();
      if (num.includes(',') && num.includes('.')) {
        num = num.replace('.', '').replace(',', '.');
      } else if (num.includes(',')) {
        num = num.replace(',', '.');
      }
      const val = parseFloat(num);
      if (!isNaN(val) && val > 0 && !prices.includes(val)) {
        prices.push(val);
      }
    });

    // Extrai título (primeira linha não vazia que não seja só preço ou url)
    const lines = raw.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    let title = '';
    for (const line of lines) {
      if (!line.startsWith('http') && !line.startsWith('R$') && line.length > 5) {
        title = line;
        break;
      }
    }

    document.getElementById('prodTitle').value = title || 'Novo Produto';
    document.getElementById('prodStore').value = storeName;
    document.getElementById('prodAffiliateUrl').value = affUrl || '';
    document.getElementById('prodImageUrl').value = imgUrl || '';

    if (prices.length === 1) {
      document.getElementById('prodCurrentPrice').value = prices[0];
    } else if (prices.length >= 2) {
      // Ordena: o menor é o preço promocional, o maior é o antigo
      prices.sort((a, b) => a - b);
      document.getElementById('prodCurrentPrice').value = prices[0];
      document.getElementById('prodOriginalPrice').value = prices[1];
    }

    if (imgUrl) {
      imagePreview.src = imgUrl;
      imagePreviewBox.style.display = 'block';
    }

    openModal();
  });
}

// Busca Automática de Metadados via URL
if (urlFetchForm) {
  urlFetchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = document.getElementById('scrapeUrl').value.trim();
    if (!url) return;

    btnFetchData.disabled = true;
    btnFetchData.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Obtendo informações...';

    try {
      const response = await fetch('/api/admin/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });

      const data = await response.json();

      productForm.reset();
      document.getElementById('prodId').value = '';
      modalTitle.textContent = 'Adicionar Produto (Dados Identificados)';

      // Preenche os campos identificados
      document.getElementById('prodTitle').value = data.title || '';
      document.getElementById('prodStore').value = data.store || 'Loja Parceira';
      document.getElementById('prodAffiliateUrl').value = data.affiliate_url || url;
      document.getElementById('prodImageUrl').value = data.image_url || '';
      
      if (data.current_price) {
        document.getElementById('prodCurrentPrice').value = data.current_price;
      }
      if (data.original_price) {
        document.getElementById('prodOriginalPrice').value = data.original_price;
      }

      if (data.image_url) {
        imagePreview.src = data.image_url;
        imagePreviewBox.style.display = 'block';
      }

      openModal();
    } catch (err) {
      alert('Não foi possível obter dados automaticamente desta página. Você pode preenchê-los manualmente.');
      openModal();
    } finally {
      btnFetchData.disabled = false;
      btnFetchData.innerHTML = '<i class="fa-solid fa-bolt"></i> Obter Dados Automaticamente';
    }
  });
}

// Salvar / Editar Produto
if (productForm) {
  productForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('prodId').value;
    const isEdit = !!id;

    // Converte categoria limpando emojis se necessário para o banco
    const categoryRaw = document.getElementById('prodCategory').value;
    const categoryClean = categoryRaw.replace(/^[^\w\sÀ-ÿ]+/, '').trim();

    const payload = {
      title: document.getElementById('prodTitle').value.trim(),
      category: categoryClean,
      store: document.getElementById('prodStore').value.trim(),
      current_price: parseFloat(document.getElementById('prodCurrentPrice').value) || null,
      original_price: parseFloat(document.getElementById('prodOriginalPrice').value) || null,
      image_url: document.getElementById('prodImageUrl').value.trim(),
      affiliate_url: document.getElementById('prodAffiliateUrl').value.trim(),
      is_featured: document.getElementById('prodIsFeatured').checked ? 1 : 0,
      is_active: document.getElementById('prodIsActive').checked ? 1 : 0
    };

    const endpoint = isEdit ? `/api/admin/products/${id}` : '/api/admin/products';
    const method = isEdit ? 'PUT' : 'POST';

    try {
      const res = await fetch(endpoint, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        window.location.reload();
      } else {
        const err = await res.json();
        alert('Erro ao salvar produto: ' + (err.detail || 'Verifique os campos.'));
      }
    } catch (err) {
      alert('Erro ao salvar produto.');
    }
  });
}

// Abrir Edição de Produto
async function openEditModal(productId) {
  try {
    const res = await fetch(`/api/admin/products/${productId}`);
    if (res.ok) {
      const p = await res.json();
      modalTitle.textContent = 'Editar Produto #' + p.id;
      document.getElementById('prodId').value = p.id;
      document.getElementById('prodTitle').value = p.title;
      document.getElementById('prodStore').value = p.store;
      document.getElementById('prodCurrentPrice').value = p.current_price || '';
      document.getElementById('prodOriginalPrice').value = p.original_price || '';
      document.getElementById('prodImageUrl').value = p.image_url;
      document.getElementById('prodAffiliateUrl').value = p.affiliate_url;
      document.getElementById('prodIsFeatured').checked = p.is_featured === 1;
      document.getElementById('prodIsActive').checked = p.is_active === 1;

      // Selecionar categoria
      const catSelect = document.getElementById('prodCategory');
      for (let i = 0; i < catSelect.options.length; i++) {
        if (catSelect.options[i].value.includes(p.category)) {
          catSelect.selectedIndex = i;
          break;
        }
      }

      if (p.image_url) {
        imagePreview.src = p.image_url;
        imagePreviewBox.style.display = 'block';
      }

      openModal();
    }
  } catch (err) {
    alert('Erro ao carregar dados do produto.');
  }
}

// Excluir Produto
async function deleteProduct(productId) {
  if (!confirm('Deseja realmente excluir este produto?')) return;
  try {
    const res = await fetch(`/api/admin/products/${productId}`, { method: 'DELETE' });
    if (res.ok) {
      window.location.reload();
    } else {
      alert('Erro ao excluir produto.');
    }
  } catch (err) {
    alert('Erro de comunicação.');
  }
}

// Alternar Status Ativo/Inativo
async function toggleProductStatus(productId, newStatus) {
  try {
    const res = await fetch(`/api/admin/products/${productId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active: newStatus })
    });
    if (res.ok) {
      window.location.reload();
    }
  } catch (err) {
    alert('Erro ao alterar status.');
  }
}

// Alternar Destaque
async function toggleProductFeatured(productId, newFeatured) {
  try {
    const res = await fetch(`/api/admin/products/${productId}/featured`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_featured: newFeatured })
    });
    if (res.ok) {
      window.location.reload();
    }
  } catch (err) {
    alert('Erro ao alterar destaque.');
  }
}
