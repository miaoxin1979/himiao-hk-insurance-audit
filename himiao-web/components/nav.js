/**
 * HiMiao · Shared Component Injector v2.0
 * Injects Nav + Ticker + Footer + AI Capsule into every page.
 * Language switching persists via localStorage across all pages.
 */

/* NAV_I18N removed — translations in components/lang.js */


const TICKER_I18N = {
  cn: [
    { text:'⚖ HiMiao Audit · 独立精算 · 不销售 · 不带货', color:'rgba(255,255,255,0.45)' },
    { text:'📊 已审计产品 147 款 · 覆盖 12 家保司', color:'#00a9e0' },
    { text:'🔒 数据来源：保司官方计划书 + HKIA 公开披露', color:'rgba(255,255,255,0.45)' },
    { text:'✅ 保诚 5年分红实现率 103% · 行业前10%', color:'rgba(255,255,255,0.45)' },
    { text:'🆕 新品：万通富饶传承 2024 · 回本期 4 年', color:'#f59e0b' },
    { text:'📮 your_email@example.com', color:'rgba(255,255,255,0.3)' },
  ],
  hk: [
    { text:'⚖ HiMiao Audit · 獨立精算 · 不銷售 · 不帶貨', color:'rgba(255,255,255,0.45)' },
    { text:'📊 已審計產品 147 款 · 覆蓋 12 家保司', color:'#00a9e0' },
    { text:'🔒 數據來源：保司官方計劃書 + HKIA 公開披露', color:'rgba(255,255,255,0.45)' },
    { text:'✅ 保誠 5年分紅實現率 103% · 行業前10%', color:'rgba(255,255,255,0.45)' },
    { text:'🆕 新品：萬通富饒傳承 2024 · 回本期 4 年', color:'#f59e0b' },
    { text:'📮 your_email@example.com', color:'rgba(255,255,255,0.3)' },
  ],
  en: [
    { text:'⚖ HiMiao Audit · Independent · No Sales · No Commissions', color:'rgba(255,255,255,0.45)' },
    { text:'📊 147 Products Audited · Across 12 Insurers', color:'#00a9e0' },
    { text:'🔒 Data Source: Official Insurer PDFs + HKIA Disclosures', color:'rgba(255,255,255,0.45)' },
    { text:'✅ Prudential 5-yr Dividend Fulfillment 103% · Top 10% Industry', color:'rgba(255,255,255,0.45)' },
    { text:'🆕 New: YF Life Rich Legacy 2024 · Breakeven Year 4', color:'#f59e0b' },
    { text:'📮 your_email@example.com', color:'rgba(255,255,255,0.3)' },
  ],
};

function buildTickerHTML(lang) {
  const items = TICKER_I18N[lang] || TICKER_I18N.cn;
  const doubled = [...items, ...items];
  return doubled.map(i =>
    `<span style="padding:0 28px;color:${i.color};font-size:11px;font-weight:600;letter-spacing:0.03em;white-space:nowrap;">${i.text}</span><span style="color:rgba(255,255,255,0.1);">·</span>`
  ).join('');
}

/* ────── HTML BUILDERS ────── */

