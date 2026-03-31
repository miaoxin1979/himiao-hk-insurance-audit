"""
app/api/v1/endpoints/articles.py — 新闻全自动流 + 人工管理

【核心设计：两套流程靠字段隔离，不造两套系统】

  产品强审核流：
    爬虫/AI 写入 → is_published=False → 管理员后台审核 → PATCH is_published=True → 上线

  新闻全自动直发流：
    爬虫写入时 auto_publish=True → 系统自动设 is_published=True → 直接对外可见
    适合每日资讯类内容，无需人工介入

接口清单：
  GET    /api/v1/articles                → 已发布文章列表（公开）
  GET    /api/v1/articles/admin/all      → 全部文章含草稿（JWT）
  GET    /api/v1/articles/admin/export   → CSV 导出（JWT）
  GET    /api/v1/articles/{slug}         → 单篇（公开）
  POST   /api/v1/articles                → 新建（JWT；auto_publish 控制是否跳审核）
  POST   /api/v1/articles/crawl          → 手动触发新闻抓取（JWT）
  PATCH  /api/v1/articles/{slug}         → 更新/上下线（JWT）
  DELETE /api/v1/articles/{slug}         → 删除（JWT）
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_editor, require_staff
from app.models.article import Article
from app.models.user import User

router = APIRouter(prefix="/articles", tags=["Articles"])


def _normalize_sina_pc_url(url: str) -> Optional[str]:
    """
    新浪手机站 news.sina.cn / zx.sina.cn 的正文多为前端渲染，静态 HTML 里 #article 常为空。
    转为 PC 站 news.sina.com.cn/c/日期/doc-*.shtml 后同篇可抓到完整正文。
    """
    if not url:
        return None
    m = re.search(
        r"https?://(?:news|zx)\.sina\.cn/(\d{4}-\d{2}-\d{2})/detail-([a-z0-9]+)\.d\.html",
        url,
        re.I,
    )
    if m:
        d, docid = m.group(1), m.group(2)
        return f"https://news.sina.com.cn/c/{d}/doc-{docid}.shtml"
    return None


def fetch_article_body_from_url(url: str, max_chars: int = 20000) -> str:
    """
    抓取详情页正文（与 /crawl 内逻辑一致）。
    新浪手机链会先换 PC 链再请求；多 URL 依次尝试。
    """
    import httpx

    if not url:
        return ""

    try_urls: list[str] = []
    pc = _normalize_sina_pc_url(url)
    if pc and pc != url:
        try_urls.append(pc)
    if url not in try_urls:
        try_urls.append(url)

    httpx_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    def _strip_tags(text: str) -> str:
        return re.sub(r"<[^>]+>", "", text or "").strip()

    def _extract_from_html(html: str) -> str:
        text = ""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "noscript", "iframe"]):
                tag.decompose()
            for sel in (
                "#article",
                "#artibody",
                "#article_content",
                ".article-content",
                ".article-body",
                "#js_article",
                "article",
                "main",
            ):
                node = soup.select_one(sel)
                if node:
                    t = node.get_text("\n", strip=True)
                    if len(t) > 80:
                        text = t
                        break
            if not text:
                art = soup.find("article")
                if art:
                    text = art.get_text("\n", strip=True)
            if not text:
                bd = soup.find("body")
                if bd:
                    for noise in bd.find_all(
                        ["nav", "header", "footer", "aside", "form"]
                    ):
                        noise.decompose()
                    text = bd.get_text("\n", strip=True)
            if text:
                text = re.sub(r"\n{3,}", "\n\n", text)
                text = re.sub(r"[ \t]+", " ", text)
                text = text.strip()
        except Exception:
            text = ""

        if not text or len(text) < 80:
            html2 = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", html, flags=re.I)
            html2 = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", html2, flags=re.I)
            block = html2
            for pat in [
                r"<!--\s*正文开始\s*-->([\s\S]*?)<!--\s*正文结束\s*-->",
                r"<article[^>]*>([\s\S]*?)</article>",
                r'<div[^>]*id="article"[^>]*>([\s\S]*?)</div>\s*</div>',
                r'<div[^>]*class="[^"]*article-body[^"]*"[^>]*>([\s\S]*?)</div>',
                r'<div[^>]*id="content"[^>]*>([\s\S]*?)</div>',
                r"<body[^>]*>([\s\S]*?)</body>",
            ]:
                m = re.search(pat, html2, re.I | re.DOTALL)
                if m and len(m.group(1)) > 100:
                    block = m.group(1)
                    break
            text = re.sub(r"<[^>]+>", " ", block)
            text = re.sub(r"\s+", " ", text).strip()
            text = _strip_tags(text)

        return text

    try:
        for fetch_url in try_urls:
            try:
                r = httpx.get(
                    fetch_url,
                    timeout=15,
                    follow_redirects=True,
                    headers=httpx_headers,
                )
            except Exception:
                continue
            if r.status_code != 200 or not r.text:
                continue
            text = _extract_from_html(r.text)
            if text and len(text) >= 80:
                return text[:max_chars]
        return ""
    except Exception:
        return ""


def _extract_source_url_fallback(content: Optional[str]) -> Optional[str]:
    """
    旧数据或未写入 source_url 时，从正文里猜原文链接。
    与 _save 在无正文时写入的「原文链接：https://...」格式一致。
    """
    if not content:
        return None
    text = content.strip()
    m = re.search(
        r"原文链接\s*[：:]\s*(https?://[^\s\u4e00-\u9fff<\"']+)",
        text[:4000],
        re.I,
    )
    if m:
        return m.group(1).rstrip(".,;，。；)）】」")
    first = text.split("\n", 1)[0].strip()
    m2 = re.match(r"(https?://\S+)", first)
    if m2:
        return m2.group(1).rstrip(".,;，。；)）】」")
    return None


# ── Request Schemas ───────────────────────────────────────────────

class ArticleCreate(BaseModel):
    """
    字段名与 Article ORM 保持一致（title_zh / content_zh）。
    前端可传 title / body 别名（与后台 admin 表单一致）。
    """
    model_config = ConfigDict(populate_by_name=True)

    slug: str
    title_zh: str = Field(..., validation_alias=AliasChoices("title_zh", "title"))
    title_tw: Optional[str] = None
    title_en: Optional[str] = None
    excerpt: Optional[str] = None
    content_zh: Optional[str] = Field(None, validation_alias=AliasChoices("content_zh", "body"))
    content_tw: Optional[str] = None
    content_en: Optional[str] = None
    cover_url: Optional[str] = None
    category: Optional[str] = None  # market|alert|policy|audit|guide
    channel: Optional[str] = Field("news", description="news=资讯 | academy=保险知识讲堂")
    content_format: Optional[str] = Field("markdown", description="markdown | html（讲堂富文本用 html）")
    tags: Optional[List[str]] = None
    author: str = "HiMiao 精算团队"
    read_min: int = 5
    is_hot: bool = False
    is_published: bool = False
    auto_publish: bool = False


class ArticlePatch(BaseModel):
    """PATCH 语义：所有字段可选"""
    model_config = ConfigDict(populate_by_name=True)

    title_zh: Optional[str] = Field(None, validation_alias=AliasChoices("title_zh", "title"))
    title_tw: Optional[str] = None
    title_en: Optional[str] = None
    excerpt: Optional[str] = None
    content_zh: Optional[str] = Field(None, validation_alias=AliasChoices("content_zh", "body"))
    content_tw: Optional[str] = None
    content_en: Optional[str] = None
    cover_url: Optional[str] = None
    category: Optional[str] = None
    channel: Optional[str] = None
    content_format: Optional[str] = None
    tags: Optional[List[str]] = None
    author: Optional[str] = None
    read_min: Optional[int] = None
    is_hot: Optional[bool] = None
    is_published: Optional[bool] = None


# ── 公开：已发布文章列表 ──────────────────────────────────────────

@router.get("", summary="已发布文章列表（公开）")
def list_articles(
    category: Optional[str] = Query(None, description="market|alert|policy|audit|guide"),
    channel: Optional[str] = Query(
        None,
        description="news=仅资讯 | academy=仅讲堂；不传=仅资讯（兼容旧数据，不含讲堂）",
    ),
    is_hot: Optional[bool] = Query(None),
    limit: int = Query(20, le=100),
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    q: Optional[str] = Query(None, description="搜索标题或摘要（模糊匹配）"),
    db: Session = Depends(get_db),
):
    """
    返回 `{ total, items, page, limit }`。前端分页、搜索与 `news.html` 对齐。
    """
    qry = db.query(Article).filter(Article.is_published == True)
    if channel:
        qry = qry.filter(Article.channel == channel)
    else:
        qry = qry.filter(
            or_(Article.channel == "news", Article.channel.is_(None), Article.channel == "")
        )
    if category:
        qry = qry.filter(Article.category == category)
    if is_hot is not None:
        qry = qry.filter(Article.is_hot == is_hot)
    if q and q.strip():
        kw = f"%{q.strip()}%"
        qry = qry.filter(
            or_(
                Article.title_zh.ilike(kw),
                Article.excerpt.ilike(kw),
            )
        )
    total = qry.count()
    skip = (page - 1) * limit
    items = (
        qry.order_by(Article.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {"total": total, "items": items, "page": page, "limit": limit}


# ── Admin：全部文章（含草稿）────────────────────────────────────

@router.get("/admin/all", summary="[Admin] 全部文章含草稿")
def admin_list_all(
    category: Optional[str] = Query(None),
    channel: Optional[str] = Query(None, description="news | academy；不传=全部"),
    is_published: Optional[bool] = Query(None),
    limit: int = Query(100, le=500),
    skip: int = Query(0),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    q = db.query(Article)
    if category is not None:
        q = q.filter(Article.category == category)
    if channel is not None:
        if channel == "news":
            q = q.filter(or_(Article.channel == "news", Article.channel.is_(None), Article.channel == ""))
        else:
            q = q.filter(Article.channel == channel)
    if is_published is not None:
        q = q.filter(Article.is_published == is_published)
    total = q.count()
    items = q.order_by(Article.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": items}


# ── Admin：CSV 导出 ───────────────────────────────────────────────

@router.get("/admin/export", summary="[Admin] 导出文章列表 CSV")
def export_articles(
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    articles = db.query(Article).order_by(Article.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "slug", "title_zh", "category", "author",
                     "is_hot", "is_published", "read_min", "created_at"])
    for a in articles:
        writer.writerow([
            a.id, a.slug, a.title_zh, a.category or "", a.author,
            a.is_hot, a.is_published, a.read_min,
            a.created_at.isoformat() if a.created_at else "",
        ])
    output.seek(0)
    filename = f"articles_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Admin：手动触发新闻抓取 ──────────────────────────────────────

@router.post("/crawl", summary="[Admin] 手动触发新闻抓取")
def trigger_crawl(
    limit: int = Query(15, le=30),
    auto_publish: bool = Query(False, description="True=直接发布，False=存草稿待审核"),
    fetch_full: bool = Query(True, description="True=访问详情页抓取正文，False=仅保存摘要"),
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    """
    手动触发新闻抓取。拉取大陆可访问的几个 RSS/JSON 源。
    - auto_publish=False（默认）：存为草稿，管理员审核后手动发布
    - auto_publish=True：直接发布
    - fetch_full=True：访问详情页抓取正文，审核时可看全文
    """
    import httpx

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, application/rss+xml, text/xml, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    saved, skipped, failed = 0, 0, 0
    details: list[dict] = []

    def _clean(text: str) -> str:
        return re.sub(r"<[^>]+>", "", text or "").strip()

    def _slug(source: str, title: str) -> str:
        h = hashlib.md5(title.encode()).hexdigest()[:10]
        prefix = re.sub(r"[^\w]", "", source.lower())[:8]
        return f"{prefix}-{h}"

    def _save(title: str, excerpt: str, content: str,
              source: str, link: str, category: str) -> bool:
        """保存一条文章，返回 True=新建 False=已存在"""
        slug = _slug(source, title)
        if db.query(Article).filter(Article.slug == slug).first():
            return False
        now = datetime.now(timezone.utc)
        body = content if content else f"原文链接：{link}\n\n{excerpt}"
        a = Article(
            slug=slug,
            title_zh=title,
            excerpt=excerpt[:200] if excerpt else title[:200],
            content_zh=body,
            source_url=link or None,
            category=category,
            channel="news",
            content_format="markdown",
            author=source,
            is_published=auto_publish,
            published_at=now if auto_publish else None,
            is_hot=False,
            read_min=3,
            tags=[source, "港险"],
        )
        db.add(a)
        db.commit()
        return True

    # ── 源1：新浪财经保险频道（JSON Roll API）────────────────────
    try:
        r = httpx.get(
            "https://feed.mix.sina.com.cn/api/roll/get"
            "?pageid=153&lid=2510&k=&num=30&page=1",
            timeout=15, follow_redirects=True, headers=headers,
        )
        if r.status_code == 200:
            for item in r.json().get("result", {}).get("data", [])[:limit]:
                title = item.get("title", "").strip()
                link  = item.get("url", "")
                intro = _clean(item.get("intro", ""))
                if not title:
                    continue
                content = fetch_article_body_from_url(link) if fetch_full and link else ""
                if _save(title, intro, content, "新浪财经", link, "market"):
                    saved += 1
                    details.append({"slug": _slug("新浪财经", title),
                                    "title": title, "source": "新浪财经"})
                else:
                    skipped += 1
    except Exception as e:
        failed += 1

    # ── 源2：证券时报（JSON API）─────────────────────────────────
    try:
        r = httpx.get(
            "https://www.stcn.com/article/list.html?type=kx&page_time=1",
            timeout=15, follow_redirects=True,
            headers={**headers, "X-Requested-With": "XMLHttpRequest",
                     "Referer": "https://www.stcn.com/article/list/kx.html"},
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("state") == 1:
                for item in data.get("data", [])[:limit]:
                    title = item.get("title", "").strip()
                    url   = item.get("url", "")
                    if not title:
                        continue
                    # 只保留港险相关
                    hk_kw = ["友邦", "AIA", "保诚", "宏利", "富卫",
                             "香港保险", "港险", "1299", "2378", "945"]
                    if not any(k in title for k in hk_kw):
                        continue
                    full_url = "https://www.stcn.com" + url if url.startswith("/") else url
                    intro = _clean(item.get("content", ""))
                    content = fetch_article_body_from_url(full_url) if fetch_full and full_url else ""
                    if _save(title, intro, content, "证券时报", full_url, "market"):
                        saved += 1
                        details.append({"slug": _slug("证券时报", title),
                                        "title": title, "source": "证券时报"})
                    else:
                        skipped += 1
    except Exception:
        failed += 1

    # ── 源3：HKMA 金管局 RSS ─────────────────────────────────────
    try:
        r = httpx.get(
            "https://www.hkma.gov.hk/eng/rss/press-releases.rss",
            timeout=15, follow_redirects=True, headers=headers,
        )
        if r.status_code == 200:
            entries = re.findall(r"<item>(.*?)</item>", r.text, re.DOTALL)
            for entry in entries[:limit]:
                title_m = re.search(
                    r"<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>",
                    entry, re.DOTALL,
                )
                title = _clean(title_m.group(1)) if title_m else ""
                if not title:
                    continue
                link_m = re.search(r"<link[^>]*>([^<]+)</link>", entry)
                link = link_m.group(1).strip() if link_m else ""
                desc_m = re.search(
                    r"<description[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>",
                    entry, re.DOTALL,
                )
                desc = _clean(desc_m.group(1))[:300] if desc_m else ""
                content = fetch_article_body_from_url(link) if fetch_full and link else ""
                if _save(title, desc, content, "HKMA金管局", link, "policy"):
                    saved += 1
                    details.append({"slug": _slug("HKMA金管局", title),
                                    "title": title, "source": "HKMA金管局"})
                else:
                    skipped += 1
    except Exception:
        failed += 1

    return {
        "ok": True,
        "saved": saved,
        "skipped": skipped,
        "failed_sources": failed,
        "auto_published": auto_publish,
        "details": details,
    }


# ── Admin：按原文链接重新抓取正文（修复手机链/旧数据）────────────────

@router.post(
    "/{slug}/refetch-body",
    summary="[Admin] 根据 source_url 重新抓取正文",
    description="优先用 source_url；若无则从正文首行「原文链接：URL」解析（兼容旧数据）。新浪手机链会自动换 PC 链。",
)
def refetch_article_body(
    slug: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    try:
        a = db.query(Article).filter(Article.slug == slug).first()
        if not a:
            raise HTTPException(404, "文章不存在")
        stored = (a.source_url or "").strip()
        link = stored
        if not link:
            link = (_extract_source_url_fallback(a.content_zh or "") or "").strip()
        if not link:
            raise HTTPException(
                400,
                "该文章没有原文链接：请先在「文章管理」编辑该条，填写「原文链接」字段；"
                "或确保正文首行含「原文链接：https://...」（旧版抓取曾写入此格式）。",
            )
        body = fetch_article_body_from_url(link)
        if not body or len(body) < 80:
            raise HTTPException(
                502,
                "未能抓到足够长的正文，请检查原文页是否可访问，或手动在编辑里粘贴正文",
            )
        a.content_zh = body
        if not stored:
            a.source_url = link
        db.commit()
        db.refresh(a)
        return {"ok": True, "length": len(body), "slug": a.slug}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"重新抓取时发生错误：{e!s}") from e


# ── 公开：单篇文章 ────────────────────────────────────────────────

@router.get("/{slug}", summary="单篇文章（公开）")
def get_article(slug: str, db: Session = Depends(get_db)):
    a = db.query(Article).filter(Article.slug == slug).first()
    if not a:
        raise HTTPException(404, "文章不存在")
    return a


# ── Admin：新建文章 ───────────────────────────────────────────────

@router.post("", status_code=201, summary="新建文章（JWT）")
def create_article(
    body: ArticleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    if db.query(Article).filter(Article.slug == body.slug).first():
        raise HTTPException(400, f"slug 已存在: {body.slug}")

    data = body.model_dump(exclude={"auto_publish"})

    # 自动流：auto_publish=True 直接发布
    if body.auto_publish:
        data["is_published"] = True
        data["published_at"] = datetime.now(timezone.utc)

    a = Article(**data)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


# ── Admin：更新文章 ───────────────────────────────────────────────

@router.patch("/{slug}", summary="更新文章（JWT）")
def patch_article(
    slug: str,
    body: ArticlePatch,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    """
    上线：PATCH {"is_published": true}
    下线：PATCH {"is_published": false}
    标热：PATCH {"is_hot": true}
    """
    a = db.query(Article).filter(Article.slug == slug).first()
    if not a:
        raise HTTPException(404, "文章不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(a, k, v)
    db.commit()
    db.refresh(a)
    return a


# ── Admin：删除文章 ───────────────────────────────────────────────

@router.delete("/{slug}", status_code=204, summary="删除文章（JWT）")
def delete_article(
    slug: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    a = db.query(Article).filter(Article.slug == slug).first()
    if not a:
        raise HTTPException(404, "文章不存在")
    db.delete(a)
    db.commit()
