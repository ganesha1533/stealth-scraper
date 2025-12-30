# 🕵️ Stealth Scraper

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Anti-Detection](https://img.shields.io/badge/Anti--Detection-Advanced-red.svg)

**Framework avançado de Web Scraping com bypass de anti-bot**

[Instalação](#-instalação) •
[Features](#-features) •
[Uso](#-uso) •
[API](#-api) •
[Contribuir](#-contribuir)

</div>

---

## 🎯 O que é?

Stealth Scraper é um framework Python para web scraping que simula comportamento humano real, evitando detecção por sistemas anti-bot como Cloudflare, Akamai, e reCAPTCHA.

## ⚡ Features

| Feature | Descrição |
|---------|-----------|
| **Fingerprint Rotation** | User-Agents, headers e perfis de browser realistas |
| **Proxy Management** | Pool de proxies com rotação automática e detecção de falhas |
| **Rate Limiting** | Delays humanizados e controle por domínio |
| **Session Persistence** | Cookies e sessões persistentes |
| **Retry Logic** | Backoff exponencial automático |
| **Cloudflare Bypass** | Headers otimizados para bypass |
| **Multi-threading** | Scraping paralelo com controle de concorrência |

## 🚀 Instalação

```bash
git clone https://github.com/vangoghdev/stealth-scraper.git
cd stealth-scraper
pip install -r requirements.txt
```

## 📖 Uso

### Sessão Simples

```python
from stealth_scraper import StealthSession

session = StealthSession()
response = session.get("https://example.com")
print(response.text)
```

### Com Rotação de Proxy

```python
from stealth_scraper import StealthSession, ProxyManager

# Criar pool de proxies
proxy_manager = ProxyManager()
proxy_manager.add_from_string("http://user:pass@proxy.com:8080")
proxy_manager.load_from_file("proxies.txt")

# Sessão com proxy
session = StealthSession(proxy_manager=proxy_manager)
response = session.get("https://example.com")
```

### Multi-URL Scraping

```python
from stealth_scraper import StealthScraper

scraper = StealthScraper(
    proxy_file="proxies.txt",
    requests_per_second=0.5,
    max_workers=5
)

urls = [
    "https://site1.com/page1",
    "https://site2.com/page2",
    "https://site3.com/page3",
]

results = scraper.scrape_urls(urls)
for r in results:
    print(f"{r['url']}: {r['status_code']}")
```

### Parser Customizado

```python
from bs4 import BeautifulSoup

def my_parser(response):
    soup = BeautifulSoup(response.text, 'html.parser')
    return {
        "title": soup.title.string,
        "links": [a['href'] for a in soup.find_all('a', href=True)]
    }

results = scraper.scrape_urls(urls, parser=my_parser)
```

### Crawler

```python
results = scraper.crawl(
    start_url="https://example.com",
    max_pages=100,
    parser=my_parser
)
```

## 🛡️ Anti-Detection Features

### Fingerprint Profiles

O sistema gera perfis de browser consistentes que incluem:

- User-Agent realista
- Headers Sec-CH-UA (Client Hints)
- Accept-Language matching
- Platform matching
- Screen resolution simulada

### Rate Limiting Humanizado

```python
from stealth_scraper import RateLimiter

limiter = RateLimiter(
    requests_per_second=0.5,  # Max 1 request a cada 2s
    min_delay=1.0,            # Delay mínimo entre requests
    max_delay=5.0             # Delay máximo (variação humana)
)
```

### Detecção de Bloqueio

O sistema detecta automaticamente quando está sendo bloqueado:
- Status 403, 429, 503
- Palavras-chave (captcha, challenge, blocked)
- Challenge pages do Cloudflare

## 📁 Formato de Proxies

```text
# proxies.txt
http://user:pass@proxy1.com:8080
socks5://proxy2.com:1080
192.168.1.1:8080
```

## ⚠️ Aviso Legal

Esta ferramenta é para fins **educacionais e de pesquisa**. Use de forma responsável:

- Respeite robots.txt
- Não sobrecarregue servidores
- Verifique os Termos de Serviço dos sites
- Uso indevido é de responsabilidade do usuário

## 🤝 Contribuir

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/NovaFeature`)
3. Commit suas mudanças (`git commit -m 'Add: nova feature'`)
4. Push para a branch (`git push origin feature/NovaFeature`)
5. Abra um Pull Request

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

---

<div align="center">

### 🎨 Desenvolvido por **VanGogh Dev**

[![GitHub](https://img.shields.io/badge/GitHub-VanGoghDev-black?style=flat&logo=github)](https://github.com/vangoghdev)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-+595%20987%20352983-25D366?style=flat&logo=whatsapp)](https://wa.me/595987352983)

**☕ Me apoie:**

[![Crypto](https://img.shields.io/badge/Donate-Crypto-orange?style=flat&logo=bitcoin)](https://plisio.net/donate/phlGd6L5)
[![Donate](https://img.shields.io/badge/Donate-PIX%2FOther-green?style=flat)](https://vendas.snoopintelligence.space/#donate)

</div>