function buildNavHTML(lang) {
  const ticker = buildTickerHTML(lang || getLang());

  return `<div id="himiao-nav-root">
<style>
@keyframes hm-ticker{from{transform:translateX(0)}to{transform:translateX(-50%)}}
#hm-ticker-track{animation:hm-ticker 44s linear infinite;}
#hm-ticker-track:hover{animation-play-state:paused;}
#hm-main-nav.scrolled{box-shadow:0 2px 20px rgba(0,0,0,0.09)!important;}
.hnav-a{font-size:13.5px;font-weight:700;color:#5e5e5e;text-decoration:none;letter-spacing:0.06em;transition:color .2s;}
.hnav-a:hover,.hnav-a.active{color:#00a9e0!important;}
#hm-lang-menu{display:none;position:absolute;top:calc(100% + 4px);right:0;background:#fff;border:1px solid #ede8de;box-shadow:0 8px 24px rgba(0,0,0,0.1);border-radius:10px;padding:6px;min-width:140px;z-index:500;}
.hlang-row{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:6px;cursor:pointer;transition:background .15s;}
.hlang-row:hover{background:#f5f1e8;}
#hm-mob-menu a{padding:11px 0;font-size:15px;font-weight:700;color:#1c1c1e;text-decoration:none;border-bottom:1px solid #f5f1e8;display:block;}
@media(min-width:1024px){#hm-nav-links{display:flex!important;}#hm-mob-btn{display:none!important;}}
</style>
<nav id="hm-main-nav" style="background:rgba(253,251,247,0.96);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-bottom:1px solid #ede8de;position:sticky;top:0;z-index:300;transition:box-shadow .2s;">
  <div style="max-width:1280px;margin:0 auto;padding:0 20px;height:64px;display:flex;align-items:center;justify-content:space-between;gap:16px;">
    <a href="index.html" style="display:flex;align-items:center;gap:8px;text-decoration:none;flex-shrink:0;">
      <img src="assets/images/logo.png" alt="HiMiao" style="height:38px;object-fit:contain;" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
      <div style="display:none;align-items:center;gap:7px;">
        <div style="width:32px;height:32px;background:#00a9e0;border-radius:7px;display:flex;align-items:center;justify-content:center;">
          <svg width="15" height="15" viewBox="0 0 16 16" fill="none"><path d="M3 12V7l5-4 5 4v5" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><rect x="5.5" y="8.5" width="2" height="3.5" rx="0.5" fill="#fff"/><rect x="8.5" y="7" width="2" height="5" rx="0.5" fill="rgba(255,255,255,0.6)"/></svg>
        </div>
        <div>
          <div style="font-size:15px;font-weight:900;color:#00a9e0;letter-spacing:-0.4px;line-height:1;">HiMiao</div>
          <div style="font-size:7px;font-weight:800;letter-spacing:0.16em;color:#8e8e93;text-transform:uppercase;">AUDIT</div>
        </div>
      </div>
    </a>
    <div id="hm-nav-links" style="display:none;align-items:center;gap:32px;">
      <a href="index.html"        class="hnav-a" data-page="home"     data-i18n="nav_home">首页</a>
      <a href="product-list.html" class="hnav-a" data-page="products" data-i18n="nav_products">产品审计库</a>
      <a href="academy.html"      class="hnav-a" data-page="academy"  data-i18n="nav_academy">HiMiao讲堂</a>
      <a href="about.html"        class="hnav-a" data-page="about"    data-i18n="nav_about">关于</a>
    </div>
    <div style="display:flex;align-items:center;gap:12px;flex-shrink:0;">
      <div style="position:relative;" id="hm-lang-sw">
        <div onclick="window._hm.toggleLang()" style="display:flex;align-items:center;gap:5px;cursor:pointer;padding:6px 2px;user-select:none;">
          <img id="hm-flag" src="https://flagcdn.com/w40/cn.png" style="width:17px;height:17px;border-radius:50%;object-fit:cover;border:1px solid #e5e5e5;">
          <span id="hm-lang-lbl" style="font-size:10px;font-weight:800;letter-spacing:0.1em;color:#5e5e5e;text-transform:uppercase;">CN</span>
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#8e8e93" stroke-width="2.5"><path d="M19 9l-7 7-7-7"/></svg>
        </div>
        <div id="hm-lang-menu">
          <div class="hlang-row" onclick="switchLang('cn')"><img src="https://flagcdn.com/w40/cn.png" style="width:16px;height:16px;border-radius:50%;"><span style="font-size:12px;font-weight:600;color:#48484a;">简体中文</span></div>
          <div class="hlang-row" onclick="switchLang('hk')"><img src="https://flagcdn.com/w40/hk.png" style="width:16px;height:16px;border-radius:50%;"><span style="font-size:12px;font-weight:600;color:#48484a;">繁體中文</span></div>
          <div class="hlang-row" onclick="switchLang('en')"><img src="https://flagcdn.com/w40/us.png" style="width:16px;height:16px;border-radius:50%;"><span style="font-size:12px;font-weight:600;color:#48484a;">English</span></div>
        </div>
      </div>
      <a href="#" style="font-size:9px;font-weight:800;background:#00a9e0;color:white;padding:7px 14px;border-radius:5px;letter-spacing:0.12em;text-decoration:none;" onmouseover="this.style.background='#0092c9'" onmouseout="this.style.background='#00a9e0'">PRO</a>
      <button id="hm-mob-btn" onclick="window._hm.toggleMob()" style="display:flex;flex-direction:column;gap:4px;background:none;border:none;cursor:pointer;padding:4px;">
        <span style="width:20px;height:2px;background:#4a4a4a;border-radius:1px;display:block;"></span>
        <span style="width:14px;height:2px;background:#4a4a4a;border-radius:1px;display:block;"></span>
        <span style="width:20px;height:2px;background:#4a4a4a;border-radius:1px;display:block;"></span>
      </button>
    </div>
  </div>
  <div id="hm-mob-menu" style="display:none;border-top:1px solid #ede8de;background:rgba(253,251,247,0.98);padding:12px 20px 16px;">
    <a href="index.html"        data-i18n="nav_home">首页</a>
    <a href="product-list.html" data-i18n="nav_products">产品审计库</a>
    <a href="academy.html"      data-i18n="nav_academy">HiMiao讲堂</a>
    <a href="about.html"        data-i18n="nav_about">关于 HiMiao</a>
  </div>
</nav>
<div style="background:#0f1d2e;overflow:hidden;height:32px;display:flex;align-items:center;border-bottom:1px solid rgba(255,255,255,0.04);">
  <div id="hm-ticker-track" style="display:flex;align-items:center;white-space:nowrap;">${ticker}</div>
</div>
</div>`;
}

