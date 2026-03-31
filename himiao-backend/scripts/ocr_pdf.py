#!/usr/bin/env python3
"""
scripts/ocr_pdf.py
手动触发单个 PDF 的 OCR 提取，并将结果写入数据库

用法：
  # 从本地文件提取
  python scripts/ocr_pdf.py --pdf /data/scraper_pdfs/AIA_WP3.pdf --slug aia_wp3

  # 从 URL 下载并提取
  python scripts/ocr_pdf.py --url https://example.com/plan.pdf --slug aia_wp3 --insurer AIA

  # 只打印结果，不写入数据库
  python scripts/ocr_pdf.py --pdf /path/to.pdf --dry-run
"""
import sys
import argparse
import json
import logging
from pathlib import Path

# 把项目根加入 path
ROOT = str(Path(__file__).parent.parent)
sys.path.insert(0, ROOT)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="HiMiao PDF OCR 提取工具")
    parser.add_argument("--pdf",     help="本地 PDF 文件路径")
    parser.add_argument("--url",     help="PDF 下载 URL")
    parser.add_argument("--slug",    required=True, help="产品 slug（数据库主键）")
    parser.add_argument("--insurer", default="", help="保司名称")
    parser.add_argument("--dry-run", action="store_true", help="只打印结果，不写入数据库")
    parser.add_argument("--env",     default=".env")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv(args.env)

    # 确定 PDF 路径
    pdf_path = args.pdf
    if not pdf_path and args.url:
        import requests
        log.info(f"Downloading: {args.url}")
        resp = requests.get(args.url, timeout=30)
        resp.raise_for_status()
        pdf_path = f"/tmp/himiao_ocr_{args.slug}.pdf"
        with open(pdf_path, "wb") as f:
            f.write(resp.content)
        log.info(f"Downloaded to: {pdf_path}")

    if not pdf_path:
        log.error("需要 --pdf 或 --url 参数")
        sys.exit(1)

    # OCR 提取
    from scraper.ocr.pdf_extractor import PDFExtractor
    extractor = PDFExtractor()
    result = extractor.extract(pdf_path)

    log.info(f"\n{'='*50}")
    log.info(f"提取结果 (置信度: {result.confidence:.0%})")
    log.info(f"{'='*50}")
    print(extractor.to_json(result))

    if args.dry_run:
        log.info("Dry run 模式，不写入数据库")
        return

    if result.confidence < 0.3:
        log.warning(f"置信度过低 ({result.confidence:.0%})，建议人工核查后再写入数据库")
        ans = input("是否仍然写入？[y/N] ").strip().lower()
        if ans != "y":
            return

    # 写入数据库
    from app.db.session import SessionLocal
    from app.models.product import Product

    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.slug == args.slug).first()
        if not p:
            log.error(f"产品不存在: {args.slug}，请先在后台创建产品记录")
            return

        # 只更新 OCR 提取到的字段，不覆盖已有数据
        updated = []
        if result.irr_20y and not p.irr_20y:
            p.irr_20y = result.irr_20y; updated.append(f"irr_20y={result.irr_20y}")
        if result.breakeven_year and not p.breakeven_year:
            p.breakeven_year = result.breakeven_year; updated.append(f"breakeven={result.breakeven_year}")
        if result.premium_years and not p.premium_years:
            p.premium_years = result.premium_years; updated.append(f"premium_years={result.premium_years}")
        if result.dividend_fulfillment and not p.dividend_fulfillment_5y:
            p.dividend_fulfillment_5y = result.dividend_fulfillment; updated.append(f"dividend={result.dividend_fulfillment}")
        if result.currency and not p.currency:
            p.currency = result.currency; updated.append(f"currency={result.currency}")

        if updated:
            db.commit()
            log.info(f"✅ 已更新产品 {args.slug}: {', '.join(updated)}")
        else:
            log.info("无新字段需要更新（已有数据优先）")

    finally:
        db.close()


if __name__ == "__main__":
    main()
