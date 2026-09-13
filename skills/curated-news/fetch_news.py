#!/usr/bin/env python3
"""
fetch_news.py — Coletor ultraleve e concorrente de feeds RSS para o Hermes.
Zero dependências externas (usa urllib e xml.etree nativos do Python).
"""

import sys
import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

FEEDS_FILE = os.path.join(os.path.dirname(__file__), "feeds.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_feed(source_name, url, max_items=4):
    items = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=7) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)

            # RSS 2.0 (<channel><item>)
            channel = root.find("channel")
            if channel is not None:
                for item in channel.findall("item")[:max_items]:
                    title = item.findtext("title", "").strip()
                    link = item.findtext("link", "").strip()
                    pub_date = item.findtext("pubDate", "").strip()
                    if title:
                        items.append({
                            "source": source_name,
                            "title": title,
                            "link": link,
                            "date": pub_date
                        })
                return items

            # Atom (<entry>)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns)[:max_items]:
                title = entry.findtext("atom:title", "", ns).strip()
                link_el = entry.find("atom:link", ns)
                link = link_el.attrib.get("href", "") if link_el is not None else ""
                pub_date = entry.findtext("atom:updated", "", ns).strip()
                if title:
                    items.append({
                        "source": source_name,
                        "title": title,
                        "link": link,
                        "date": pub_date
                    })
    except Exception as e:
        # Falha silenciosa individual para não quebrar os outros feeds
        pass
    return items

def get_news(category=None, max_per_source=3):
    if not os.path.exists(FEEDS_FILE):
        print(f"Erro: Arquivo {FEEDS_FILE} não encontrado.", file=sys.stderr)
        return []

    with open(FEEDS_FILE, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    sources_to_query = []
    if category and category in catalog:
        sources_to_query = catalog[category]
    elif category == "all" or not category:
        for cat_sources in catalog.values():
            sources_to_query.extend(cat_sources)
    else:
        # Busca por aproximação
        for cat, sources in catalog.items():
            if category.lower() in cat.lower():
                sources_to_query.extend(sources)

    if not sources_to_query:
        print(f"Nenhuma fonte encontrada para categoria: {category}")
        return []

    all_articles = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(fetch_feed, s["name"], s["url"], max_per_source): s["name"]
            for s in sources_to_query
        }
        for future in as_completed(futures):
            try:
                res = future.result()
                if res:
                    all_articles.extend(res)
            except Exception:
                pass

    return all_articles

def add_feed(category, name, url):
    if not os.path.exists(FEEDS_FILE):
        catalog = {}
    else:
        with open(FEEDS_FILE, "r", encoding="utf-8") as f:
            catalog = json.load(f)

    if category not in catalog:
        catalog[category] = []

    # Evita duplicatas
    for entry in catalog[category]:
        if entry["url"] == url:
            return f"Feed '{name}' já existe na categoria '{category}'."

    catalog[category].append({"name": name, "url": url})
    with open(FEEDS_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    return f"Fonte '{name}' adicionada com sucesso à categoria '{category}'."

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--url" and len(sys.argv) > 2:
        # Busca em uma URL avulsa passada dinamicamente
        custom_url = sys.argv[2]
        results = fetch_feed("Fonte Externa", custom_url, max_items=5)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "--add" and len(sys.argv) >= 5:
        # Adiciona nova fonte: --add <categoria> <nome> <url>
        cat = sys.argv[2]
        name = sys.argv[3]
        url = sys.argv[4]
        msg = add_feed(cat, name, url)
        print(json.dumps({"success": True, "message": msg}, ensure_ascii=False, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "--list":
        with open(FEEDS_FILE, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        cat = sys.argv[1] if len(sys.argv) > 1 else "all"
        results = get_news(cat)
        print(json.dumps(results, ensure_ascii=False, indent=2))