function buildFooterHTML() {
  return `<footer id="himiao-footer" style="background:#2e2e2e;color:white;padding:48px 20px 28px;margin-top:auto;">
  <div style="max-width:1280px;margin:0 auto;">
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:32px;margin-bottom:36px;">
      <div>
        <div style="font-size:15px;font-weight:900;color:#00a9e0;margin-bottom:10px;">HiMiao Audit</div>
        <p style="font-size:12px;color:rgba(255,255,255,0.35);line-height:1.75;max-width:260px;" data-i18n="footer_about_desc">HiMiao 致力于提供中立、客观的保险产品审计服务。</p>
      </div>
      <div>
        <div style="font-size:10px;font-weight:800;letter-spacing:0.1em;color:rgba(255,255,255,0.2);text-transform:uppercase;margin-bottom:12px;" data-i18n="footer_nav_title">导航</div>
        <div style="display:flex;flex-direction:column;gap:9px;">
          <a href="index.html"        data-i18n="nav_home"     style="font-size:12px;color:rgba(255,255,255,0.45);text-decoration:none;" onmouseover="this.style.color='white'" onmouseout="this.style.color='rgba(255,255,255,0.45)'">首页</a>
          <a href="product-list.html" data-i18n="nav_products" style="font-size:12px;color:rgba(255,255,255,0.45);text-decoration:none;" onmouseover="this.style.color='white'" onmouseout="this.style.color='rgba(255,255,255,0.45)'">产品审计库</a>
          <a href="academy.html"      data-i18n="nav_academy"  style="font-size:12px;color:rgba(255,255,255,0.45);text-decoration:none;" onmouseover="this.style.color='white'" onmouseout="this.style.color='rgba(255,255,255,0.45)'">HiMiao讲堂</a>
          <a href="about.html"        data-i18n="nav_about"    style="font-size:12px;color:rgba(255,255,255,0.45);text-decoration:none;" onmouseover="this.style.color='white'" onmouseout="this.style.color='rgba(255,255,255,0.45)'">关于</a>
        </div>
      </div>
      <div>
        <div style="font-size:10px;font-weight:800;letter-spacing:0.1em;color:rgba(255,255,255,0.2);text-transform:uppercase;margin-bottom:12px;" data-i18n="footer_contact_title">联系</div>
        <div style="display:flex;flex-direction:column;gap:9px;">
          <a href="mailto:your_email@example.com" style="font-size:12px;color:rgba(255,255,255,0.45);text-decoration:none;font-family:monospace;" onmouseover="this.style.color='#00a9e0'" onmouseout="this.style.color='rgba(255,255,255,0.45)'">your_email@example.com</a>
          <a href="about.html#privacy" data-i18n="footer_privacy" style="font-size:12px;color:rgba(255,255,255,0.45);text-decoration:none;" onmouseover="this.style.color='white'" onmouseout="this.style.color='rgba(255,255,255,0.45)'">隐私条款</a>
          <a href="about.html#contact" data-i18n="footer_contact" style="font-size:12px;color:rgba(255,255,255,0.45);text-decoration:none;" onmouseover="this.style.color='white'" onmouseout="this.style.color='rgba(255,255,255,0.45)'">联系我们</a>
        </div>
      </div>
    </div>
    <div style="border-top:1px solid rgba(255,255,255,0.08);padding-top:18px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
      <p style="font-size:11px;color:rgba(255,255,255,0.18);font-weight:700;letter-spacing:0.08em;text-transform:uppercase;" data-i18n="footer_copyright">© 2026 HiMiao. 全球视野，精算未来。</p>
      <p style="font-size:11px;color:rgba(255,255,255,0.15);" data-i18n="footer_disclaimer">本资料不构成任何产品招揽或销售要约。</p>
    </div>
  </div>
</footer>`;
}

