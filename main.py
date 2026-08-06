import os, requests, random, threading, json, time, sys, signal
from colorama import Fore, init

init(autoreset=True)

# ─── CONFIG ───
CONFIG_PATH = 'config/config.json'
PROXIES_PATH = 'config/proxies.txt'
RESULTS_PATH = 'results/hit.txt'

DEFAULT_CONFIG = {
    "thread": 50,
    "proxies": "http",
    "webhook": {
        "url": "https://discord.com/api/webhooks/1534684880288612513/lYtS-D0S3a2ifLLKuA9kFxHWcIMi8IDQuoBRLsP2UZP1PdZGrQnRKYi6GBu9DPvAikCf",
        "username": "l6j6",
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
    "check_timeout": 10,
    "delay_min": 0.5,
    "delay_max": 2.0,
    "use_random_ua": True,
    "promo_code_length": 24,
    "api_version": "v9",
    "max_retries": 3,
    "scrape_interval_minutes": 30,
    "restart_on_crash": True,
    "save_invalid": False
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

# ─── UTILS ───
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
    # Migrate old string-only sources to dict format
    sources = cfg.get("proxy_sources", [])
    new_sources = []
    for s in sources:
        if isinstance(s, str):
            # Detect type from URL
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

# ─── PROXY SCRAPER ───
class ProxyScraper:
    def __init__(self, sources):
        self.sources = sources
        self.proxies = []
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": random.choice(USER_AGENTS)})

    def _clean_proxy(self, line, default_type="http"):
        line = line.strip()
        if not line or line.startswith("#"):
            return None
        # If line already has protocol
        for prefix in ['http://', 'https://', 'socks4://', 'socks5://']:
            if line.lower().startswith(prefix):
                # Validate
                rest = line[len(prefix):]
                if ':' in rest:
                    parts = rest.rsplit(':', 1)
                    if len(parts) == 2 and parts[1].isdigit():
                        port = int(parts[1])
                        if 1 <= port <= 65535:
                            return line
                return None
        # No protocol - add default
        if ':' in line:
            parts = line.rsplit(':', 1)
            if len(parts) == 2 and parts[1].isdigit():
                port = int(parts[1])
                if 1 <= port <= 65535:
                    return f"{default_type}://{line}"
        return None

    def scrape(self):
        self.proxies = []
        print(f"{Fore.CYAN}[INFO]{Fore.RESET} Scraping proxies from {len(self.sources)} source(s)...\n")
        for src in self.sources:
            url = src.get("url", "") if isinstance(src, dict) else src
            ptype = src.get("type", "http") if isinstance(src, dict) else "http"
            try:
                r = self.session.get(url, timeout=20, headers={"User-Agent": random.choice(USER_AGENTS)})
                if r.status_code == 200:
                    lines = [self._clean_proxy(line, ptype) for line in r.text.splitlines()]
                    lines = [p for p in lines if p]
                    self.proxies.extend(lines)
                    print(f"{Fore.GREEN}[OK]{Fore.RESET}  {url[:55]}... -> {len(lines)} {ptype} proxies")
                else:
                    print(f"{Fore.RED}[FAIL]{Fore.RESET} {url[:55]}... -> HTTP {r.status_code}")
            except Exception as e:
                print(f"{Fore.RED}[ERR]{Fore.RESET}  {url[:55]}... -> {str(e)[:45]}")
        # Deduplicate
        self.proxies = list(dict.fromkeys(self.proxies))
        print(f"\n{Fore.CYAN}[INFO]{Fore.RESET} Total unique proxies scraped: {Fore.GREEN}{len(self.proxies)}{Fore.RESET}")
        return self.proxies

    def save(self, path=PROXIES_PATH):
        with open(path, 'w', encoding='utf-8') as f:
            for p in self.proxies:
                f.write(p + "\n")
        print(f"{Fore.CYAN}[INFO]{Fore.RESET} Saved {len(self.proxies)} proxies to {path}\n")

    def load(self, path=PROXIES_PATH):
        if not os.path.exists(path):
            return []
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and '://' in line]

# ─── CONSOLE ───
class Console:
    _lock = threading.Lock()

    def ui(self):
        os.system('cls && title [DNG] Discord Promo Generator ^| Auto-Proxy ^| 24/7' if os.name == "nt" else "clear")
        banner = center(f"""\n\n
██████╗ ███╗   ██╗ ██████╗ 
██╔══██╗████╗  ██║██╔════╝            ~ Discord Promo Generator ~
██║  ██║██╔██╗ ██║██║  ███╗     
██║  ██║██║╚██╗██║██║   ██║     Auto-Proxy ~ SOCKS/HTTP ~ 24/7
██████╔╝██║ ╚████║╚██████╔╝ 
╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ \n\n
              """)
        print(banner.replace('█', Fore.CYAN + "█" + Fore.RESET).replace('~', Fore.CYAN + "~" + Fore.RESET))

    def printer(self, color, status, code):
        with self._lock:
            print(f"{color} {status} > {Fore.RESET}promos.discord.gg/{code}")

    def log(self, color, tag, msg):
        with self._lock:
            print(f"{color}[{tag}]{Fore.RESET} {msg}")

    def proxies_count(self):
        if not os.path.exists(PROXIES_PATH):
            return 0
        with open(PROXIES_PATH, 'r', encoding='utf-8') as f:
            return sum(1 for line in f if line.strip() and '://' in line)

# ─── WORKER ───
class Worker:
    def __init__(self, config, proxies):
        self.config = config
        self.proxies = proxies
        self.console = Console()
        self.session = requests.Session()
        self._lock = threading.Lock()
        self.checked = 0
        self.valid = 0
        self.invalid = 0
        self.ratelimited = 0
        self.retries = 0
        self.errors = 0
        self.running = True

    def random_proxy(self):
        if not self.proxies:
            return None
        return random.choice(self.proxies)

    def get_headers(self):
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://discord.com",
            "Referer": "https://discord.com/",
            "X-Discord-Locale": "en-US",
            "X-Discord-Timezone": "America/New_York",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        if self.config.get("use_random_ua", True):
            headers["User-Agent"] = random.choice(USER_AGENTS)
        return headers

    def generate_code(self):
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        length = self.config.get("promo_code_length", 24)
        return "".join(random.choice(chars) for _ in range(length))

    def send_webhook(self, code, gift_data=None):
        url = self.config.get("webhook", {}).get("url", "")
        if not url:
            return

        embed = {
            "title": "🎉 New Valid Promo Code Found!",
            "description": f"**Code:** `promos.discord.gg/{code}`\n\n[Click to Redeem](https://promos.discord.gg/{code})",
            "color": 0x00ff00,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            "footer": {"text": "DNG Promo Generator"}
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
            "username": self.config.get("webhook", {}).get("username", "DNG Promo"),
            "avatar_url": self.config.get("webhook", {}).get("avatar", ""),
            "embeds": [embed]
        }
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            self.console.log(Fore.LIGHTBLACK_EX, "WH", f"Webhook failed: {e}")

    def check_code(self, code, attempt=1):
        proxy = self.random_proxy()
        proxies = None
        if proxy:
            proxies = {
                "http": proxy,
                "https": proxy
            }

        api_ver = self.config.get("api_version", "v9")
        url = f"https://discord.com/api/{api_ver}/entitlements/gift-codes/{code}?with_application=false&with_subscription_plan=true"

        try:
            r = self.session.get(
                url,
                headers=self.get_headers(),
                proxies=proxies,
                timeout=self.config.get("check_timeout", 10),
                allow_redirects=True
            )

            if r.status_code == 200:
                data = r.json()
                self.console.printer(Fore.LIGHTGREEN_EX, " VALID ", code)
                with self._lock:
                    self.valid += 1
                    self.checked += 1
                with open(RESULTS_PATH, 'a', encoding='utf-8') as f:
                    f.write(f"https://promos.discord.gg/{code}\n")
                self.send_webhook(code, data)
                return True

            elif r.status_code == 404:
                self.console.printer(Fore.LIGHTRED_EX, "Invalid", code)
                with self._lock:
                    self.invalid += 1
                    self.checked += 1
                return True

            elif r.status_code == 429:
                retry_after = 1
                try:
                    retry_after = int(r.json().get('retry_after', 1000)) / 1000 + 1
                except:
                    retry_after = random.uniform(2, 5)
                self.console.printer(Fore.LIGHTBLUE_EX, "RTlimit", code)
                with self._lock:
                    self.ratelimited += 1
                    self.checked += 1
                time.sleep(retry_after)
                return False

            elif r.status_code in [403, 401]:
                self.console.printer(Fore.LIGHTYELLOW_EX, " Block ", code)
                with self._lock:
                    self.checked += 1
                    self.errors += 1
                return False

            elif r.status_code == 400:
                self.console.printer(Fore.LIGHTYELLOW_EX, " BadFmt", code)
                with self._lock:
                    self.checked += 1
                return True

            else:
                self.console.printer(Fore.LIGHTYELLOW_EX, " Retry ", code)
                with self._lock:
                    self.retries += 1
                if attempt < self.config.get("max_retries", 3):
                    time.sleep(random.uniform(1, 3))
                    return self.check_code(code, attempt + 1)
                with self._lock:
                    self.checked += 1
                return True

        except requests.exceptions.ProxyError:
            if attempt < self.config.get("max_retries", 3):
                return self.check_code(code, attempt + 1)
            with self._lock:
                self.errors += 1
            return True

        except requests.exceptions.Timeout:
            if attempt < self.config.get("max_retries", 3):
                return self.check_code(code, attempt + 1)
            with self._lock:
                self.errors += 1
            return True

        except requests.exceptions.ConnectionError:
            if attempt < self.config.get("max_retries", 3):
                return self.check_code(code, attempt + 1)
            with self._lock:
                self.errors += 1
            return True

        except KeyboardInterrupt:
            raise

        except Exception:
            if attempt < self.config.get("max_retries", 3):
                return self.check_code(code, attempt + 1)
            with self._lock:
                self.errors += 1
            return True

    def run(self):
        while self.running:
            try:
                code = self.generate_code()
                self.check_code(code)
                time.sleep(random.uniform(
                    self.config.get("delay_min", 0.5),
                    self.config.get("delay_max", 2.0)
                ))
            except KeyboardInterrupt:
                self.running = False
                break

# ─── STATS PRINTER ───
def stats_worker(worker):
    while worker.running:
        time.sleep(15)
        if not worker.running:
            break
        worker.console.log(
            Fore.CYAN, "STATS",
            f"Checked: {worker.checked} | Valid: {Fore.GREEN}{worker.valid}{Fore.RESET} | "
            f"Invalid: {worker.invalid} | RateLimited: {worker.ratelimited} | "
            f"Errors: {worker.errors} | Threads: {threading.active_count()}"
        )

# ─── PROXY RE-SCRAPER ───
def proxy_rescraper(config, worker):
    interval = config.get("scrape_interval_minutes", 30) * 60
    while worker.running:
        time.sleep(interval)
        if not worker.running:
            break
        if config.get("auto_scrape_proxies", True):
            worker.console.log(Fore.CYAN, "PROXY", "Re-scraping proxies...")
            scraper = ProxyScraper(config.get("proxy_sources", DEFAULT_CONFIG["proxy_sources"]))
            new_proxies = scraper.scrape()
            if new_proxies:
                scraper.save()
                with worker._lock:
                    worker.proxies = new_proxies
                worker.console.log(Fore.GREEN, "PROXY", f"Updated to {len(new_proxies)} fresh proxies!")

# ─── MAIN ───
def main():
    console = Console()
    console.ui()

    cfg = load_config()
    # Ensure config has all keys
    updated = False
    for k, v in DEFAULT_CONFIG.items():
        if k not in cfg:
            cfg[k] = v
            updated = True
    if updated:
        save_config(cfg)

    # Scrape proxies if enabled
    if cfg.get("auto_scrape_proxies", True):
        scraper = ProxyScraper(cfg.get("proxy_sources", DEFAULT_CONFIG["proxy_sources"]))
        scraper.scrape()
        scraper.save()

    proxies = ProxyScraper([]).load()
    if not proxies:
        console.log(Fore.LIGHTRED_EX, "ERR", "No proxies found! Please add proxies to config/proxies.txt")
        input("Press Enter to exit...")
        sys.exit(1)

    console.log(Fore.CYAN, "INFO", f"{len(proxies)} Total proxies loaded...")
    console.log(Fore.CYAN, "INFO", f"Threads: {cfg.get('thread', 50)} | Delay: {cfg.get('delay_min', 0.5)}s-{cfg.get('delay_max', 2.0)}s")
    console.log(Fore.CYAN, "INFO", f"API: discord.com/api/{cfg.get('api_version', 'v9')}/entitlements/gift-codes/<code>")
    console.log(Fore.CYAN, "INFO", "Starting workers...\n")

    worker = Worker(cfg, proxies)

    # Start stats thread
    threading.Thread(target=stats_worker, args=(worker,), daemon=True).start()

    # Start proxy re-scraper thread
    threading.Thread(target=proxy_rescraper, args=(cfg, worker), daemon=True).start()

    # Start workers
    try:
        while worker.running:
            if threading.active_count() <= int(cfg.get("thread", 50)) + 3:
                t = threading.Thread(target=worker.run, daemon=True)
                t.start()
    except KeyboardInterrupt:
        worker.running = False
        console.ui()
        console.log(Fore.LIGHTRED_EX, "STOP", "Promo Gen Stopped by Keyboard Interrupt.")
        console.log(Fore.CYAN, "STATS", f"Final -> Checked: {worker.checked} | Valid: {worker.valid} | Invalid: {worker.invalid}")
        if os.name == "nt":
            os.system('pause >nul')
        else:
            input("Press Enter to exit...")

if __name__ == "__main__":
    # Auto-restart on crash if enabled
    cfg = load_config()
    if cfg.get("restart_on_crash", True):
        while True:
            try:
                main()
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"{Fore.LIGHTRED_EX}[CRASH]{Fore.RESET} {e}")
                print(f"{Fore.CYAN}[INFO]{Fore.RESET} Restarting in 5 seconds...")
                time.sleep(5)
    else:
        main()
