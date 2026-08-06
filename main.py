import os, random, asyncio, aiohttp, aiofiles, json, time, sys, socket
from colorama import Fore, init
from concurrent.futures import ThreadPoolExecutor

init(autoreset=True)

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════
CONFIG_PATH = 'config/config.json'
PROXIES_PATH = 'config/proxies.txt'
RESULTS_PATH = 'results/hit.txt'
GOOD_PROXIES_PATH = 'config/good_proxies.txt'

DEFAULT_CONFIG = {
    "concurrent": 2000,
    "batch_size": 1000,
    "webhook": {
        "url": "https://discord.com/api/webhooks/1534684880288612513/lYtS-D0S3a2ifLLKuA9kFxHWcIMi8IDQuoBRLsP2UZP1PdZGrQnRKYi6GBu9DPvAikCf",
        "username": "leo/l6",
        "avatar": ""
    },
    "auto_scrape_proxies": True,
    "proxy_sources": [
        {"url": "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text", "type": "auto"},
        {"url": "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.txt", "type": "auto"},
        {"url": "https://raw.githubusercontent.com/komutan234/Proxy-List-Free/main/proxies/http.txt", "type": "http"},
        {"url": "https://raw.githubusercontent.com/komutan234/Proxy-List-Free/main/proxies/socks4.txt", "type": "socks4"},
        {"url": "https://raw.githubusercontent.com/komutan234/Proxy-List-Free/main/proxies/socks5.txt", "type": "socks5"},
        {"url": "https://raw.githubusercontent.com/VPSLabCloud/VPSLab-Free-Proxy-List/main/http_all.txt", "type": "http"},
        {"url": "https://raw.githubusercontent.com/VPSLabCloud/VPSLab-Free-Proxy-List/main/socks5_all.txt", "type": "socks5"},
        {"url": "https://raw.githubusercontent.com/wiki/gfpcom/free-proxy-list/lists/http.txt", "type": "http"},
        {"url": "https://raw.githubusercontent.com/wiki/gfpcom/free-proxy-list/lists/https.txt", "type": "http"},
        {"url": "https://raw.githubusercontent.com/wiki/gfpcom/free-proxy-list/lists/socks5.txt", "type": "socks5"},
        {"url": "https://cdn.jsdelivr.net/gh/officialputuid/KangProxy@main/http/http.txt", "type": "http"},
        {"url": "https://cdn.jsdelivr.net/gh/officialputuid/KangProxy@main/socks5/socks5.txt", "type": "socks5"},
        {"url": "https://cdn.jsdelivr.net/gh/officialputuid/KangProxy@main/xResults/Proxies.txt", "type": "auto"},
        {"url": "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/proxies/http.txt", "type": "http"},
        {"url": "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/proxies/socks5.txt", "type": "socks5"}
    ],
    "timeout": 3,
    "proxy_check_timeout": 5,
    "proxy_check_url": "https://discord.com/api/v9/gateway",
    "max_good_proxies": 5000,
    "use_random_ua": True,
    "promo_code_length": 24,
    "promo_format": "plain",
    "api_version": "v9",
    "scrape_interval_minutes": 20,
    "restart_on_crash": True,
    "dns_cache_ttl": 300,
    "keepalive_timeout": 30,
    "tcp_limit": 0,
    "tcp_limit_per_host": 0
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.2535.79"
]

# ═══════════════════════════════════════════════════════════════
# UTILS
# ═══════════════════════════════════════════════════════════════
def ensure_dirs():
    os.makedirs('config', exist_ok=True)
    os.makedirs('results', exist_ok=True)

def load_config():
    ensure_dirs()
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    sources = cfg.get("proxy_sources", [])
    new_sources = []
    for s in sources:
        if isinstance(s, str):
            t = "http"
            if "socks5" in s.lower(): t = "socks5"
            elif "socks4" in s.lower(): t = "socks4"
            new_sources.append({"url": s, "type": t})
        else:
            new_sources.append(s)
    cfg["proxy_sources"] = new_sources
    return cfg

def save_config(cfg):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4)

def center(var: str, space: int = None):
    try:
        if not space:
            space = (os.get_terminal_size().columns - len(var.splitlines()[int(len(var.splitlines()) / 2)])) / 2
    except:
        space = 0
    return "\n".join((' ' * int(space)) + line for line in var.splitlines())

