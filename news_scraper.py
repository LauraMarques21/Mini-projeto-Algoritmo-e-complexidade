# news_scraper.py
"""
Scraper de notícias.
Tenta primeiro o G1 (globo). Se não conseguir, usa um fallback genérico.
Salva em 'manchetes.json' uma lista de objetos: { "titulo":..., "link":..., "resumo":... }
"""

import requests 
from bs4 import BeautifulSoup 
import json
import time
from urllib.parse import urljoin

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
             "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

HEADERS = {"User-Agent": USER_AGENT}

DEFAULT_URL = "https://g1.globo.com/"  # site padrão

def fetch(url, timeout=10):
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp.text

def parse_g1(html, base_url=DEFAULT_URL):
    """
    Tentativa de extrair manchetes do G1. O HTML do site pode mudar;
    aqui fazemos várias tentativas de seletores comuns para sermos robustos.
    """
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # Tentativa 1: blocos principais com classe feed-post-body
    # (seletor comum em várias versões do G1)
    candidates = soup.select("a.feed-post-link, a.feed-post-link[href], .feed-post-body a")
    seen = set()
    for a in candidates:
        href = a.get("href")
        title = a.get_text(strip=True)
        if not href or not title:
            continue
        if href.startswith("/"):
            href = urljoin(base_url, href)
        key = (title, href)
        if key in seen:
            continue
        seen.add(key)
        # Tentar pegar resumo se houver
        parent = a.parent
        resumo = ""
        # procurar um .feed-post-body-resumo ou similar
        resumo_tag = None
        if parent:
            resumo_tag = parent.select_one(".feed-post-body-resumo, .resumo, p")
        if resumo_tag:
            resumo = resumo_tag.get_text(strip=True)
        results.append({"titulo": title, "link": href, "resumo": resumo})
        if len(results) >= 30:
            break

    # Se não encontrou nada, tentar outra abordagem
    if not results:
        # procurar <h3> ou <h2> com <a>
        for header in soup.select("h1 a, h2 a, h3 a"):
            a = header
            href = a.get("href")
            title = a.get_text(strip=True)
            if not href or not title:
                continue
            if href.startswith("/"):
                href = urljoin(base_url, href)
            results.append({"titulo": title, "link": href, "resumo": ""})
            if len(results) >= 30:
                break

    return results

def parse_generic(html, base_url):
    """Fallback para sites genéricos: busca links em tags h1/h2/h3 e primeiras <p> após o link."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()

    for tag in soup.select("h1 a, h2 a, h3 a, a"):
        a = tag
        href = a.get("href")
        title = a.get_text(strip=True)
        if not href or not title:
            continue
        if href.startswith("/"):
            href = urljoin(base_url, href)
        if (title, href) in seen:
            continue
        seen.add((title, href))
        resumo = ""
        # tentar buscar parágrafo próximo
        parent = a.parent
        if parent:
            p = parent.find_next("p")
            if p:
                resumo = p.get_text(strip=True)[:400]
        results.append({"titulo": title, "link": href, "resumo": resumo})
        if len(results) >= 30:
            break
    return results

def save_json(data, filename="manchetes.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def run(url=DEFAULT_URL, out_file="manchetes.json"):
    print(f"[+] Acessando: {url}")
    try:
        html = fetch(url)
    except Exception as e:
        print(f"[!] Erro ao acessar {url}: {e}")
        return

    # Se for G1 (ou domínio globo), tentar parse_g1
    try:
        data = parse_g1(html, base_url=url)
        if not data:
            data = parse_generic(html, base_url=url)
    except Exception as e:
        print("[!] Erro no parser específico:", e)
        data = parse_generic(html, base_url=url)

    if not data:
        print("[!] Nenhuma manchete encontrada.")
    else:
        save_json(data, out_file)
        print(f"[+] Salvou {len(data)} itens em {out_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scraper de notícias (salva manchetes.json).")
    parser.add_argument("--url", "-u", help="URL do site para raspar (por padrão G1).", default=DEFAULT_URL)
    parser.add_argument("--out", "-o", help="Arquivo de saída JSON", default="manchetes.json")
    args = parser.parse_args()
    run(url=args.url, out_file=args.out)
