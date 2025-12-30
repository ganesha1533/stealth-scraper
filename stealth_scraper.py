#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    STEALTH SCRAPER - by VanGogh Dev                            ║
║           Framework Avançado de Web Scraping com Anti-Detection                ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Features:
- Rotação automática de User-Agents
- Proxy rotation
- Fingerprint randomization
- Cloudflare/Akamai bypass
- Rate limiting inteligente
- Sessões persistentes
- Retry com backoff exponencial
"""

import random
import time
import hashlib
import json
import logging
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StealthScraper")


# ═══════════════════════════════════════════════════════════════════════════════
# USER AGENTS DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

USER_AGENTS = {
    "chrome_windows": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ],
    "chrome_mac": [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ],
    "firefox_windows": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    ],
    "firefox_mac": [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    ],
    "safari_mac": [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    ],
    "edge_windows": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ],
    "mobile_android": [
        "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    ],
    "mobile_ios": [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    ]
}


# ═══════════════════════════════════════════════════════════════════════════════
# FINGERPRINT PROFILES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BrowserProfile:
    """Perfil de navegador para fingerprinting consistente"""
    user_agent: str
    platform: str
    language: str
    timezone: str
    screen_resolution: str
    color_depth: int
    accept_encoding: str
    accept_language: str
    sec_ch_ua: str = ""
    sec_ch_ua_mobile: str = "?0"
    sec_ch_ua_platform: str = ""
    
    def to_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": self.accept_language,
            "Accept-Encoding": self.accept_encoding,
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }
        
        if self.sec_ch_ua:
            headers.update({
                "Sec-CH-UA": self.sec_ch_ua,
                "Sec-CH-UA-Mobile": self.sec_ch_ua_mobile,
                "Sec-CH-UA-Platform": self.sec_ch_ua_platform,
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            })
        
        return headers


class ProfileGenerator:
    """Gera perfis de navegador realistas"""
    
    LANGUAGES = ["pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7", "en-US,en;q=0.9", "pt-BR,pt;q=0.9"]
    TIMEZONES = ["America/Sao_Paulo", "America/New_York", "Europe/London"]
    RESOLUTIONS = ["1920x1080", "1366x768", "2560x1440", "1536x864", "1440x900"]
    
    @classmethod
    def generate_chrome_profile(cls) -> BrowserProfile:
        ua = random.choice(USER_AGENTS["chrome_windows"] + USER_AGENTS["chrome_mac"])
        is_windows = "Windows" in ua
        
        return BrowserProfile(
            user_agent=ua,
            platform="Win32" if is_windows else "MacIntel",
            language=random.choice(cls.LANGUAGES),
            timezone=random.choice(cls.TIMEZONES),
            screen_resolution=random.choice(cls.RESOLUTIONS),
            color_depth=24,
            accept_encoding="gzip, deflate, br",
            accept_language=random.choice(cls.LANGUAGES),
            sec_ch_ua='"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            sec_ch_ua_mobile="?0",
            sec_ch_ua_platform='"Windows"' if is_windows else '"macOS"'
        )
    
    @classmethod
    def generate_firefox_profile(cls) -> BrowserProfile:
        ua = random.choice(USER_AGENTS["firefox_windows"] + USER_AGENTS["firefox_mac"])
        is_windows = "Windows" in ua
        
        return BrowserProfile(
            user_agent=ua,
            platform="Win32" if is_windows else "MacIntel",
            language=random.choice(cls.LANGUAGES),
            timezone=random.choice(cls.TIMEZONES),
            screen_resolution=random.choice(cls.RESOLUTIONS),
            color_depth=24,
            accept_encoding="gzip, deflate, br",
            accept_language=random.choice(cls.LANGUAGES)
        )
    
    @classmethod
    def generate_mobile_profile(cls) -> BrowserProfile:
        ua = random.choice(USER_AGENTS["mobile_android"] + USER_AGENTS["mobile_ios"])
        is_android = "Android" in ua
        
        return BrowserProfile(
            user_agent=ua,
            platform="Linux armv8l" if is_android else "iPhone",
            language=random.choice(cls.LANGUAGES),
            timezone=random.choice(cls.TIMEZONES),
            screen_resolution="412x915" if is_android else "390x844",
            color_depth=24,
            accept_encoding="gzip, deflate, br",
            accept_language=random.choice(cls.LANGUAGES),
            sec_ch_ua_mobile="?1"
        )
    
    @classmethod
    def generate_random(cls) -> BrowserProfile:
        generators = [cls.generate_chrome_profile, cls.generate_firefox_profile, cls.generate_mobile_profile]
        weights = [0.6, 0.3, 0.1]  # Chrome é mais comum
        return random.choices(generators, weights=weights)[0]()


# ═══════════════════════════════════════════════════════════════════════════════
# PROXY MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Proxy:
    """Representa um proxy"""
    host: str
    port: int
    protocol: str = "http"
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    failures: int = 0
    last_used: float = 0
    
    @property
    def url(self) -> str:
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "http": self.url,
            "https": self.url
        }


class ProxyManager:
    """Gerencia pool de proxies com rotação inteligente"""
    
    def __init__(self, proxies: List[Proxy] = None, max_failures: int = 3):
        self.proxies = proxies or []
        self.max_failures = max_failures
        self.current_index = 0
    
    def add_proxy(self, proxy: Proxy):
        self.proxies.append(proxy)
    
    def add_from_string(self, proxy_string: str):
        """Parse proxy string: protocol://user:pass@host:port or host:port"""
        try:
            if "://" in proxy_string:
                parsed = urlparse(proxy_string)
                self.proxies.append(Proxy(
                    host=parsed.hostname,
                    port=parsed.port,
                    protocol=parsed.scheme,
                    username=parsed.username,
                    password=parsed.password
                ))
            else:
                parts = proxy_string.split(":")
                self.proxies.append(Proxy(host=parts[0], port=int(parts[1])))
        except Exception as e:
            logger.warning(f"Failed to parse proxy: {proxy_string} - {e}")
    
    def load_from_file(self, filepath: str):
        """Carrega proxies de arquivo (um por linha)"""
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        self.add_from_string(line)
            logger.info(f"Loaded {len(self.proxies)} proxies from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load proxies: {e}")
    
    def get_next(self) -> Optional[Proxy]:
        """Retorna próximo proxy disponível"""
        if not self.proxies:
            return None
        
        # Remove proxies com muitas falhas
        self.proxies = [p for p in self.proxies if p.failures < self.max_failures]
        
        if not self.proxies:
            return None
        
        # Rotação round-robin
        self.current_index = (self.current_index + 1) % len(self.proxies)
        proxy = self.proxies[self.current_index]
        proxy.last_used = time.time()
        
        return proxy
    
    def mark_failure(self, proxy: Proxy):
        """Marca falha no proxy"""
        proxy.failures += 1
        logger.warning(f"Proxy {proxy.host}:{proxy.port} failure #{proxy.failures}")
    
    def mark_success(self, proxy: Proxy):
        """Marca sucesso no proxy (reseta contador de falhas)"""
        proxy.failures = 0


