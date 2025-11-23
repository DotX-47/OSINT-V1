
# ---------------------------------------------------------
#  User-Search - Made By DotX-47
#  Animated rainbow banner + username enumeration (OSINT).
# ---------------------------------------------------------

import os
import sys
import time
import threading
import concurrent.futures
from typing import List

import requests
from bs4 import BeautifulSoup
import pyfiglet
from colorama import Fore, init

# ---------------------------------------------------------
#  Basic Configuration
# ---------------------------------------------------------
init(autoreset=True)

BANNER_TEXT = "User-Search - Made By DotX-47"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/58.0.3029.110 Safari/537.36"
)
REQUEST_TIMEOUT = 8
MAX_WORKERS = 30
RESULTS_DIR = "Doxed"

# Color shortcuts
COLORS = [
    Fore.RED,
    Fore.YELLOW,
    Fore.GREEN,
    Fore.CYAN,
    Fore.BLUE,
    Fore.MAGENTA,
]
RED = Fore.RED
GREEN = Fore.GREEN
RESET = Fore.RESET

print_lock = threading.Lock()

# ---------------------------------------------------------
#  Animated Rainbow Banner
# ---------------------------------------------------------
def _clear_terminal():
    """Clear the terminal screen in a cross-platform way."""
    if os.name == "nt":
        os.system("cls")
    else:
        # Use ANSI clear for speed/compatibility
        sys.stdout.write("\033c")
        sys.stdout.flush()


def _colorize_line_shifted(line: str, shift: int) -> str:
    """Return a single line where each character is colored by shifting through COLORS."""
    out = []
    color_count = len(COLORS)
    for i, ch in enumerate(line):
        # preserve whitespace but still advance the color index for aesthetic continuity
        color = COLORS[(i + shift) % color_count]
        out.append(f"{color}{ch}")
    out.append(RESET)
    return "".join(out)


def animate_banner(text: str, frames: int = 24, delay: float = 0.06):
    """Animate the ASCII banner for a brief rainbow wave."""
    ascii_art = pyfiglet.figlet_format(text)
    lines = ascii_art.splitlines()

    try:
        for frame in range(frames):
            _clear_terminal()
            shift = frame  # moving color index
            for line in lines:
                print(_colorize_line_shifted(line, shift))
            # small subtitle in the center-ish area
            subtitle = "Made By DotX-47"
            print()  # blank line
            # color subtitle with a rotated color pattern
            print("".join(COLORS[(i + shift) % len(COLORS)] + ch for i, ch in enumerate(subtitle)) + RESET)
            time.sleep(delay)
    except KeyboardInterrupt:
        # If the user interrupts, just stop animating and proceed gracefully
        pass

    # Print final, non-animated banner (settled state)
    _clear_terminal()
    final_shift = frames % len(COLORS)
    ascii_art = pyfiglet.figlet_format(text)
    for line in ascii_art.splitlines():
        print(_colorize_line_shifted(line, final_shift))
    print()
    subtitle = "Made By DotX-47"
    print("".join(COLORS[(i + final_shift) % len(COLORS)] + ch for i, ch in enumerate(subtitle)) + RESET)
    print("\n")  # space before menu


# Run the animation once at startup
animate_banner(BANNER_TEXT, frames=30, delay=0.055)


# ---------------------------------------------------------
#  Helper Functions (unchanged core functionality)
# ---------------------------------------------------------
def make_session() -> requests.Session:
    """Return a configured requests session."""
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def google_dork_search(query: str) -> List[str]:
    """Perform a basic Google dork search (simple HTML scrape)."""
    url = f"https://www.google.com/search?q={query}"
    session = make_session()

    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except Exception as e:
        print(f"{RED}[!] Error during Google request: {e}{RESET}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    # Note: Google's HTML changes often; this is a best-effort selector.
    for div in soup.find_all("div", class_="BVG0Nb"):
        link = div.find("a")
        if link and "href" in link.attrs:
            results.append(link["href"])

    return results


def check_username(target: str, url: str, session: requests.Session) -> bool:
    """Return True if the username text appears on the page (basic substring check)."""
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200 and target in resp.text:
            return True
        return False
    except Exception as e:
        with print_lock:
            print(f"{RED}[!] Error checking {url}: {e}{RESET}")
        return False


def username_lookup(target: str):
    """Check a curated list of platforms for the username; save positive hits."""
    platforms = [
        f"https://www.youtube.com/@{target}",
        f"https://www.tiktok.com/@{target}",
        f"https://www.instagram.com/{target}/",
        f"https://www.facebook.com/{target}/",
        f"https://x.com/{target}",
        f"https://www.reddit.com/user/{target}",
        f"https://www.github.com/{target}",
        f"https://gitlab.com/{target}",
        f"https://soundcloud.com/{target}",
        f"https://pastebin.com/u/{target}",
        f"https://linktr.ee/{target}",
        f"https://steamcommunity.com/id/{target}",
        f"https://keybase.io/{target}",
        f"https://about.me/{target}",
        f"https://www.tumblr.com/{target}",
        f"https://www.behance.net/{target}",
        f"https://dribbble.com/{target}",
        f"https://www.deviantart.com/{target}",
        f"https://t.me/{target}",
        f"https://vk.com/{target}",
        f"https://ok.ru/{target}",
        f"https://www.pinterest.com/{target}/",
        f"https://www.twitch.tv/{target}",
        f"https://www.linkedin.com/in/{target}",
        f"https://www.quora.com/profile/{target}",
    ]

    session = make_session()
    found = []

    print(f"\n[+] Looking up username: {target}\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {
            executor.submit(check_username, target, url, session): url for url in platforms
        }

        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                exists = future.result()
            except Exception:
                exists = False

            with print_lock:
                if exists:
                    print(f"{GREEN}[+] Found: {url}{RESET}")
                    found.append(url)
                else:
                    print(f"{RED}[-] Not found: {url}{RESET}")

    if found:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        file_path = os.path.join(RESULTS_DIR, f"{target}.txt")
        try:
            with open(file_path, "w", encoding="utf-8") as fh:
                for line in found:
                    fh.write(line + "\n")
            print(f"\n{GREEN}[?] Results saved to: {file_path}{RESET}\n")
        except Exception as e:
            print(f"{RED}[!] Failed to save results: {e}{RESET}")
    else:
        print(f"\n{RED}[!] No profiles found for {target}.{RESET}\n")


# ---------------------------------------------------------
#  Main Menu
# ---------------------------------------------------------
def main():
    while True:
        print("[ MENU ]")
        print("1. Google Dork Search")
        print("2. Username Lookup")
        print("3. Exit")

        choice = input("\nSelect an option (1/2/3): ").strip()

        if choice == "1":
            query = input("\nEnter Google dork query: ").strip()
            results = google_dork_search(query)
            if results:
                print(f"\n{GREEN}[+] Google Dork Results:{RESET}")
                for r in results:
                    print(r)
            else:
                print(f"{RED}[!] No results found.{RESET}")

        elif choice == "2":
            username = input("\nEnter the username to check: ").strip()
            username_lookup(username)

        elif choice == "3":
            print("\nGoodbye.")
            break

        else:
            print(f"{RED}[!] Invalid choice. Try again.{RESET}")


if __name__ == "__main__":
    main()

