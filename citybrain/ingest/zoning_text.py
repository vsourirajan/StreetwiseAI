import time
import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup  # type: ignore

from citybrain.config import DATA_DIR
from citybrain.utils.chunking import chunk_text, attach_metadata

BASE_URL = "https://zr.planning.nyc.gov"
SECTIONS = [
    "article-i",
    "article-ii", 
    "article-iii",
    "article-iv",
    "article-v",
    "article-vi",
    "article-vii",
    "article-viii",
    "article-ix",
    "article-x",
    "article-xi",
    "article-xii",
    "article-xiii",
    "article-xiv",
]


def _fetch(url: str) -> str:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def _extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    
    # Find the main content area - look for the actual regulation text
    main_content = None
    
    # Try to find the main content div that contains the actual regulations
    for selector in [
        "main",
        ".main-content", 
        ".content",
        "#content",
        ".regulation-content",
        ".zoning-text"
    ]:
        main_content = soup.select_one(selector)
        if main_content:
            break
    
    if not main_content:
        # Fallback to body if no specific content area found
        main_content = soup.find("body") or soup
    
    # Remove navigation, headers, footers, and other non-content elements
    for selector in [
        "nav", "header", "footer", ".navigation", ".menu", ".toc", 
        ".breadcrumb", ".sidebar", ".advertisement", ".social-share",
        "script", "style", ".print-button", ".copy-link"
    ]:
        for el in main_content.select(selector):
            el.decompose()
    
    # Extract text with better formatting
    text = main_content.get_text(separator="\n", strip=True)
    
    # Clean up excessive whitespace and normalize
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    return text.strip()


def _find_chapter_links(article_html: str, base_url: str) -> List[str]:
    """Extract links to individual chapters from an article page."""
    soup = BeautifulSoup(article_html, "html.parser")
    chapter_links = []
    
    # Look for chapter links - they typically follow patterns like:
    # - /article-i/chapter-1
    # - /article-i/chapter-2
    # - Links containing "chapter" in href or text
    
    # Method 1: Look for href patterns
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "chapter" in href.lower():
            if href.startswith("/"):
                full_url = urljoin(base_url, href)
            elif href.startswith("http"):
                full_url = href
            else:
                full_url = urljoin(base_url, "/" + href)
            chapter_links.append(full_url)
    
    '''# Method 2: Look for text patterns that suggest chapters
    for link in soup.find_all("a"):
        link_text = link.get_text().lower()
        if any(keyword in link_text for keyword in ["chapter", "section", "part"]):
            href = link.get("href")
            if href:
                if href.startswith("/"):
                    full_url = urljoin(base_url, href)
                elif href.startswith("http"):
                    full_url = href
                else:
                    full_url = urljoin(base_url, "/" + href)
                if full_url not in chapter_links:
                    chapter_links.append(full_url)
    
    # Method 3: Look for common chapter URL patterns
    article_slug = base_url.split("/")[-1]
    for i in range(1, 50):  # Reasonable upper limit for chapters
        potential_url = f"{BASE_URL}/{article_slug}/chapter-{i}"
        chapter_links.append(potential_url)'''
    
    return list(set(chapter_links))  # Remove duplicates


def _is_valid_chapter_content(text: str) -> bool:
    """Check if the extracted text contains meaningful regulation content."""
    if not text or len(text.strip()) < 100:
        return False
    
    # Skip pages that are mostly navigation or error messages
    skip_indicators = [
        "page not found", "error", "access denied", "forbidden",
        "this page is under construction", "coming soon"
    ]
    
    text_lower = text.lower()
    if any(indicator in text_lower for indicator in skip_indicators):
        return False
    
    # Check if it contains regulation-like content
    regulation_indicators = [
        "shall", "must", "required", "permitted", "prohibited",
        "minimum", "maximum", "height", "floor area", "zoning",
        "district", "use", "building", "development"
    ]
    
    indicator_count = sum(1 for indicator in regulation_indicators if indicator in text_lower)
    return indicator_count >= 3  # At least 3 regulation indicators


