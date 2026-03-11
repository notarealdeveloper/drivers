#!/usr/bin/env python

__all__ = ['web']

import os
import bs4
import shutil
import requests
from pathlib import Path
from urllib.parse import urlparse


class web:
    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/35.0.1916.47 Safari/537.36"
    )

    def __init__(self, type="chrome", headless=False, incognito=True, as_self=True, user_agent=USER_AGENT):

        self.type = type

        if type == "chrome":
            from selenium.webdriver.chrome.service import Service as Service
            from selenium.webdriver.chrome.options import Options as Options
            from selenium.webdriver import Chrome as Driver

            driver_path = shutil.which("chromedriver")
            if not driver_path:
                raise RuntimeError(
                    "chromedriver not found on PATH. Install chromedriver via your package manager "
                    "or add it to PATH."
                )

            from pathlib import Path
            home = Path.home()
            chrome_profile = home / ".config/google-chrome"

            self.options = Options()
            # New headless mode on modern Chrome
            if headless:
                self.options.add_argument("--headless=new")
            if incognito:
                self.options.add_argument("--incognito")
            self.options.add_argument("--start-maximized")
            self.options.add_argument(f"--user-agent={user_agent}")

            if as_self:
                # This is ALMOST RIGHT but every website hates you.
                # Need to figure out how to lie better.
                # To be continued.
                self.options.add_argument(f"--user-data-dir={chrome_profile}")
                self.options.add_argument(f"--profile-directory=Default")

            self.service = Service(executable_path=driver_path)
            self.driver = Driver(service=self.service, options=self.options)

        elif type == "firefox":
            from selenium.webdriver.firefox.service import Service as Service
            from selenium.webdriver.firefox.options import Options as Options
            from selenium.webdriver import Firefox as Driver

            driver_path = shutil.which("geckodriver")
            if not driver_path:
                raise RuntimeError(
                    "geckodriver not found on PATH. Install geckodriver via your package manager "
                    "or add it to PATH."
                )

            self.options = Options()
            if headless:
                self.options.add_argument("--headless")
            if incognito:
                # Firefox: private browsing is a preference, not a CLI flag.
                self.options.set_preference("browser.privatebrowsing.autostart", True)

            # Firefox UA override (works, but some sites ignore it)
            if user_agent:
                self.options.set_preference("general.useragent.override", user_agent)

            self.service = Service(executable_path=driver_path)
            self.driver = Driver(service=self.service, options=self.options)

        else:
            raise ValueError(f"Unsupported browser type: {type}")

    def __getattr__(self, attr):
        return getattr(self.driver, attr)

    def __dir__(self):
        return super().__dir__() + self.driver.__dir__()

    def page(self):
        return self.driver.page_source

    def soup(self):
        return bs4.BeautifulSoup(self.driver.page_source, "html.parser")

    def get(self, url):
        self.driver.get(url)
        return self

    def run(self, script):
        return self.driver.execute_script(script)

    def querySelectorAll(self, selector):
        return self.run(f"""
        return Array.from(document.querySelectorAll("{selector}"));
        """)

    def get_jpgs(self):
        return self.run("""
        return Array.from(document.querySelectorAll('img[src$="jpg"]')).map(img => img.src);
        """)

    def get_pngs(self):
        return self.run("""
        return Array.from(document.querySelectorAll('img[src$="png"]')).map(img => img.src);
        """)

    def get_gifs(self):
        return self.run("""
        return Array.from(document.querySelectorAll('img[src$="gif"]')).map(img => img.src);
        """)

    def get_images(self):
        return self.run("""
        return Array.from(document.querySelectorAll("img")).map(img => img.src);
        """)

    def get_images_full(self):
        return self.run("""
        let a2imgs = Array.from(document.querySelectorAll("a > img"));
        return a2imgs.map(img => img.parentNode.href);
        """)

    def url_to_path(self, url=None):
        if url is None:
            url = self.driver.current_url
        u = urlparse(url)
        return os.path.join(u.netloc, u.path.lstrip("/"))

    def download_images(self, **kwds):
        urls = self.get_images()
        return self.download_urls(urls, **kwds)

    def download_urls(self, urls=(), url=None, outdir="browser", max_workers=8):
        if url is not None:
            self.get(url)

        from concurrent.futures import ThreadPoolExecutor, as_completed

        dirname = os.path.join(outdir, self.url_to_path())
        os.makedirs(dirname, exist_ok=True)

        results = {"succeeded": [], "failed": []}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for u in urls:
                basename = os.path.basename(urlparse(u).path) or "download"
                pathname = os.path.join(dirname, basename)
                fut = executor.submit(self.download_url, u, pathname)
                fut.url = u
                futures.append(fut)

            for fut in as_completed(futures):
                try:
                    fut.result()  # IMPORTANT: surface exceptions
                    results["succeeded"].append(fut.url)
                except Exception:
                    results["failed"].append(fut.url)

        return results

    def download_url(self, url, pathname):
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with open(pathname, "wb") as fp:
            fp.write(r.content)
        relpath = Path(pathname).relative_to(os.getcwd())
        print(f"Downloaded url: {url!r} to {str(relpath)!r}")

