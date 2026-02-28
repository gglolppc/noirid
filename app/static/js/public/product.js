(() => {
  // ===== BOOTSTRAP DATA =====
  const PD = window.PRODUCT_DATA || {};
  const variants = PD.variants || [];
  const productSlug = PD.productSlug || null;
  const productId = PD.productId || null;

  // ===== DOM (lazy-safe) =====
  const $ = (id) => document.getElementById(id);

  // Elements used across modules
  const els = {
    previewSpinner: null,
    previewBadge: null,
    helperHint: null,
    mainImg: null,
    priceValue: null,

    mobileStickyBar: null,
    mobilePriceValue: null,
    addToCartBtnMobile: null,

    sheen: null,
    thumbs: [],
    prevBtn: null,
    nextBtn: null,

    addToCartBtn: null,
    cartToast: null,
    toastMessage: null,

    modelWrap: null,
  };

    let scrollY = 0;

    function lockBodyScroll() {
      scrollY = window.scrollY;

      document.body.style.position = 'fixed';
      document.body.style.top = `-${scrollY}px`;
      document.body.style.left = '0';
      document.body.style.right = '0';
    }

    function unlockBodyScroll() {
      document.body.style.position = '';
      document.body.style.top = '';
      document.body.style.left = '';
      document.body.style.right = '';

      window.scrollTo(0, scrollY);
    }

  function openMobileSheet(options, onSelect) {
      const sheet = document.getElementById('mobileSelectSheet');
      const content = document.getElementById('sheetContent');
      const list = document.getElementById('sheetOptions');
      setStickyVisible(false);
      lockBodyScroll();


      list.innerHTML = options.map(opt => `
        <div class="py-4 px-4 text-white text-base
                    border-b border-white/5
                    active:bg-white/10"
             data-value="${opt}">
          ${opt}
        </div>
      `).join('');

      list.querySelectorAll('[data-value]').forEach(item => {
        item.onclick = () => {
          onSelect(item.dataset.value);
          closeMobileSheet();
        };
      });

      sheet.classList.remove('opacity-0', 'pointer-events-none');
      content.classList.remove('translate-y-full');
    }

    function closeMobileSheet() {
      const sheet = document.getElementById('mobileSelectSheet');
      const content = document.getElementById('sheetContent');

      sheet.classList.add('opacity-0', 'pointer-events-none');
      content.classList.add('translate-y-full');
      setStickyVisible(true);
      unlockBodyScroll();
    }

    function updatePriceUI() {
      // desktop price
      if (selectedVariant && els.priceValue) {
        const p = Number(selectedVariant.price);
        if (!Number.isNaN(p)) {
          els.priceValue.innerHTML = `${p.toFixed(2)} <span class="text-xs md:text-sm not-italic uppercase opacity-40">€</span>`;
        }
      }

      // mobile price
      if (selectedVariant && els.mobilePriceValue) {
        const p = Number(selectedVariant.price);
        if (!Number.isNaN(p)) {
          els.mobilePriceValue.textContent = `${p.toFixed(2)} €`;
        }
      }
    }

  function hydrateDomRefs() {
    els.showPreviewBtn = $('showPreviewBtn');
    els.mobileStickyBar = $('mobileStickyBar');
    els.mobilePriceValue = $('mobilePriceValue');
    els.addToCartBtnMobile = $('addToCartBtnMobile');
    els.previewSpinner = $('previewSpinner');
    els.previewBadge = $('previewBadge');
    els.helperHint = $('helperHint');
    els.mainImg = $('mainProductImg');
    els.priceValue = $('priceValue');

    els.sheen = $('gallerySheen');
    els.thumbs = Array.from(document.querySelectorAll('.thumb-btn'));
    els.prevBtn = $('galleryPrev');
    els.nextBtn = $('galleryNext');

    els.addToCartBtn = $('addToCartBtn');
    els.cartToast = $('cartToast');
    els.toastMessage = $('toastMessage');

    els.modelWrap = $('modelWrap');
  }

  // ===== STATE =====
  let selectedBrand = null;
  let selectedModel = null;
  let selectedVariant = null;

  const previewState = {
    abort: null,
    isRunning: false,
    lastPersonalizationHash: '',
    previewUrl: null,
  };

  let galleryIndex = 0;
  let galleryLocked = false;
  let pendingGalleryIndex = null;

  let previewDebounceTimer = null;

  // ===== UTIL =====

  function setStickyVisible(isVisible) {
      if (!els.mobileStickyBar) return;
      els.mobileStickyBar.classList.toggle('translate-y-full', !isVisible);
      els.mobileStickyBar.classList.toggle('opacity-0', !isVisible);
      els.mobileStickyBar.classList.toggle('pointer-events-none', !isVisible);
    }

  function setHint(text) {
      if (els.helperHint) els.helperHint.textContent = text;

      const mobileHint = document.getElementById('helperHintMobile');
      if (mobileHint) mobileHint.textContent = text;
    }

  function setPreviewLoading(isLoading) {
    if (!els.previewSpinner || !els.previewBadge) return;
    if (isLoading) {
      els.previewSpinner.classList.remove('hidden');
      els.previewBadge.classList.add('hidden');
    } else {
      els.previewSpinner.classList.add('hidden');
    }
  }

  function notify(msg, isError = false) {
    const toast = els.cartToast;
    const m = els.toastMessage;
    if (!toast || !m) return;

    const viewBagLink = toast.querySelector('a[href="/cart"]');

    m.textContent = msg;
    m.className = isError
      ? 'text-[10px] font-black uppercase tracking-[0.2em] text-red-500'
      : 'text-[10px] font-black uppercase tracking-[0.2em] text-black';

    if (viewBagLink) {
      viewBagLink.style.display = msg.toLowerCase().includes('bag') ? 'block' : 'none';
    }

    toast.classList.remove('opacity-0', 'translate-y-8', 'pointer-events-none');
    setTimeout(() => {
      toast.classList.add('opacity-0', 'translate-y-8', 'pointer-events-none');
    }, 3000);
  }

  function wrapIndex(i, len) {
    if (!len) return 0;
    return (i % len + len) % len;
  }

  // ===== MODEL SORT (your logic) =====
  function normalizeModelName(s) {
    return String(s || '').trim().toLowerCase();
  }

  function parseModel(s) {
    const t = normalizeModelName(s);

    const numMatch = t.match(/\b(\d{1,2})\b/);
    const num = numMatch ? Number(numMatch[1]) : -1;

    let tier = 0;
    if (/\bultra\b/.test(t)) tier = 50;
    else if (/\bpro\s*max\b/.test(t)) tier = 45;
    else if (/\bpro\b/.test(t)) tier = 40;
    else if (/\bplus\b/.test(t)) tier = 30;
    else if (/\bedge\b/.test(t)) tier = 25;
    else if (/\bair\b/.test(t)) tier = 20;
    else tier = 10;

    return { num, tier };
  }

  function modelCompare(a, b) {
    const A = parseModel(a);
    const B = parseModel(b);

    if (A.num !== B.num) return B.num - A.num;
    if (A.tier !== B.tier) return B.tier - A.tier;
    return normalizeModelName(a).localeCompare(normalizeModelName(b));
  }

  // ===== SELECT UI =====
  function closeAllSelects() {
    document.querySelectorAll('.select-options').forEach(el => {
      el.classList.add('opacity-0', 'invisible');
      const arrow = el.parentElement?.querySelector?.('.arrow');
      if (arrow) arrow.style.transform = 'rotate(0deg)';
    });
  }

  function initCustomSelect(containerId, options, onSelect) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const trigger = container.querySelector('.select-trigger');
    const optionsList = container.querySelector('.select-options');
    const label = trigger?.querySelector?.('.selected-value');
    const arrow = trigger?.querySelector?.('.arrow');

    if (!trigger || !optionsList || !label) return;

    trigger.onclick = (e) => {
      e.stopPropagation();

      // 📱 MOBILE → open bottom sheet instead of dropdown
      if (window.innerWidth < 768) {
        openMobileSheet(options, (val) => {
          label.textContent = val;
          label.classList.remove('text-zinc-400', 'italic');
          label.classList.add('text-white');
          onSelect(val);

        });
        return;
      }

      // 🖥 DESKTOP → default dropdown
      const isVisible = !optionsList.classList.contains('opacity-0');
      closeAllSelects();
      if (!isVisible) {
        optionsList.classList.remove('opacity-0', 'invisible');
        if (arrow) arrow.style.transform = 'rotate(180deg)';
      }
    };


    optionsList.innerHTML = options.map(opt => `
    <div class="select-item px-6 py-4 text-zinc-400 hover:text-white cursor-pointer text-[12px] uppercase tracking-widest transition-all"
         data-value="${String(opt).replace(/"/g, '&quot;')}">
      ${opt}
    </div>
  `).join('');

    optionsList.querySelectorAll('[data-value]').forEach(item => {
      item.onclick = (e) => {
        e.stopPropagation();
        const val = item.getAttribute('data-value');
        label.textContent = val;
        label.classList.remove('text-zinc-400', 'italic');
        label.classList.add('text-white');
        closeAllSelects();
        onSelect(val);
      };
    });
  }

  // ===== PERSONALIZATION =====
  function collectPersonalization({ requireAll }) {
    const inputs = document.querySelectorAll('[data-personalization-key]');
    const out = {};
    let anyFilled = false;

    for (const i of inputs) {
      const key = i.getAttribute('data-personalization-key');
      const val = (i.value || '').trim();
      if (val) anyFilled = true;
      if (requireAll && !val) return { ok: false, personalization: null };
      if (val) out[key] = val;
    }
    if (!anyFilled) return { ok: false, personalization: null };
    return { ok: true, personalization: out };
  }

  function getPersonalizationHash(p) {
    if (!p || typeof p !== 'object') return '';
    const keys = Object.keys(p).sort();
    return keys.map(k => `${k}=${JSON.stringify(p[k])}`).join('|');
  }

  function shouldSkipPreview(newP) {
    const hash = getPersonalizationHash(newP);
    if (hash === previewState.lastPersonalizationHash) return true;
    if (!hash) return true;

    const values = Object.values(newP).map(v => String(v || '').trim());


    return false;
  }

  // ===== GALLERY =====
  function setActiveThumb(idx) {
    els.thumbs.forEach((b, i) => {
      b.classList.toggle('ring-2', i === idx);
      b.classList.toggle('ring-white/30', i === idx);
      b.classList.toggle('bg-white/10', i === idx);
    });

    const active = els.thumbs[idx];
    if (active) active.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
  }

  async function setMainImageAnimated(url, { isPreview = false } = {}) {
    if (!els.mainImg || !url) return;
    if (galleryLocked) return;

    galleryLocked = true;

    try {
      if (!isPreview) {
        previewState.previewUrl = null;
        els.previewBadge?.classList.add('hidden');
      }

      els.mainImg.classList.add('gallery-leave');
      els.sheen?.classList.add('sheen-on');
      await new Promise(r => setTimeout(r, 140));

      const prevSrc = els.mainImg.src;
      els.mainImg.src = url;

      if (!els.mainImg.complete || els.mainImg.naturalWidth === 0) {
        await new Promise((resolve) => {
          const done = () => {
            els.mainImg.onload = null;
            els.mainImg.onerror = null;
            resolve();
          };
          els.mainImg.onload = done;
          els.mainImg.onerror = () => {
            if (prevSrc) els.mainImg.src = prevSrc;
            done();
          };
        });
      }

      els.mainImg.classList.remove('gallery-leave');
      els.mainImg.classList.add('gallery-enter');
      await new Promise(r => setTimeout(r, 520));

    } finally {
      els.sheen?.classList.remove('sheen-on');
      els.mainImg?.classList.remove('gallery-enter');
      galleryLocked = false;
    }
  }

  async function goToIndex(nextIdx) {
    if (!els.thumbs.length) return;

    if (galleryLocked) {
      pendingGalleryIndex = nextIdx;
      return;
    }

    galleryIndex = wrapIndex(nextIdx, els.thumbs.length);
    const src = els.thumbs[galleryIndex].dataset.src;

    setActiveThumb(galleryIndex);
    await setMainImageAnimated(src, { isPreview: false });

    if (pendingGalleryIndex !== null) {
      const last = pendingGalleryIndex;
      pendingGalleryIndex = null;
      await goToIndex(last);
    }
  }

  function initGallery() {
    if (!els.thumbs.length) return;

    setActiveThumb(0);
    galleryIndex = 0;

    els.thumbs.forEach((btn, i) => btn.addEventListener('click', () => goToIndex(i)));
    els.prevBtn?.addEventListener('click', () => goToIndex(galleryIndex - 1));
    els.nextBtn?.addEventListener('click', () => goToIndex(galleryIndex + 1));
  }

  // ===== PREVIEW =====
  function debouncedPreview({ force = false } = {}) {
    clearTimeout(previewDebounceTimer);

    if (previewState.abort) {
      try { previewState.abort.abort(); } catch (e) {}
      previewState.abort = null;
    }

    if (force) {
      void doPreview({ force: true });
      return;
    }

    previewDebounceTimer = setTimeout(() => void doPreview({ force: false }), 900);
  }

     async function doPreview({ force = false } = {}) {
      if (previewState.isRunning) return;
      if (!selectedVariant) return;

      const p = collectPersonalization({ requireAll: false });
      if (!p.ok) return;

      if (!force && shouldSkipPreview(p.personalization)) return;

      // ✅ только тут — реально начинаем генерацию
      els.showPreviewBtn?.classList.add('hidden');

      previewState.isRunning = true;
      previewState.lastPersonalizationHash = getPersonalizationHash(p.personalization);

      setPreviewLoading(true);
      setHint('Generating preview…');

      try {
      previewState.abort = new AbortController();

      const res = await fetch('/api/mockups/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: previewState.abort.signal,
        body: JSON.stringify({
          product_slug: productSlug,
          variant_id: selectedVariant.id,
          personalization: p.personalization,
        }),
      });

      previewState.previewUrl = res.headers.get('X-Preview-Url');

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);

      await setMainImageAnimated(url, { isPreview: true });
      els.previewBadge?.classList.remove('hidden');
      setHint('Preview ready · customize further or add to bag');


      if (els.showPreviewBtn) {
         els.showPreviewBtn.classList.remove('hidden');
      }


    } catch (e) {
      if (e.name !== 'AbortError') {
        console.warn('Preview fetch failed:', e);
        setHint('Preview failed — try again');
      }
    } finally {
      previewState.isRunning = false;
      previewState.abort = null;
      setPreviewLoading(false);
    }
  }

  // ===== PRICE =====
  function updatePriceUI() {
    if (!selectedVariant || !els.priceValue) return;
    const p = Number(selectedVariant.price);
    if (!Number.isNaN(p)) {
      els.priceValue.innerHTML = `${p.toFixed(2)} <span class="text-xs md:text-sm not-italic uppercase opacity-40">€</span>`;
    }
  }

  // ===== SCROLL =====