function buildCapsuleHTML() {
  return `<div id="hm-capsule">
<style>
@keyframes hm-pr{0%{transform:scale(1);opacity:.7}100%{transform:scale(2.4);opacity:0}}
@keyframes hm-su{from{opacity:0;transform:translateY(14px) scale(.97)}to{opacity:1;transform:translateY(0) scale(1)}}
</style>
<div id="hm-chat" style="display:none;position:fixed;bottom:88px;right:20px;width:340px;max-width:calc(100vw - 40px);background:white;border-radius:16px;box-shadow:0 8px 48px rgba(0,0,0,0.18);border:1px solid #f0f0f0;overflow:hidden;z-index:490;flex-direction:column;animation:hm-su .25s ease both;">
  <div style="background:#1c1c1e;padding:14px 16px;display:flex;justify-content:space-between;align-items:center;">
    <div style="display:flex;align-items:center;gap:8px;">
      <span style="width:7px;height:7px;border-radius:50%;background:#00e5a0;display:inline-block;position:relative;flex-shrink:0;">
        <span style="position:absolute;inset:-3px;border-radius:50%;background:rgba(0,229,160,0.28);animation:hm-pr 1.8s ease-out infinite;"></span>
      </span>
      <span style="color:white;font-size:11px;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;">HiMiao AI</span>
      <span style="font-size:10px;color:rgba(255,255,255,0.28);font-weight:600;">Audit Core</span>
    </div>
    <button onclick="window._hm.toggleChat()" style="background:none;border:none;cursor:pointer;color:rgba(255,255,255,0.4);font-size:18px;line-height:1;padding:0 2px;transition:color .15s;" onmouseover="this.style.color='white'" onmouseout="this.style.color='rgba(255,255,255,0.4)'">✕</button>
  </div>
  <div id="hm-msgs" style="height:240px;overflow-y:auto;padding:14px;background:#f9f9f7;display:flex;flex-direction:column;gap:10px;">
    <div style="display:flex;gap:8px;align-items:flex-start;">
      <div style="width:24px;height:24px;border-radius:50%;background:#1c1c1e;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:9px;font-weight:900;color:white;">AI</div>
      <div data-i18n="ai_greeting" style="background:white;padding:10px 12px;border-radius:12px;border:1px solid #efefef;font-size:12px;color:#48484a;line-height:1.65;max-width:260px;">精算系统就绪。请上传保单 PDF，或输入产品代码（如 AIA-Wealth），我将为您测算真实 IRR。</div>
    </div>
  </div>
  <div style="padding:10px 12px;background:white;border-top:1px solid #f0f0f0;display:flex;gap:8px;align-items:center;">
    <input id="hm-inp" type="text" placeholder="输入指令，例如：帮我分析 AIA 20年 IRR…" data-i18n-placeholder="ai_placeholder" style="flex:1;background:#f5f5f3;border:none;border-radius:8px;padding:8px 12px;font-size:12px;color:#1c1c1e;outline:none;font-family:inherit;" onkeydown="if(event.key==='Enter')window._hm.send()">
    <button onclick="window._hm.send()" style="width:32px;height:32px;border-radius:8px;background:#1c1c1e;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:background .15s;" onmouseover="this.style.background='#00a9e0'" onmouseout="this.style.background='#1c1c1e'">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
    </button>
  </div>
</div>
<button id="hm-fab" onclick="window._hm.toggleChat()" style="position:fixed;bottom:24px;right:20px;z-index:491;display:flex;align-items:center;gap:8px;padding:11px 20px;border-radius:50px;background:#1c1c1e;color:white;font-size:12px;font-weight:800;letter-spacing:0.06em;cursor:pointer;border:none;box-shadow:0 4px 20px rgba(0,0,0,0.22);transition:transform .2s,background .15s;font-family:inherit;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
  <span style="width:8px;height:8px;border-radius:50%;background:#00e5a0;position:relative;flex-shrink:0;">
    <span style="position:absolute;inset:-3px;border-radius:50%;background:rgba(0,229,160,0.28);animation:hm-pr 1.8s ease-out infinite;"></span>
  </span>
  HiMiao AI
</button>
</div>`;
}

