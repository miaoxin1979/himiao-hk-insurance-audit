
/**
 * api-client.js — HiMiao 前端统一 API 客户端 v2.3
 *
 * 核心改进：
 *  1. API_BASE 改为相对路径，自动匹配当前域名+端口，开发/生产通用
 *     如需指向独立后端：const API_BASE = 'http://YOUR_NAS_IP:8888/api/v1';
 *  2. Token key 全站统一为 hm_token（兼容读取旧 key himiao_token）
 *  3. adminFetch 统一提取 FastAPI detail 错误信息，方便前端提示
 *  4. 新增 getArticle(slug) 单篇文章接口
 *  5. getArticles 增加 !res.ok 抛错，方便上层 catch
 *  6. [v2.3] 恢复 401 自动触发登出
 *  7. [v2.4] getMe() 当前用户角色（用于后台权限 UI）
 */

const API_BASE = '/api/v1';

const HiMiaoAPI = {

  /* ── Articles ────────────────────────────────────────────── */
  async getArticles(params = {}) {
    const qs = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/articles${qs ? '?' + qs : ''}`);
    if (!res.ok) throw new Error(`文章列表加载失败 (HTTP ${res.status})`);
    return res.json();
  },

  async getArticle(slug) {
    const res = await fetch(`${API_BASE}/articles/${encodeURIComponent(slug)}`);
    if (!res.ok) throw new Error(`文章不存在: ${slug}`);
    return res.json();
  },

  /** 后台富文本插图：multipart，勿手动设 Content-Type */
  async uploadImage(file) {
    const token = this.getToken();
    if (!token) throw new Error('未登录');
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(`${API_BASE}/upload/image`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data.detail ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)) : `上传失败 (${res.status})`;
      throw new Error(msg);
    }
    return data;
  },

  /* ── Products ────────────────────────────────────────────── */
  async getProducts(params = {}) {
    const qs = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/products${qs ? '?' + qs : ''}`);
    if (!res.ok) throw new Error(`产品列表加载失败 (HTTP ${res.status})`);
    return res.json();
  },

  async getProduct(slug, lang) {
    const qs = lang ? `?lang=${encodeURIComponent(lang)}` : '';
    const res = await fetch(`${API_BASE}/products/${slug}${qs}`);
    if (!res.ok) throw new Error(`产品不存在: ${slug}`);
    return res.json();
  },

  /* ── Subscribers ─────────────────────────────────────────── */
  async subscribe(email, source = 'website') {
    const res = await fetch(`${API_BASE}/subscribers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, source }),
    });
    if (!res.ok) throw new Error('订阅失败，请稍后重试');
    return res.json();
  },

  /* ── Brokers ─────────────────────────────────────────────── */
  async getBrokers(params = {}) {
    const qs = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/brokers${qs ? '?' + qs : ''}`);
    if (!res.ok) throw new Error(`经纪人列表加载失败 (HTTP ${res.status})`);
    return res.json();
  },

  /* ── Ads ─────────────────────────────────────────────────── */
  async getActiveAds() {
    const res = await fetch(`${API_BASE}/ads`);
    if (!res.ok) return [];
    return res.json();
  },

  /* ── Auth ────────────────────────────────────────────────── */
  async login(username, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      let msg = res.status === 403 ? '该账号无权登录后台' : '用户名或密码错误';
      try {
        const d = await res.json();
        if (d.detail && typeof d.detail === 'string') msg = d.detail;
      } catch (_) { /* ignore */ }
      throw new Error(msg);
    }
    const { access_token } = await res.json();
    localStorage.setItem('hm_token', access_token);
    return access_token;
  },

  getToken() {
    // 统一读 hm_token，兼容旧 key himiao_token
    return localStorage.getItem('hm_token')
      || localStorage.getItem('himiao_token')
      || null;
  },

  logout() {
    localStorage.removeItem('hm_token');
    localStorage.removeItem('himiao_token');
    window.location.href = 'admin.html';
  },

  /** 当前登录用户信息（需 JWT，含 role: admin|editor|viewer） */
  async getMe() {
    return this.adminFetch('/auth/me');
  },

  /* ── Admin 安全鉴权请求（404/500 静默，不触发 logout）──── */
  async adminFetchSafe(path, options = {}) {
    try {
      return await this.adminFetch(path, options);
    } catch (e) {
      // 401 照常传播（触发 logout）；其余（404/500/网络）静默返回 null
      if (String(e.message).includes('401')) throw e;
      return null;
    }
  },

  /* ── Admin 鉴权请求 ──────────────────────────────────────── */
  async adminFetch(path, options = {}) {
    const token = this.getToken();
    if (!token) {
      if (window._appReady) this.logout();
      return null;
    }

    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...(options.headers || {}),
      },
    });

    if (res.status === 401) {
      if (window._appReady) {
        console.warn("API 401 Unauthorized, logging out.");
        this.logout();
      }
      throw new Error("认证过期或权限不足 (401)");
    }

    // 204 No Content
    if (res.status === 204) return null;

    const text = await res.text();
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      if (!res.ok) {
        const snippet = text ? String(text).replace(/<[^>]+>/g, ' ').trim().slice(0, 180) : '';
        throw new Error(
          snippet || `请求失败 (HTTP ${res.status})`
        );
      }
      throw new Error(`响应解析失败 (HTTP ${res.status})，请检查网关/后端是否返回了 HTML`);
    }

    if (!res.ok) {
      // 提取 FastAPI 的 detail 字段作为错误信息
      const msg = data?.detail
        ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail))
        : `请求失败 (HTTP ${res.status})`;
      throw new Error(msg);
    }

    return data;
  },
};

window.HiMiaoAPI = HiMiaoAPI;
window.API_BASE = API_BASE;