# ═══════════════════════════════════════════════════════════════
# PROXY SCRAPER
# ═══════════════════════════════════════════════════════════════
class ProxyScraper:
    def __init__(self, sources):
        self.sources = sources
        self.proxies = []

    def _clean_proxy(self, line, default_type="http"):
        line = line.strip()
        if not line or line.startswith("#"):
            return None
        for prefix in ['http://', 'https://', 'socks4://', 'socks5://']:
            if line.lower().startswith(prefix):
                rest = line[len(prefix):]
                if ':' in rest:
                    parts = rest.rsplit(':', 1)
                    if len(parts) == 2 and parts[1].isdigit():
                        port = int(parts[1])
                        if 1 <= port <= 65535:
                            return line
                return None
        if ':' in line:
            parts = line.rsplit(':', 1)
            if len(parts) == 2 and parts[1].isdigit():
                port = int(parts[1])
                if 1 <= port <= 65535:
                    return f"{default_type}://{line}"
        return None

    async def scrape(self):
        self.proxies = []
        print(f"{Fore.CYAN}[INFO]{Fore.RESET} Scraping proxies from {len(self.sources)} source(s)...\n")
        connector = aiohttp.TCPConnector(limit=200, limit_per_host=50, ttl_dns_cache=300)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for src in self.sources:
                url = src.get("url", "") if isinstance(src, dict) else src
                ptype = src.get("type", "http") if isinstance(src, dict) else "http"
                tasks.append(self._fetch_source(session, url, ptype))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, list):
                    self.proxies.extend(res)
        self.proxies = list(dict.fromkeys(self.proxies))
        print(f"\n{Fore.CYAN}[INFO]{Fore.RESET} Total unique proxies scraped: {Fore.GREEN}{len(self.proxies)}{Fore.RESET}")
        return self.proxies

    async def _fetch_source(self, session, url, ptype):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15), headers={"User-Agent": random.choice(USER_AGENTS)}) as r:
                if r.status == 200:
                    text = await r.text()
                    lines = [self._clean_proxy(line, ptype) for line in text.splitlines()]
                    lines = [p for p in lines if p]
                    print(f"{Fore.GREEN}[OK]{Fore.RESET}  {url[:55]}... -> {len(lines)} {ptype} proxies")
                    return lines
                else:
                    print(f"{Fore.RED}[FAIL]{Fore.RESET} {url[:55]}... -> HTTP {r.status}")
                    return []
        except Exception as e:
            print(f"{Fore.RED}[ERR]{Fore.RESET}  {url[:55]}... -> {str(e)[:45]}")
            return []

    async def save(self, path=PROXIES_PATH):
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            for p in self.proxies:
                await f.write(p + "\n")
        print(f"{Fore.CYAN}[INFO]{Fore.RESET} Saved {len(self.proxies)} proxies to {path}")

    async def load(self, path=PROXIES_PATH):
        if not os.path.exists(path):
            return []
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            content = await f.read()
        return [line.strip() for line in content.splitlines() if line.strip() and '://' in line]

