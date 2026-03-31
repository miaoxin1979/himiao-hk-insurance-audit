/* ═══════════════════════════════════════════════════════════════
   HiMiao · i18n 引擎 v2.0 — 铁律架构 · 不可摧毁版
   
   架构铁律：
   ① lang.js 定义字典 (HM_DICT)
   ② i18n-engine.js 提供唯一渲染引擎
   ③ nav.js 触发语言切换
   ④ 所有翻译通过 data-i18n 属性驱动
   
   API：
   - HM_I18N.set('en')      切换语言
   - HM_I18N.lang()         获取当前语言  
   - HM_I18N.t('key')       获取翻译文本
   - HM_I18N.render()       手动触发全页渲染
   - window.switchLang(l)   兼容旧代码
════════════════════════════════════════════════════════════════ */

(function() {
  'use strict';

  var STORAGE_KEY = 'himiao-lang';
  var VALID = ['cn', 'hk', 'en'];

  function getLang() {
    var s = localStorage.getItem(STORAGE_KEY);
    return VALID.indexOf(s) >= 0 ? s : 'cn';
  }

  /* ── 核心渲染：遍历所有 [data-i18n] 元素 ── */
  function renderLanguage(lang) {
    if (VALID.indexOf(lang) < 0) lang = 'cn';

    var dict = (window.HM_DICT && window.HM_DICT[lang]) || {};

    /* [data-i18n] → innerHTML */
    document.querySelectorAll('[data-i18n]').forEach(function(el) {
      var key = el.getAttribute('data-i18n');
      if (dict[key] !== undefined) el.innerHTML = dict[key];
    });

    /* [data-i18n-ph] → placeholder */
    document.querySelectorAll('[data-i18n-ph]').forEach(function(el) {
      var key = el.getAttribute('data-i18n-ph');
      if (dict[key] !== undefined) el.placeholder = dict[key];
    });

    /* [data-i18n-title] → title attribute */
    document.querySelectorAll('[data-i18n-title]').forEach(function(el) {
      var key = el.getAttribute('data-i18n-title');
      if (dict[key] !== undefined) el.title = dict[key];
    });

    /* html lang attribute */
    document.documentElement.lang =
      lang === 'hk' ? 'zh-HK' : lang === 'en' ? 'en' : 'zh-CN';

    /* Store for JS-rendered components */
    window.HM_LANG = lang;

    /* Fire event for JS-rendered components (news cards, product cards, etc.) */
    document.dispatchEvent(
      new CustomEvent('hm:langchange', { detail: { lang: lang, dict: dict } })
    );
    /* Backward compat event */
    document.dispatchEvent(
      new CustomEvent('himiao:langchange', { detail: { lang: lang } })
    );
  }

  /* ── 设置语言 ── */
  function setLang(lang) {
    if (VALID.indexOf(lang) < 0) return;
    localStorage.setItem(STORAGE_KEY, lang);
    renderLanguage(lang);
  }

  /* ── 公开 API ── */
  window.HM_I18N = {
    set:    setLang,
    render: function() { renderLanguage(getLang()); },
    lang:   getLang,
    t: function(key) {
      var lang = getLang();
      var dict = (window.HM_DICT && window.HM_DICT[lang]) || {};
      return dict[key] !== undefined ? dict[key] : key;
    }
  };

  /* ── 全局兼容：window.switchLang ── */
  window.switchLang = setLang;

  /* ── MutationObserver：自动处理动态注入的 data-i18n 元素 ── */
  var _renderTimer = null;
  function scheduleRender() {
    if (_renderTimer) clearTimeout(_renderTimer);
    _renderTimer = setTimeout(function() {
      renderLanguage(getLang());
    }, 0); /* 0ms: 等本轮 DOM 更新完成后渲染 */
  }

  var observer = new MutationObserver(function(mutations) {
    var needRender = false;
    mutations.forEach(function(m) {
      if (m.type === 'childList' && m.addedNodes.length > 0) {
        m.addedNodes.forEach(function(node) {
          if (node.nodeType === 1) { /* Element node */
            if (node.querySelector && node.querySelector('[data-i18n]')) {
              needRender = true;
            }
            if (node.getAttribute && node.getAttribute('data-i18n')) {
              needRender = true;
            }
          }
        });
      }
    });
    if (needRender) scheduleRender();
  });

  /* ── 初始化 ── */
  function init() {
    /* 1. 立即渲染当前语言 */
    renderLanguage(getLang());

    /* 2. 监听 DOM 变化（nav注入、产品卡片渲染等） */
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