/* ────── INJECTION ────── */
function injectAll() {
  const nav = document.getElementById('himiao-nav');
  if (nav) nav.innerHTML = buildNavHTML();

  document.querySelectorAll('footer-placeholder').forEach(el => {
    const div = document.createElement('div');
    div.innerHTML = buildFooterHTML();
    el.replaceWith(div.firstElementChild);
  });

  document.querySelectorAll('ai-capsule-placeholder').forEach(el => {
    const div = document.createElement('div');
    div.innerHTML = buildCapsuleHTML();
    el.replaceWith(div.firstElementChild);
  });

  initNav();
  applyLang(getLang(), false);
  markActive();
}

function initNav() {
  window.addEventListener('scroll', () => {
    const n = document.getElementById('hm-main-nav');
    if (n) n.classList.toggle('scrolled', window.scrollY > 8);
  }, { passive: true });
  document.addEventListener('click', e => {
    const sw = document.getElementById('hm-lang-sw');
    const m = document.getElementById('hm-lang-menu');
    if (sw && m && !sw.contains(e.target)) m.style.display = 'none';
  });
}

function markActive() {
  const pg = (window.location.pathname.split('/').pop().replace('.html','')) || 'index';
  const map = { index:'home', 'product-list':'products', academy:'academy', 'academy-article':'academy', about:'about', 'product-detail':'products' };
  // 情报站 news.html 已从主导航隐藏：不高亮任何项
  if (pg === 'news') {
    document.querySelectorAll('.hnav-a').forEach(a => a.classList.remove('active'));
    return;
  }
  const cur = map[pg] || 'home';
  document.querySelectorAll('.hnav-a').forEach(a => {
    a.classList.toggle('active', a.dataset.page === cur);
  });
}