# ═══════════════════════════════════════════════════════════════
# PROXY CHECKER - Filter working proxies only
# ═══════════════════════════════════════════════════════════════
class ProxyChecker:
    def __init__(self, cfg):
        self.cfg = cfg
        self.good_proxies = []
        self.checked = 0
        self.lock = asyncio.Lock()

    async def check_proxy(self, session, proxy):
        try:
            async with session.get(
                self.cfg.get("proxy_check_url", "https://discord.com/api/v9/gateway"),
                proxy=proxy,
                timeout=aiohttp.ClientTimeout(total=self.cfg.get("proxy_check_timeout", 5)),
                headers={"User-Agent": random.choice(USER_AGENTS)}
            ) as r:
                if r.status in [200, 301, 302, 403, 429]:
                    async with self.lock:
                        self.good_proxies.append(proxy)
                        self.checked += 1
                    return True
        except:
            async with self.lock:
                self.checked += 1
        return False

    async def check_all(self, proxies):
        print(f"\n{Fore.CYAN}[INFO]{Fore.RESET} Testing {len(proxies)} proxies for speed...")
        connector = aiohttp.TCPConnector(limit=0, limit_per_host=0, ttl_dns_cache=300, use_dns_cache=True)
        async with aiohttp.ClientSession(connector=connector) as session:
            sem = asyncio.Semaphore(500)
            async def check_one(p):
                async with sem:
                    return await self.check_proxy(session, p)
            tasks = [check_one(p) for p in proxies]
            await asyncio.gather(*tasks, return_exceptions=True)

        max_good = self.cfg.get("max_good_proxies", 5000)
        if len(self.good_proxies) > max_good:
            self.good_proxies = random.sample(self.good_proxies, max_good)

        print(f"{Fore.GREEN}[OK]{Fore.RESET} {len(self.good_proxies)} working proxies found!")
        return self.good_proxies

    async def save_good(self, path=GOOD_PROXIES_PATH):
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            for p in self.good_proxies:
                await f.write(p + "\n")
        print(f"{Fore.CYAN}[INFO]{Fore.RESET} Saved {len(self.good_proxies)} good proxies to {path}\n")

    async def load_good(self, path=GOOD_PROXIES_PATH):
        if not os.path.exists(path):
            return []
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            content = await f.read()
        return [line.strip() for line in content.splitlines() if line.strip() and '://' in line]

# ═══════════════════════════════════════════════════════════════
# CONSOLE
# ═══════════════════════════════════════════════════════════════
class Console:
    def __init__(self):
        self._lock = asyncio.Lock()

    def ui(self):
        os.system('cls && title [DNG] Discord Promo Generator ^| ULTRA SPEED' if os.name == "nt" else "clear")
        banner = center(f"""\n\n
██████╗ ███╗   ██╗ ██████╗ 
██╔══██╗████╗  ██║██╔════╝            ~ Discord Promo Generator ~
██║  ██║██╔██╗ ██║██║  ███╗     
██║  ██║██║╚██╗██║██║   ██║     ULTRA SPEED ~ aiohttp ~ 24/7
██████╔╝██║ ╚████║╚██████╔╝ 
╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ \n\n
              """)
        print(banner.replace('█', Fore.CYAN + "█" + Fore.RESET).replace('~', Fore.CYAN + "~" + Fore.RESET))

    async def printer(self, color, status, code):
        async with self._lock:
            print(f"{color} {status} > {Fore.RESET}https://promos.discord.gg/{code}")

    async def log(self, color, tag, msg):
        async with self._lock:
            print(f"{color}[{tag}]{Fore.RESET} {msg}")

# ═══════════════════════════════════════════════════════════════
# GENERATOR
# ═══════════════════════════════════════════════════════════════
def generate_code(length=24, fmt="plain"):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    code = "".join(random.choice(chars) for _ in range(length))
    if fmt == "dashed":
        return "-".join([code[i:i+4] for i in range(0, length, 4)])
    return code

# ═══════════════════════════════════════════════════════════════
# WEBHOOK
# ═══════════════════════════════════════════════════════════════
async def send_webhook(session, cfg, code, gift_data=None):
    url = cfg.get("webhook", {}).get("url", "")
    if not url:
        return
    embed = {
        "title": "🎉 VALID PROMO CODE FOUND!",
        "description": f"**Code:** `https://promos.discord.gg/{code}`\n\n[Click to Redeem](https://promos.discord.gg/{code})",
        "color": 0x00ff00,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
        "footer": {"text": "DNG Promo Generator v4.0"}
    }
    if gift_data:
        if 'subscription_plan' in gift_data:
            plan = gift_data['subscription_plan']
            embed["fields"] = [
                {"name": "Plan", "value": plan.get('name', 'Unknown'), "inline": True},
                {"name": "Interval", "value": plan.get('interval', 'Unknown'), "inline": True}
            ]
        if 'expires_at' in gift_data:
            embed["fields"] = embed.get("fields", []) + [
                {"name": "Expires", "value": gift_data['expires_at'], "inline": True}
            ]
    payload = {
        "content": "||@everyone|| **VALID PROMO CODE DETECTED!**",
        "username": cfg.get("webhook", {}).get("username", "DNG Promo"),
        "avatar_url": cfg.get("webhook", {}).get("avatar", ""),
        "embeds": [embed]
    }
    try:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)):
            pass
    except:
        pass