# ═══════════════════════════════════════════════════════════════════════════════
# RATE LIMITER
# ═══════════════════════════════════════════════════════════════════════════════

class RateLimiter:
    """Rate limiter por domínio com delays humanizados"""
    
    def __init__(self, requests_per_second: float = 1.0, min_delay: float = 0.5, max_delay: float = 3.0):
        self.requests_per_second = requests_per_second
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.domain_last_request: Dict[str, float] = {}
    
    def wait(self, url: str):
        """Aguarda tempo necessário antes da próxima request"""
        domain = urlparse(url).netloc
        
        if domain in self.domain_last_request:
            elapsed = time.time() - self.domain_last_request[domain]
            min_interval = 1.0 / self.requests_per_second
            
            if elapsed < min_interval:
                # Adiciona variação humana
                delay = min_interval - elapsed + random.uniform(self.min_delay, self.max_delay)
                time.sleep(delay)
        
        self.domain_last_request[domain] = time.time()
    
    def random_delay(self):
        """Delay aleatório para parecer humano"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)


# ═══════════════════════════════════════════════════════════════════════════════
# STEALTH SESSION
# ═══════════════════════════════════════════════════════════════════════════════

class StealthSession:
    """Sessão HTTP com recursos anti-detection"""
    
    def __init__(
        self,
        profile: BrowserProfile = None,
        proxy_manager: ProxyManager = None,
        rate_limiter: RateLimiter = None,
        max_retries: int = 3,
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        self.profile = profile or ProfileGenerator.generate_random()
        self.proxy_manager = proxy_manager
        self.rate_limiter = rate_limiter or RateLimiter()
        self.max_retries = max_retries
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        self.session = self._create_session()
        self.cookies: Dict[str, str] = {}
        self.request_count = 0
    
    def _create_session(self) -> requests.Session:
        """Cria sessão com retry automático"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers base do perfil
        session.headers.update(self.profile.to_headers())
        
        return session
    
    def rotate_profile(self):
        """Rotaciona para novo perfil de navegador"""
        self.profile = ProfileGenerator.generate_random()
        self.session.headers.update(self.profile.to_headers())
        logger.debug("Profile rotated")
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """GET request com stealth"""
        return self._request("GET", url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """POST request com stealth"""
        return self._request("POST", url, **kwargs)
    
    def _request(self, method: str, url: str, rotate_profile: bool = False, **kwargs) -> requests.Response:
        """Request genérico com todas as proteções"""
        
        if rotate_profile or self.request_count > 0 and self.request_count % 10 == 0:
            self.rotate_profile()
        
        # Rate limiting
        self.rate_limiter.wait(url)
        
        # Adiciona Referer realista
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        
        parsed = urlparse(url)
        kwargs["headers"]["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"
        kwargs["headers"]["Origin"] = f"{parsed.scheme}://{parsed.netloc}"
        
        # Proxy
        proxy = None
        if self.proxy_manager:
            proxy = self.proxy_manager.get_next()
            if proxy:
                kwargs["proxies"] = proxy.to_dict()
        
        # Timeout
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("verify", self.verify_ssl)
        
        try:
            response = self.session.request(method, url, **kwargs)
            self.request_count += 1
            
            if proxy:
                self.proxy_manager.mark_success(proxy)
            
            # Detecta bloqueios
            if self._is_blocked(response):
                logger.warning(f"Possible block detected on {url}")
                self.rate_limiter.random_delay()
                self.rotate_profile()
            
            return response
            
        except requests.exceptions.RequestException as e:
            if proxy:
                self.proxy_manager.mark_failure(proxy)
            raise
    
    def _is_blocked(self, response: requests.Response) -> bool:
        """Detecta se request foi bloqueada"""
        blocked_indicators = [
            "captcha",
            "challenge",
            "blocked",
            "access denied",
            "rate limit",
            "too many requests",
            "cf-browser-verification",
            "security check"
        ]
        
        # Status codes suspeitos
        if response.status_code in [403, 429, 503]:
            return True
        
        # Verifica conteúdo
        content_lower = response.text.lower()
        return any(indicator in content_lower for indicator in blocked_indicators)


# ═══════════════════════════════════════════════════════════════════════════════
# CLOUDFLARE BYPASS
# ═══════════════════════════════════════════════════════════════════════════════

class CloudflareBypass:
    """Técnicas para bypass de Cloudflare"""
    
    @staticmethod
    def get_headers_v1() -> Dict[str, str]:
        """Headers otimizados para Cloudflare"""
        return {
            "User-Agent": random.choice(USER_AGENTS["chrome_windows"]),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Cache-Control": "max-age=0",
        }
    
    @staticmethod
    def solve_js_challenge(html: str) -> Optional[Dict]:
        """Tenta resolver JS challenge simples do Cloudflare"""
        # Esta é uma implementação básica - challenges complexos precisam de browser
        import re
        
        # Procura por parâmetros do challenge
        patterns = {
            "jschl_vc": r'name="jschl_vc" value="([^"]+)"',
            "pass": r'name="pass" value="([^"]+)"',
            "jschl_answer": r'name="jschl_answer" value="([^"]+)"',
        }
        
        result = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, html)
            if match:
                result[key] = match.group(1)
        
        return result if result else None


# ═══════════════════════════════════════════════════════════════════════════════
# SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════

class StealthScraper:
    """Scraper principal com todas as funcionalidades"""
    
    def __init__(
        self,
        proxy_file: str = None,
        requests_per_second: float = 0.5,
        max_workers: int = 5
    ):
        self.proxy_manager = ProxyManager()
        if proxy_file:
            self.proxy_manager.load_from_file(proxy_file)
        
        self.rate_limiter = RateLimiter(requests_per_second=requests_per_second)
        self.max_workers = max_workers
        self.results: List[Dict] = []
    
    def create_session(self) -> StealthSession:
        """Cria nova sessão stealth"""
        return StealthSession(
            proxy_manager=self.proxy_manager if self.proxy_manager.proxies else None,
            rate_limiter=self.rate_limiter
        )
    
    def scrape_url(self, url: str, parser: Callable = None) -> Dict:
        """Scrape uma URL"""
        session = self.create_session()
        
        try:
            response = session.get(url)
            
            result = {
                "url": url,
                "status_code": response.status_code,
                "content_length": len(response.content),
                "success": response.status_code == 200
            }
            
            if parser and response.status_code == 200:
                result["data"] = parser(response)
            else:
                result["html"] = response.text[:1000]  # Preview
            
            return result
            
        except Exception as e:
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }
    
    def scrape_urls(self, urls: List[str], parser: Callable = None) -> List[Dict]:
        """Scrape múltiplas URLs em paralelo"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.scrape_url, url, parser): url for url in urls}
            
            for future in as_completed(futures):
                url = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Scraped {url}: {result.get('status_code', 'error')}")
                except Exception as e:
                    results.append({"url": url, "error": str(e)})
        
        return results
    
    def crawl(self, start_url: str, max_pages: int = 100, parser: Callable = None) -> List[Dict]:
        """Crawler simples com extração de links"""
        from html.parser import HTMLParser
        
        class LinkExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links = []
            
            def handle_starttag(self, tag, attrs):
                if tag == 'a':
                    for attr, value in attrs:
                        if attr == 'href':
                            self.links.append(value)
        
        visited = set()
        to_visit = [start_url]
        results = []
        base_domain = urlparse(start_url).netloc
        
        session = self.create_session()
        
        while to_visit and len(visited) < max_pages:
            url = to_visit.pop(0)
            
            if url in visited:
                continue
            
            visited.add(url)
            
            try:
                response = session.get(url)
                
                result = {
                    "url": url,
                    "status_code": response.status_code
                }
                
                if parser:
                    result["data"] = parser(response)
                
                results.append(result)
                
                # Extrai links
                if response.status_code == 200:
                    extractor = LinkExtractor()
                    extractor.feed(response.text)
                    
                    for link in extractor.links:
                        full_url = urljoin(url, link)
                        if urlparse(full_url).netloc == base_domain:
                            if full_url not in visited:
                                to_visit.append(full_url)
                
                logger.info(f"Crawled {url} ({len(visited)}/{max_pages})")
                
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
        
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# EXEMPLO DE USO
# ═══════════════════════════════════════════════════════════════════════════════

def example_usage():
    """Exemplos de uso do StealthScraper"""
    
    print("=" * 60)
    print("🎨 STEALTH SCRAPER - by VanGogh Dev")
    print("=" * 60)
    
    # Exemplo 1: Sessão simples
    print("\n[1] Sessão Stealth Simples:")
    session = StealthSession()
    print(f"    User-Agent: {session.profile.user_agent[:50]}...")
    print(f"    Platform: {session.profile.platform}")
    
    # Exemplo 2: Request com rate limiting
    print("\n[2] Request com Rate Limiting:")
    try:
        response = session.get("https://httpbin.org/ip")
        print(f"    Status: {response.status_code}")
        print(f"    IP: {response.json()}")
    except Exception as e:
        print(f"    Error: {e}")
    
    # Exemplo 3: Scraper com múltiplas URLs
    print("\n[3] Multi-URL Scraping:")
    scraper = StealthScraper(requests_per_second=0.5)
    urls = [
        "https://httpbin.org/headers",
        "https://httpbin.org/user-agent",
    ]
    results = scraper.scrape_urls(urls)
    for r in results:
        print(f"    {r['url']}: {r.get('status_code', 'error')}")
    
    print("\n" + "=" * 60)
    print("✅ Exemplos concluídos!")
    print("=" * 60)


if __name__ == "__main__":
    example_usage()
