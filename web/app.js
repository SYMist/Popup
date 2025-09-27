(() => {
  const qs = (s, el = document) => el.querySelector(s);
  const qsa = (s, el = document) => Array.from(el.querySelectorAll(s));
  const $list = qs('#list');
  const $meta = qs('#meta');
  const $fIsPopup = qs('#f-isPopup');
  const $fStatus = qs('#f-status');
  const $fCity = qs('#f-city');
  const $fCategory = qs('#f-category');
  const $fSearch = qs('#f-search');
  const $fSort = qs('#f-sort');

  let DATA = [];
  let MANIFEST = null;

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

      $list.appendChild(node);
    }
    $meta.textContent = `${rows.length} / ${DATA.length} 항목`;
  }

  async function fetchJSON(url) {
    const v = Date.now();
    const u = url + (url.includes('?') ? '&' : '?') + 'v=' + v;
    const res = await fetch(u);
    if (!res.ok) throw new Error('HTTP ' + res.status + ' for ' + url);
    return res.json();
  }

  async function tryLoadFromBase(base) {
    // Try manifest first
    let manifest = null;
    try { manifest = await fetchJSON(`${base}/index-manifest.json`); } catch (_) { manifest = null; }
    if (!manifest || manifest.mode === 'single') {
      const rows = await fetchJSON(`${base}/index.json`);
      return { rows, manifest };
    } else if (manifest.mode === 'monthly') {
      const months = Array.isArray(manifest.months) ? manifest.months : [];
      const tasks = months.map(m => fetchJSON(`${base}/index-${m === 'unknown' ? 'unknown' : m}.json`));
      const parts = await Promise.all(tasks);
      return { rows: parts.flat(), manifest };
    }
    return { rows: [], manifest };
  }

  async function loadData() {
    const bases = ['/data', 'data', '../data'];
    let loaded = null;
    let lastErr = null;
    for (const b of bases) {
      try {
        loaded = await tryLoadFromBase(b);
        if (loaded && loaded.rows && loaded.rows.length >= 0) { // accept empty too
          MANIFEST = loaded.manifest;
          DATA = loaded.rows;
          break;
        }
      } catch (e) { lastErr = e; }
    }
    if (!loaded) {
      $meta.textContent = '데이터 로딩 실패. 서버에서 /web/을 루트로 열면 data/가 접근되지 않습니다. (루트에서 제공하거나 web/data에 인덱스를 생성하세요)';
      console.error('데이터 로딩 실패', lastErr);
      return;
    }

    // Populate filter options
    const cities = uniqSorted(DATA.map(r => r.city));
    const cats = uniqSorted(DATA.map(r => r.category));
    fillOptions($fCity, cities);
    fillOptions($fCategory, cats);

    applyFilters();
  }

  // Events
  [$fIsPopup, $fStatus, $fSearch, $fSort].forEach(el => el.addEventListener('input', applyFilters));
  $fCity.addEventListener('change', applyFilters);
  $fCategory.addEventListener('change', applyFilters);

  document.addEventListener('DOMContentLoaded', loadData);
})();