# ═══════════════════════════════════════════════════════════════
# ULTRA FAST CHECKER
# ═══════════════════════════════════════════════════════════════
class UltraChecker:
    def __init__(self, cfg, proxies, console):
        self.cfg = cfg
        self.proxies = proxies
        self.console = console
        self.checked = 0
        self.valid = 0
        self.invalid = 0
        self.ratelimited = 0
        self.errors = 0
        self.lock = asyncio.Lock()
        self.proxy_idx = 0
        self.batch_size = cfg.get("batch_size", 1000)

    def get_proxy(self):
        if not self.proxies:
            return None
        p = self.proxies[self.proxy_idx % len(self.proxies)]
        self.proxy_idx += 1
        return p

    def get_headers(self):
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://discord.com",
            "Referer": "https://discord.com/",
            "X-Discord-Locale": "en-US",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        if self.cfg.get("use_random_ua", True):
            headers["User-Agent"] = random.choice(USER_AGENTS)
        return headers

    async def check_one(self, session, code):
        proxy = self.get_proxy()
        api_ver = self.cfg.get("api_version", "v9")
        url = f"https://discord.com/api/{api_ver}/entitlements/gift-codes/{code}?with_application=false&with_subscription_plan=true"

        try:
            if proxy:
                async with session.get(url, headers=self.get_headers(), proxy=proxy, 
                                       timeout=aiohttp.ClientTimeout(total=self.cfg.get("timeout", 3)),
                                       ssl=False) as r:
                    status = r.status
                    if status == 200:
                        data = await r.json()
            else:
                async with session.get(url, headers=self.get_headers(),
                                       timeout=aiohttp.ClientTimeout(total=self.cfg.get("timeout", 3)),
                                       ssl=False) as r:
                    status = r.status
                    if status == 200:
                        data = await r.json()

            if status == 200:
                await self.console.printer(Fore.LIGHTGREEN_EX, " VALID ", code)
                async with self.lock:
                    self.valid += 1
                    self.checked += 1
                async with aiofiles.open(RESULTS_PATH, 'a', encoding='utf-8') as f:
                    await f.write(f"https://promos.discord.gg/{code}\n")
                await send_webhook(session, self.cfg, code, data)

            elif status == 404:
                async with self.lock:
                    self.invalid += 1
                    self.checked += 1

            elif status == 429:
                async with self.lock:
                    self.ratelimited += 1
                    self.checked += 1

            elif status in [403, 401]:
                async with self.lock:
                    self.checked += 1
                    self.errors += 1

            else:
                async with self.lock:
                    self.checked += 1

        except asyncio.TimeoutError:
            async with self.lock:
                self.errors += 1
        except aiohttp.ClientProxyConnectionError:
            async with self.lock:
                self.errors += 1
        except aiohttp.ClientHttpProxyError:
            async with self.lock:
                self.errors += 1
        except aiohttp.ClientConnectorError:
            async with self.lock:
                self.errors += 1
        except Exception:
            async with self.lock:
                self.errors += 1

    async def run_batch(self, session, codes):
        tasks = [self.check_one(session, code) for code in codes]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def run(self):
        connector = aiohttp.TCPConnector(
            limit=self.cfg.get("tcp_limit", 0),
            limit_per_host=self.cfg.get("tcp_limit_per_host", 0),
            ttl_dns_cache=self.cfg.get("dns_cache_ttl", 300),
            use_dns_cache=True,
            enable_cleanup_closed=True,
            force_close=False
        )
        timeout = aiohttp.ClientTimeout(total=None, connect=3, sock_connect=3, sock_read=3)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            while True:
                codes = [generate_code(self.cfg.get("promo_code_length", 24), self.cfg.get("promo_format", "plain")) for _ in range(self.batch_size)]
                await self.run_batch(session, codes)