/* ────── LANGUAGE ────── */
const FLAGS = { cn:'https://flagcdn.com/w40/cn.png', hk:'https://flagcdn.com/w40/hk.png', en:'https://flagcdn.com/w40/us.png' };

function getLang() { return (window.HM_I18N ? window.HM_I18N.lang() : null) || localStorage.getItem('himiao-lang') || 'cn'; }

function applyLang(lang, save) {
  /* Nav UI updates */
  const f = document.getElementById('hm-flag'), l = document.getElementById('hm-lang-lbl');
  if (f) f.src = FLAGS[lang];
  if (l) l.textContent = lang.toUpperCase();
  /* Update ticker */
  const ticker = document.getElementById('hm-ticker-track');
  if (ticker) ticker.innerHTML = buildTickerHTML(lang);
  const m = document.getElementById('hm-lang-menu');
  if (m) m.style.display = 'none';
  /* Delegate ALL translation to HM_I18N engine */
  if (window.HM_I18N) {
    window.HM_I18N.set(lang);
  } else {
    /* Fallback: save + fire old event for backward compat */
    if (save) localStorage.setItem('himiao-lang', lang);
    document.dispatchEvent(new CustomEvent('himiao:langchange', { detail: { lang } }));
    document.dispatchEvent(new CustomEvent('hm:langchange', { detail: { lang } }));
  }
}

/* ────── CHAT ────── */
function chatSend() {
  const inp = document.getElementById('hm-inp');
  const msgs = document.getElementById('hm-msgs');
  if (!inp || !msgs || !inp.value.trim()) return;
  const text = inp.value.trim(); inp.value = '';
  const ub = document.createElement('div');
  ub.style.cssText = 'display:flex;justify-content:flex-end;';
  ub.innerHTML = `<div style="background:#1c1c1e;color:white;padding:9px 12px;border-radius:12px;font-size:12px;line-height:1.6;max-width:240px;">${text}</div>`;
  msgs.appendChild(ub);
  msgs.scrollTop = msgs.scrollHeight;
  setTimeout(() => {
    const ab = document.createElement('div');
    ab.style.cssText = 'display:flex;gap:8px;align-items:flex-start;';
    ab.innerHTML = `<div style="width:24px;height:24px;border-radius:50%;background:#1c1c1e;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:9px;font-weight:900;color:white;">AI</div><div style="background:white;padding:10px 12px;border-radius:12px;border:1px solid #efefef;font-size:12px;color:#48484a;line-height:1.65;max-width:260px;">HiMiao AI 完整版精算引擎即将上线，敬请期待。</div>`;
    msgs.appendChild(ab);
    msgs.scrollTop = msgs.scrollHeight;
  }, 700);
}

/* ────── GLOBAL INTERFACE ────── */
window._hm = {
  toggleLang: () => {
    const m = document.getElementById('hm-lang-menu');
    if (m) m.style.display = m.style.display === 'none' ? 'block' : 'none';
  },
  toggleMob: () => {
    const m = document.getElementById('hm-mob-menu');
    if (m) m.style.display = m.style.display === 'none' ? 'block' : 'none';
  },
  toggleChat: () => {
    const w = document.getElementById('hm-chat');
    if (!w) return;
    const open = w.style.display === 'flex';
    w.style.display = open ? 'none' : 'flex';
    if (!open) w.style.flexDirection = 'column';
  },
  send: chatSend
};

// Exposed globals for backward compatibility
window.switchLang    = (lang) => applyLang(lang, true);  /* kept for nav onclick compat */
window.toggleChat    = window._hm.toggleChat;
window.loadComponents = () => Promise.resolve();

/* ────── BOOT ────── */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', injectAll);
} else {
  injectAll();
}
