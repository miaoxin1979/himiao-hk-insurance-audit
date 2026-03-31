# scraper/items.py
import scrapy


class InsuranceProductItem(scrapy.Item):
    """爬取到的保险产品原始数据"""
    # 来源
    source_url    = scrapy.Field()
    insurer       = scrapy.Field()   # "AIA" | "Prudential" | "Manulife" | "YFLife"
    scraped_at    = scrapy.Field()

    # 产品基本信息
    product_name  = scrapy.Field()
    product_name_en = scrapy.Field()
    product_type  = scrapy.Field()   # "whole_life" | "term" | "ci"
    currency      = scrapy.Field()

    # 文件链接（PDF 计划书）
    pdf_urls      = scrapy.Field()   # list[str]
    brochure_url  = scrapy.Field()

    # 精算数据（从 PDF 提取后填入）
    premium_years     = scrapy.Field()
    irr_20y           = scrapy.Field()
    breakeven_year    = scrapy.Field()
    loan_ltv          = scrapy.Field()
    dividend_fulfillment = scrapy.Field()

    # 原始 HTML 片段（备用）
    raw_html      = scrapy.Field()


class NewsArticleItem(scrapy.Item):
    """爬取到的保险资讯文章"""
    source_url    = scrapy.Field()
    source_name   = scrapy.Field()   # "HKIA" | "MPF" | "HKMA" | etc.
    scraped_at    = scrapy.Field()

    title_zh      = scrapy.Field()
    title_tw      = scrapy.Field()
    title_en      = scrapy.Field()
    excerpt       = scrapy.Field()
    content_zh    = scrapy.Field()
    content_tw    = scrapy.Field()
    content_en    = scrapy.Field()
    cover_url     = scrapy.Field()
    category      = scrapy.Field()
    published_at  = scrapy.Field()
    tags          = scrapy.Field()   # list[str]


class PDFDocumentItem(scrapy.Item):
    """待 OCR 处理的 PDF 文件"""
    pdf_url       = scrapy.Field()
    insurer       = scrapy.Field()
    product_name  = scrapy.Field()
    local_path    = scrapy.Field()   # 下载到 NAS 后的本地路径
    scraped_at    = scrapy.Field()