def download_zoning_text(out_dir: Path | None = None) -> Path:
    logger = logging.getLogger(__name__)
    out_dir = out_dir or DATA_DIR / "zoning"
    out_dir.mkdir(parents=True, exist_ok=True)

    all_pages: List[Dict] = []
    all_chapters: List[Dict] = []
    
    logger.info(f"Starting NYC Zoning Resolution text download to {out_dir}")
    logger.info(f"Processing {len(SECTIONS)} articles...")
    
    for i, article_slug in enumerate(SECTIONS, 1):
        logger.info(f"[{i}/{len(SECTIONS)}] Processing {article_slug}...")
        article_url = f"{BASE_URL}/{article_slug}"
        
        try:
            # Fetch the article overview page
            logger.debug(f"  Fetching article overview: {article_url}")
            article_html = _fetch(article_url)
            article_text = _extract_text(article_html)
            
            # Store article overview
            all_pages.append({
                "url": article_url,
                "slug": article_slug,
                "type": "article_overview",
                "text": article_text
            })
            logger.debug(f"  Article overview extracted: {len(article_text)} characters")
            
            # Find and fetch all chapters
            chapter_links = _find_chapter_links(article_html, article_url)
            logger.info(f"  Found {len(chapter_links)} potential chapter links")
            
            valid_chapters = 0
            for j, chapter_url in enumerate(chapter_links, 1):
                try:
                    logger.debug(f"    [{j}/{len(chapter_links)}] Fetching {chapter_url}")
                    chapter_html = _fetch(chapter_url)
                    chapter_text = _extract_text(chapter_html)
                    
                    # Only keep chapters with meaningful content
                    if _is_valid_chapter_content(chapter_text):
                        chapter_slug = chapter_url.split("/")[-1]
                        all_chapters.append({
                            "url": chapter_url,
                            "slug": chapter_slug,
                            "article": article_slug,
                            "type": "chapter",
                            "text": chapter_text
                        })
                        valid_chapters += 1
                        logger.debug(f"      ✓ Valid chapter content ({len(chapter_text)} chars)")
                    else:
                        logger.debug(f"      ✗ Skipped - insufficient content")
                    
                    time.sleep(0.5)  # Be respectful to the server
                    
                except Exception as exc:
                    logger.warning(f"      ✗ Error fetching chapter {chapter_url}: {exc}")
                    continue
            
            logger.info(f"  {article_slug}: {valid_chapters} valid chapters extracted")
            time.sleep(1)  # Pause between articles
            
        except Exception as exc:
            logger.error(f"Error processing {article_slug}: {exc}")
            continue
    
    # Save all data
    logger.info("Saving downloaded data...")
    raw_json = out_dir / "zoning_pages.json"
    raw_json.write_text(json.dumps(all_pages, ensure_ascii=False, indent=2))
    logger.info(f"  Article overviews saved to: {raw_json}")
    
    chapters_json = out_dir / "zoning_chapters.json"
    chapters_json.write_text(json.dumps(all_chapters, ensure_ascii=False, indent=2))
    logger.info(f"  Chapter content saved to: {chapters_json}")
    
    # Combine all text for the full corpus
    all_texts = []
    all_texts.extend([p["text"] for p in all_pages if p.get("text")])
    all_texts.extend([c["text"] for c in all_chapters if c.get("text")])
    
    full_text = "\n\n".join(all_texts)
    full_text_path = out_dir / "zoning_text.txt"
    full_text_path.write_text(full_text)
    logger.info(f"  Combined text saved to: {full_text_path}")
    
    logger.info(f"Download complete: {len(all_pages)} article pages and {len(all_chapters)} chapters")
    logger.info(f"Total text length: {len(full_text):,} characters")
    
    return out_dir


def chunk_and_write_embeddings_corpus(out_dir: Path | None = None) -> Path:
    logger = logging.getLogger(__name__)
    out_dir = out_dir or DATA_DIR / "zoning"
    txt_path = out_dir / "zoning_text.txt"
    
    if not txt_path.exists():
        logger.info("Zoning text not found, downloading first...")
        download_zoning_text(out_dir)
    
    logger.info("Starting text chunking for embeddings...")
    text = txt_path.read_text()
    logger.info(f"Input text length: {len(text):,} characters")
    
    chunks = chunk_text(text, max_tokens=900, overlap_tokens=120)
    logger.info(f"Created {len(chunks)} chunks with ~900 tokens each")
    
    docs = attach_metadata(
        chunks,
        {
            "source": "nyc-zoning-resolution",
            "jurisdiction": "NYC",
            "doc_type": "legal-text",
        },
    )
    
    jsonl_path = out_dir / "zoning_chunks.jsonl"
    with jsonl_path.open("w") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    
    logger.info(f"Chunks saved to: {jsonl_path}")
    logger.info(f"Ready for Pinecone indexing with {len(chunks)} documents")
    
    return jsonl_path