function scrollToPreview() {
  if (window.innerWidth < 1024) {
    const previewElement = document.getElementById('product-preview');

    if (previewElement) {
      const yOffset = -100; // на 100px выше
      const y = previewElement.getBoundingClientRect().top + window.pageYOffset + yOffset;

      window.scrollTo({
        top: y,
        behavior: 'smooth'
      });
    }
  }
}

  // ===== INPUT LISTENERS =====
 function initPersonalizationListeners() {
  document.querySelectorAll('[data-personalization-key]').forEach(inp => {
    inp.addEventListener('input', (e) => {
      // убрать подсветку ошибки
      e.target.classList.remove(
        'border-white/50',
        'ring-1',
        'ring-white/40'
      );

      debouncedPreview();
    });
  });
}

  // ===== BRAND → MODEL =====
  function initBrandModel() {
    const brands = [...new Set(variants.map(v => v.brand))].sort();

    initCustomSelect('brandCustomSelect', brands, (brand) => {
      selectedBrand = brand;
      selectedModel = null;
      selectedVariant = null;
      previewState.previewUrl = null;
      els.showPreviewBtn?.classList.add('hidden');

      setHint('Select your model to generate preview');



      if (els.modelWrap) {
        els.modelWrap.classList.remove('opacity-20', 'pointer-events-none');
      }

      const models = variants
        .filter(v => v.brand === brand)
        .map(v => v.model);

      const uniqueSortedModels = [...new Set(models)].sort(modelCompare);

      initCustomSelect('modelCustomSelect', uniqueSortedModels, (model) => {
        els.showPreviewBtn?.classList.add('hidden');
        selectedModel = model;
        selectedVariant = variants.find(v => v.brand === selectedBrand && v.model === selectedModel);

        updatePriceUI();
        setHint('Type personalization to generate preview');

        // Смена модели должна всегда считать превью устаревшим
        previewState.lastPersonalizationHash = '';
        previewState.previewUrl = null;

        // Если уже есть введённая персонализация — ререндерим сразу
        const p = collectPersonalization({ requireAll: false });
        if (p.ok) {
          debouncedPreview({ force: true });
        }
      });
    });
  }

  // ===== COORDS WIDGET =====
  let currentHems = { lat: 'N', lng: 'W' };

  function toggleHem(type, val) {
    currentHems[type] = val;
    document.querySelectorAll(`[id^="btn-${type}-"]`).forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.getElementById(`btn-${type}-${val}`);
    if (activeBtn) activeBtn.classList.add('active');
    syncCoords();
  }

  function syncCoords() {
    const lat = document.getElementById('latInput')?.value?.trim() || '0.0000';
    const lng = document.getElementById('lngInput')?.value?.trim() || '0.0000';
    const final = `${lat}° ${currentHems.lat}\n${lng}° ${currentHems.lng}`;

    const hidden = document.getElementById('finalCoords');
    if (hidden) {
      hidden.value = final;
      debouncedPreview();
    }
  }

  function initCoordsListeners() {
    ['latInput', 'lngInput'].forEach(id => {
      const el = document.getElementById(id);
      if (!el) return;
      el.addEventListener('input', () => syncCoords());
      el.addEventListener('change', () => syncCoords());
    });

    // init hemispheres if widget exists
    if (document.getElementById('coordsWidget')) {
      toggleHem('lat', 'N');
      toggleHem('lng', 'W');
    }
  }

  // expose for HTML onclick
  window.toggleHem = toggleHem;
  window.getCurrentLocation = getCurrentLocation;

  // ===== GOOGLE AUTOCOMPLETE =====
  let autocomplete;

  // ===== GOOGLE AUTOCOMPLETE (REWRITTEN) =====
  async function initAutocomplete() {
    const input = document.getElementById('locationSearch');
    if (!input) return;

    try {
      // Явно импортируем библиотеку мест
      const { Autocomplete } = await google.maps.importLibrary("places");

      const options = {
        fields: ['geometry', 'name'],
        types: ['geocode'],
      };

      autocomplete = new Autocomplete(input, options);

      // Предотвращаем отправку формы по Enter в поиске
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') e.preventDefault();
      });

      autocomplete.addListener('place_changed', () => {
        const place = autocomplete.getPlace();

        if (!place.geometry || !place.geometry.location) {
          notify('Location details not found', true);
          return;
        }

        const lat = place.geometry.location.lat();
        const lng = place.geometry.location.lng();

        // Обновляем полушария
        toggleHem('lat', lat >= 0 ? 'N' : 'S');
        toggleHem('lng', lng >= 0 ? 'E' : 'W');

        // Заполняем инпуты
        const latInput = document.getElementById('latInput');
        const lngInput = document.getElementById('lngInput');

        if (latInput) latInput.value = Math.abs(lat).toFixed(4);
        if (lngInput) lngInput.value = Math.abs(lng).toFixed(4);

        // Синхронизируем и запускаем превью
        syncCoords();

        // Очищаем поиск после выбора, чтобы не мешал
        input.value = place.name || '';
      });

    } catch (e) {
      console.error("Autocomplete failed:", e);
    }
  }

  // ===== GEOLOCATION =====
  function getCurrentLocation() {
    if (!navigator.geolocation) {
      notify('Geolocation not supported', true);
      return;
    }

    const btn = document.querySelector('button[onclick="getCurrentLocation()"]');
    btn?.classList?.add('animate-pulse');

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude: lat, longitude: lng } = position.coords;

        toggleHem('lat', lat >= 0 ? 'N' : 'S');
        toggleHem('lng', lng >= 0 ? 'E' : 'W');

        document.getElementById('latInput').value = Math.abs(lat).toFixed(4);
        document.getElementById('lngInput').value = Math.abs(lng).toFixed(4);
        syncCoords();

        const searchInput = document.getElementById('locationSearch');
        if (searchInput) searchInput.value = 'Current Location';

        btn?.classList?.remove('animate-pulse');
        notify('Coordinates updated');
      },
      (error) => {
        btn?.classList?.remove('animate-pulse');
        console.error('Geolocation error:', error);
        notify('Failed to get location', true);
      },
      { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
    );
  }

  // ===== ADD TO CART =====
  function initAddToCart() {
      const btnDesktop = els.addToCartBtn;
      const btnMobile = els.addToCartBtnMobile;

      if (!btnDesktop && !btnMobile) return;

      const setButtonsDisabled = (disabled, html = null) => {
        [btnDesktop, btnMobile].forEach(btn => {
          if (!btn) return;
          btn.disabled = disabled;
          if (html !== null) btn.innerHTML = html;
        });
      };

      const originalDesktop = btnDesktop ? btnDesktop.innerHTML : null;
      const originalMobile = btnMobile ? btnMobile.innerHTML : null;

      const onClick = async () => {
        if (!selectedVariant) {
          setHint('Select device model to continue');
          return notify('Select Device', true);
        }

        // 1) validate personalization + highlight empty fields
        const inputs = document.querySelectorAll('[data-personalization-key]');
        let hasError = false;

        inputs.forEach(input => {
          const empty = !input.value.trim();
          if (empty) {
            hasError = true;
            input.classList.add('border-white/50', 'ring-1', 'ring-white/40');
          } else {
            input.classList.remove('border-white/50', 'ring-1', 'ring-white/40');
          }
        });

        if (hasError) {
          setHint('Fill all personalization fields');
          return notify('FILL FIELDS', true);
        }

        // 2) collect personalization (BUGFIX: p was missing)
        const p = collectPersonalization({ requireAll: true });
        if (!p.ok) {
          setHint('Fill all personalization fields');
          return notify('FILL FIELDS', true);
        }

        // 3) loading state
        const loadingHtml = '<span class="text-black text-[11px] font-bold uppercase tracking-[0.5em] animate-pulse">Wait...</span>';
        setButtonsDisabled(true, loadingHtml);

        try {
          // ensure preview exists
          if (!previewState.previewUrl) {
            await new Promise(r => setTimeout(r, 100));
            debouncedPreview({ force: true });
          }

          let attempts = 0;
          while (!previewState.previewUrl && attempts < 30) {
            await new Promise(r => setTimeout(r, 100));
            attempts++;
          }

          if (!previewState.previewUrl) throw new Error('Preview generation timed out');

          const res = await fetch('/api/cart/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              product_id: productId,
              variant_id: selectedVariant.id,
              qty: 1,
              personalization: p.personalization,
              preview_url: previewState.previewUrl,
            }),
          });

          if (res.ok) {
            const cart = await res.json().catch(() => null);
            window.dispatchEvent(new CustomEvent('cart:updated', { detail: cart }));
            setHint('Added to bag · you can checkout anytime');
            notify('Added to bag');
          } else {
            throw new Error('Add to cart failed');
          }

        } catch (e) {
          console.error('Cart add error:', e);
          setHint('Could not add to bag');
          notify('Error', true);
        } finally {
          // restore buttons
          if (btnDesktop) btnDesktop.innerHTML = originalDesktop;
          if (btnMobile) btnMobile.innerHTML = originalMobile;
          setButtonsDisabled(false, null);
        }
      };

      if (btnDesktop) btnDesktop.onclick = onClick;
      if (btnMobile) btnMobile.onclick = onClick;
    }


  // ===== INIT =====
  function initGlobalListeners() {
    document.addEventListener('click', closeAllSelects);
  }

  function init() {
    hydrateDomRefs();
    initGlobalListeners();

    setHint('Select device model to generate preview');


    if (els.showPreviewBtn) {
      els.showPreviewBtn.onclick = () => {
        scrollToPreview();
      };
    }

    initGallery();
    initBrandModel();
    initPersonalizationListeners();

    initCoordsListeners();

    // Autocomplete after maps is present
    // If google loads after this script, it still works because it checks existence
    initAutocomplete();

    initAddToCart();
  }

  document.addEventListener('DOMContentLoaded', init);
})();

