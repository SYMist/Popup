(() => {
  const qs = (s, el = document) => el.querySelector(s);
  const qsa = (s, el = document) => Array.from(el.querySelectorAll(s));
  const $list = qs('#list');
  const $meta = qs('#meta');
  const $error = qs('#error');
  const $loading = qs('#loading');
  const $loadMore = qs('#load-more');
  const $fIsPopup = qs('#f-isPopup');
  const $fStatus = qs('#f-status');
  const $fCity = qs('#f-city');
  const $fCategory = qs('#f-category');
  const $fSearch = qs('#f-search');
  const $fSort = qs('#f-sort');
  const $modal = qs('#modal');
  const $modalIframe = qs('#modal-iframe');
  const $modalTitle = qs('#modal-title');
  const $modalOpen = qs('#modal-open-page');

  let DATA = [];
  let MANIFEST = null;
  let BASE = null;
  let MONTHS = [];
  const LOADED_MONTHS = new Set();
  const INITIAL_MONTHS = 3; // 최초 로드 개월수
  const BATCH_MONTHS = 3;   // 더 보기 로드 단위

  function parseDate(s) {
    if (!s) return null;
    const m = /^\d{4}-\d{2}-\d{2}$/.exec(s);
    if (!m) return null;
    const d = new Date(s + 'T00:00:00Z');
    return isNaN(d) ? null : d;
  }

  function statusOf(e, today = new Date()) {
    const s = parseDate(e.start);
    const en = parseDate(e.end);
    const t = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()));
    if (s && t < s) return 'upcoming';
    if (en && t > en) return 'ended';
    return 'ongoing';
  }

  function textContains(hay, needle) {
    if (!needle) return true;
    if (!hay) return false;
    return hay.toLowerCase().includes(needle.toLowerCase());
  }

  function uniqSorted(arr) {
    return Array.from(new Set(arr.filter(Boolean))).sort((a, b) => a.localeCompare(b));
  }

  function fillOptions($sel, items) {
    $sel.innerHTML = '';
    for (const it of items) {
      const opt = document.createElement('option');
      opt.value = it; opt.textContent = it;
      $sel.appendChild(opt);
    }
  }

  function applyFilters() {
    const onlyPopup = $fIsPopup.checked;
    const status = $fStatus.value; // all|ongoing|upcoming|ended
    const cities = qsa('option:checked', $fCity).map(o => o.value);
    const cats = qsa('option:checked', $fCategory).map(o => o.value);
    const query = ($fSearch.value || '').trim();

    let rows = DATA;
    if (onlyPopup) rows = rows.filter(e => !!e.isPopup);
    if (status !== 'all') rows = rows.filter(e => statusOf(e) === status);
    if (cities.length) rows = rows.filter(e => e.city && cities.includes(e.city));
    if (cats.length) rows = rows.filter(e => e.category && cats.includes(e.category));
    if (query) rows = rows.filter(e => textContains(e.title, query));

    const sortKey = $fSort.value;
    rows = rows.slice();
    const cmpDate = (a, b, key, asc = true) => {
      const da = parseDate(a[key]);
      const db = parseDate(b[key]);
      const va = da ? da.getTime() : Infinity;
      const vb = db ? db.getTime() : Infinity;
      return asc ? va - vb : vb - va;
    };
    const cmpText = (a, b, key, asc = true) => {
      const va = (a[key] || '').toLowerCase();
      const vb = (b[key] || '').toLowerCase();
      return asc ? va.localeCompare(vb) : vb.localeCompare(va);
    };
    if (sortKey === 'end-asc') rows.sort((a, b) => cmpDate(a, b, 'end', true));
    if (sortKey === 'end-desc') rows.sort((a, b) => cmpDate(a, b, 'end', false));
    if (sortKey === 'start-asc') rows.sort((a, b) => cmpDate(a, b, 'start', true));
    if (sortKey === 'start-desc') rows.sort((a, b) => cmpDate(a, b, 'start', false));
    if (sortKey === 'title-asc') rows.sort((a, b) => cmpText(a, b, 'title', true));
    if (sortKey === 'title-desc') rows.sort((a, b) => cmpText(a, b, 'title', false));

    render(rows);
  }

  function render(rows) {
    $list.innerHTML = '';
    const tpl = qs('#card-tpl');
    for (const e of rows) {
      const node = tpl.content.firstElementChild.cloneNode(true);
      const $a = qs('.thumb-link', node);
      const $img = qs('img.thumb', node);
      const $title = qs('.title', node);
      const $dates = qs('.dates', node);
      const $city = qs('.city', node);
      const $cat = qs('.badge.cat', node);
      const $popup = qs('.badge.popup', node);
      const $status = qs('.badge.status', node);
      const $quick = qs('.btn.quick', node);

      $a.href = `p/${e.id}.html`;
      $img.src = e.thumb || '';
      $img.alt = e.title || 'thumbnail';
      $title.textContent = e.title || '(제목 없음)';
      const ds = e.start || '?';
      const de = e.end || '?';
      $dates.textContent = `${ds} ~ ${de}`;
      $city.textContent = e.city || '—';
      $cat.textContent = e.category || '—';
      $popup.style.display = e.isPopup ? 'inline-block' : 'none';
      const st = statusOf(e);
      $status.textContent = ({ongoing: '진행중', upcoming: '예정', ended: '종료'})[st];
      $status.dataset.status = st;

      if ($quick) {
        $quick.addEventListener('click', (ev) => {
          ev.preventDefault();
          openModal(e);
        });
      }

      $list.appendChild(node);
    }
    const monthsInfo = (MANIFEST && MANIFEST.mode === 'monthly' && MONTHS.length)
      ? ` · ${LOADED_MONTHS.size}/${MONTHS.length}개월`
      : '';
    $meta.textContent = `${rows.length} / ${DATA.length} 항목${monthsInfo}`;
  }

  async function fetchJSON(url) {
    const v = Date.now();
    const u = url + (url.includes('?') ? '&' : '?') + 'v=' + v;
    const res = await fetch(u);
    if (!res.ok) throw new Error('HTTP ' + res.status + ' for ' + url);
    return res.json();
  }

  function setLoading(on) {
    if (!$loading) return;
    $loading.style.display = on ? 'flex' : 'none';
    if (on) {
      if ($error) $error.style.display = 'none';
    }
  }

  function showError(message) {
    if ($error) {
      $error.textContent = message;
      $error.style.display = 'block';
    }
    if ($meta) $meta.textContent = '데이터 로딩 실패';
    console.error(message);
  }

  async function tryLoadFromBase(base) {
    // Try manifest first
    let manifest = null;
    try { manifest = await fetchJSON(`${base}/index-manifest.json`); } catch (_) { manifest = null; }
    if (!manifest || manifest.mode === 'single') {
      const rows = await fetchJSON(`${base}/index.json`);
      return { rows, manifest };
    } else if (manifest.mode === 'monthly') {
      // 지연 로딩: 여기서는 행을 즉시 로드하지 않고 manifest만 반환
      return { rows: [], manifest };
    }
    return { rows: [], manifest };
  }

  function sortMonthsDescWithUnknownLast(months) {
    const list = Array.isArray(months) ? months.slice() : [];
    const known = list.filter(m => m && m !== 'unknown').sort((a, b) => a < b ? 1 : (a > b ? -1 : 0));
    const unk = list.includes('unknown') ? ['unknown'] : [];
    return known.concat(unk);
  }

  async function loadMonth(month) {
    if (!BASE || !month || LOADED_MONTHS.has(month)) return [];
    const fname = month === 'unknown' ? 'index-unknown.json' : `index-${month}.json`;
    const url = `${BASE}/${fname}`;
    const part = await fetchJSON(url);
    if (Array.isArray(part)) {
      DATA = DATA.concat(part);
      LOADED_MONTHS.add(month);
      return part;
    }
    return [];
  }

  async function loadNextBatch(count) {
    if (!MONTHS.length) return;
    const remaining = MONTHS.filter(m => !LOADED_MONTHS.has(m));
    const take = remaining.slice(0, Math.max(1, count|0));
    if (!$loadMore) return;
    $loadMore.disabled = true;
    try {
      await Promise.all(take.map(loadMonth));
    } finally {
      $loadMore.disabled = false;
      updateOptionsPreserve();
      applyFilters();
      updateLoadMoreButton();
    }
  }

  function getSelectedValues($sel) {
    return qsa('option:checked', $sel).map(o => o.value);
  }
  function setSelectedValues($sel, values) {
    const set = new Set(values);
    qsa('option', $sel).forEach(o => { o.selected = set.has(o.value); });
  }
  function updateOptionsPreserve() {
    const selCities = getSelectedValues($fCity);
    const selCats = getSelectedValues($fCategory);
    const cities = uniqSorted(DATA.map(r => r.city));
    const cats = uniqSorted(DATA.map(r => r.category));
    fillOptions($fCity, cities);
    fillOptions($fCategory, cats);
    setSelectedValues($fCity, selCities);
    setSelectedValues($fCategory, selCats);
  }

  function updateLoadMoreButton() {
    if (!$loadMore) return;
    if (!(MANIFEST && MANIFEST.mode === 'monthly')) {
      $loadMore.style.display = 'none';
      return;
    }
    const remaining = MONTHS.filter(m => !LOADED_MONTHS.has(m)).length;
    if (remaining > 0) {
      $loadMore.style.display = 'inline-block';
      $loadMore.textContent = `이전 월 더 보기 (${remaining}개월 남음)`;
      $loadMore.disabled = false;
    } else {
      $loadMore.style.display = 'none';
    }
  }

  // Modal
  let lastFocus = null;
  function openModal(entry) {
    if (!$modal) return;
    lastFocus = document.activeElement;
    const href = `p/${entry.id}.html`;
    if ($modalTitle) $modalTitle.textContent = entry.title || '(상세)';
    if ($modalIframe) $modalIframe.src = href + `?v=${Date.now()}`;
    if ($modalOpen) {
      $modalOpen.href = href;
      $modalOpen.setAttribute('aria-label', `${entry.title || ''} 상세 페이지로 이동`);
    }
    $modal.classList.add('show');
    $modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    // focus to close button if exists
    const closeBtn = $modal.querySelector('.modal-close');
    if (closeBtn) closeBtn.focus();
  }
  function closeModal() {
    if (!$modal) return;
    $modal.classList.remove('show');
    $modal.style.display = 'none';
    document.body.style.overflow = '';
    if ($modalIframe) $modalIframe.src = '';
    if (lastFocus && typeof lastFocus.focus === 'function') {
      try { lastFocus.focus(); } catch (_) {}
    }
  }
  if ($modal) {
    $modal.addEventListener('click', (e) => {
      const t = e.target;
      if (t && (t.getAttribute('data-close') === 'true')) {
        e.preventDefault();
        closeModal();
      }
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && $modal.style.display === 'block') {
        closeModal();
      }
    });
  }

  async function loadData() {
    setLoading(true);
    const bases = ['/data', 'data', '../data'];
    let loaded = null;
    const errors = [];
    for (const b of bases) {
      try {
        const tryLoaded = await tryLoadFromBase(b);
        if (tryLoaded && tryLoaded.rows && tryLoaded.rows.length >= 0) {
          loaded = tryLoaded;
          MANIFEST = loaded.manifest;
          DATA = loaded.rows;
          BASE = b;
          break;
        }
      } catch (e) {
        errors.push({ base: b, error: e });
      }
    }
    if (!loaded) {
      setLoading(false);
      const tried = bases.join(', ');
      const last = errors.length ? (errors[errors.length - 1].error?.message || String(errors[errors.length - 1].error)) : 'unknown error';
      showError(`데이터 로딩 실패. 시도한 경로: ${tried}. 마지막 오류: ${last}.\n루트에서 /data 를 제공하거나 web/data 에 인덱스를 생성하세요.`);
      return;
    }

    if (MANIFEST && MANIFEST.mode === 'monthly') {
      MONTHS = sortMonthsDescWithUnknownLast(Array.isArray(MANIFEST.months) ? MANIFEST.months : []);
      // 초기 배치 로드
      await loadNextBatch(Math.min(INITIAL_MONTHS, MONTHS.length));
      updateLoadMoreButton();
      setLoading(false);
      return;
    }

    // single mode
    const cities = uniqSorted(DATA.map(r => r.city));
    const cats = uniqSorted(DATA.map(r => r.category));
    fillOptions($fCity, cities);
    fillOptions($fCategory, cats);
    applyFilters();
    setLoading(false);
  }

  // Events
  [$fIsPopup, $fStatus, $fSearch, $fSort].forEach(el => el.addEventListener('input', applyFilters));
  $fCity.addEventListener('change', applyFilters);
  $fCategory.addEventListener('change', applyFilters);

  document.addEventListener('DOMContentLoaded', loadData);
  if ($loadMore) $loadMore.addEventListener('click', () => loadNextBatch(BATCH_MONTHS));
})();