# ═══════════════════════════════════════════════════════════════
# STATS
# ═══════════════════════════════════════════════════════════════
async def stats_worker(checker, start_time):
    last_checked = 0
    while True:
        await asyncio.sleep(10)
        elapsed = max(1, time.time() - start_time)
        cps = checker.checked / elapsed
        rps = (checker.checked - last_checked) / 10
        last_checked = checker.checked
        await checker.console.log(
            Fore.CYAN, "STATS",
            f"Checked: {checker.checked} | Valid: {Fore.GREEN}{checker.valid}{Fore.RESET} | "
            f"Invalid: {checker.invalid} | RateLimited: {checker.ratelimited} | "
            f"Errors: {checker.errors} | Avg: {Fore.YELLOW}{cps:.1f}{Fore.RESET} req/s | "
            f"Current: {Fore.YELLOW}{rps:.1f}{Fore.RESET} req/s"
        )

# ═══════════════════════════════════════════════════════════════
# PROXY RE-SCRAPER
# ═══════════════════════════════════════════════════════════════
async def proxy_rescraper(cfg, checker):
    interval = cfg.get("scrape_interval_minutes", 20) * 60
    while True:
        await asyncio.sleep(interval)
        if cfg.get("auto_scrape_proxies", True):
            await checker.console.log(Fore.CYAN, "PROXY", "Re-scraping & testing proxies...")
            scraper = ProxyScraper(cfg.get("proxy_sources", DEFAULT_CONFIG["proxy_sources"]))
            all_proxies = await scraper.scrape()
            if all_proxies:
                await scraper.save()
                pchecker = ProxyChecker(cfg)
                good = await pchecker.check_all(all_proxies)
                if good:
                    await pchecker.save_good()
                    checker.proxies = good
                    await checker.console.log(Fore.GREEN, "PROXY", f"Updated to {len(good)} fast proxies!")

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
async def main():
    console = Console()
    console.ui()

    cfg = load_config()
    updated = False
    for k, v in DEFAULT_CONFIG.items():
        if k not in cfg:
            cfg[k] = v
            updated = True
    if updated:
        save_config(cfg)

    # Load or scrape proxies
    good_proxies = []
    if os.path.exists(GOOD_PROXIES_PATH):
        good_proxies = await ProxyChecker(cfg).load_good()
        if good_proxies:
            print(f"{Fore.CYAN}[INFO]{Fore.RESET} Loaded {len(good_proxies)} previously tested good proxies.\n")

    if not good_proxies or cfg.get("auto_scrape_proxies", True):
        scraper = ProxyScraper(cfg.get("proxy_sources", DEFAULT_CONFIG["proxy_sources"]))
        all_proxies = await scraper.scrape()
        await scraper.save()

        if all_proxies:
            pchecker = ProxyChecker(cfg)
            good_proxies = await pchecker.check_all(all_proxies)
            if good_proxies:
                await pchecker.save_good()

    if not good_proxies:
        await console.log(Fore.LIGHTRED_EX, "ERR", "No working proxies found! Add good proxies to config/good_proxies.txt")
        input("Press Enter to exit...")
        sys.exit(1)

    await console.log(Fore.CYAN, "INFO", f"{len(good_proxies)} FAST proxies loaded...")
    await console.log(Fore.CYAN, "INFO", f"Batch Size: {cfg.get('batch_size', 1000)} | Timeout: {cfg.get('timeout', 3)}s")
    await console.log(Fore.CYAN, "INFO", f"API: discord.com/api/{cfg.get('api_version', 'v9')}/entitlements/gift-codes/<code>")
    await console.log(Fore.CYAN, "INFO", "Starting ULTRA SPEED workers...\n")

    checker = UltraChecker(cfg, good_proxies, console)
    start_time = time.time()

    # Run multiple batch workers
    workers = [asyncio.create_task(checker.run()) for _ in range(5)]
    stats_task = asyncio.create_task(stats_worker(checker, start_time))
    rescraper_task = asyncio.create_task(proxy_rescraper(cfg, checker))

    await asyncio.gather(*workers, stats_task, rescraper_task)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print(f"\n{Fore.LIGHTRED_EX}[STOP]{Fore.RESET} Interrupted by user.")
            break
        except Exception as e:
            print(f"\n{Fore.LIGHTRED_EX}[CRASH]{Fore.RESET} {e}")
            print(f"{Fore.CYAN}[INFO]{Fore.RESET} Restarting in 5 seconds...")
            time.sleep(5)
