// JavaScript do Frontend - V Variedades
document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('searchInput');
  const clearSearch = document.getElementById('clearSearch');
  const categoryTabs = document.querySelectorAll('.cat-pill');
  const mainGrid = document.getElementById('mainGrid');
  const featuredGrid = document.getElementById('featuredGrid');
  const featuredSection = document.getElementById('featuredSection');
  const emptyState = document.getElementById('emptyState');
  const productCount = document.getElementById('productCount');

  let allProducts = [];
  let currentCategory = 'all';
  let searchTerm = '';

  // Formatação de Preço em Real Brasileiro
  function formatMoney(amount) {
    if (amount === null || amount === undefined || isNaN(amount)) return '';
    return Number(amount).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  // Criação do Elemento HTML do Card
  function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';

    // Badge de Desconto
    const discountBadge = product.discount_percent > 0 
      ? `<span class="badge-discount">-${product.discount_percent}%</span>` 
      : '';

    // Badge de Destaque
    const featuredBadge = product.is_featured 
      ? `<span class="badge-featured"><i class="fa-solid fa-star"></i> Top</span>` 
      : '';

    // Preços
    let priceHtml = '';
    if (product.current_price) {
      const oldPriceHtml = product.original_price && product.original_price > product.current_price
        ? `<span class="card-old-price">R$ ${formatMoney(product.original_price)}</span>`
        : '';
      
      priceHtml = `
        <div class="card-pricing">
          ${oldPriceHtml}
          <div class="card-current-price"><small>R$</small>${formatMoney(product.current_price)}</div>
        </div>
      `;
    } else {
      priceHtml = `
        <div class="card-pricing">
          <div class="card-current-price" style="font-size:0.95rem; color:var(--primary);">Confira o Preço</div>
        </div>
      `;
    }

    // Imagem fallback caso a URL original falhe
    const safeImage = product.image_url || 'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=600&auto=format&fit=crop&q=80';

    card.innerHTML = `
      <div class="card-img-wrap">
        ${discountBadge}
        ${featuredBadge}
        <img src="${safeImage}" alt="${product.title}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=600&auto=format&fit=crop&q=80';">
      </div>
      <div class="card-body">
        <span class="card-store">${product.store || 'Loja Parceira'}</span>
        <h3 class="card-title" title="${product.title}">${product.title}</h3>
        ${priceHtml}
        <a href="${product.affiliate_url}" target="_blank" rel="noopener noreferrer nofollow" class="btn-offer">
          <span>VER OFERTA</span>
          <i class="fa-solid fa-arrow-up-right-from-square"></i>
        </a>
      </div>
    `;

    return card;
  }

  // Filtragem e Renderização
  function renderProducts() {
    const filtered = allProducts.filter(p => {
      // Filtro de Categoria
      const matchCategory = (currentCategory === 'all') || (p.category.toLowerCase() === currentCategory.toLowerCase());
      
      // Filtro de Busca por Título e Loja
      const matchSearch = searchTerm === '' || 
        p.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.store.toLowerCase().includes(searchTerm.toLowerCase());

      return matchCategory && matchSearch;
    });

    // Seção Destaques
    const featuredItems = filtered.filter(p => p.is_featured);
    featuredGrid.innerHTML = '';
    
    // Ocultar destaques se o usuário estiver fazendo uma pesquisa textual ou se não houver destaques
    if (featuredItems.length > 0 && searchTerm === '') {
      featuredSection.style.display = 'block';
      featuredItems.forEach(item => {
        featuredGrid.appendChild(createProductCard(item));
      });
    } else {
      featuredSection.style.display = 'none';
    }

    // Grid Principal (demais produtos ou todos os produtos)
    mainGrid.innerHTML = '';
    if (filtered.length === 0) {
      emptyState.style.display = 'block';
      productCount.textContent = '0 itens';
    } else {
      emptyState.style.display = 'none';
      productCount.textContent = `${filtered.length} ${filtered.length === 1 ? 'item' : 'itens'}`;
      filtered.forEach(item => {
        mainGrid.appendChild(createProductCard(item));
      });
    }
  }

  // Carregar dados da API
  async function loadProducts() {
    try {
      const response = await fetch('/api/products');
      if (response.ok) {
        allProducts = await response.json();
        renderProducts();
      }
    } catch (err) {
      console.error('Erro ao carregar produtos:', err);
    }
  }

  // Eventos de Busca
  searchInput.addEventListener('input', (e) => {
    searchTerm = e.target.value.trim();
    clearSearch.style.display = searchTerm.length > 0 ? 'block' : 'none';
    renderProducts();
  });

  clearSearch.addEventListener('click', () => {
    searchInput.value = '';
    searchTerm = '';
    clearSearch.style.display = 'none';
    renderProducts();
  });

  // Eventos de Categorias
  categoryTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      categoryTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentCategory = tab.getAttribute('data-category');
      renderProducts();
    });
  });

  // Inicialização
  loadProducts();
});
