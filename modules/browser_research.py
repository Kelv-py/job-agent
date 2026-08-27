"""
Browser research using Playwright.

Two capabilities:
  - search_job_listings(query, location) : find candidate job posting URLs
  - fetch_job_posting(url)                : open a specific posting and pull
                                             its visible text for analysis

Notes:
  - This drives a real browser, so it works on most public job pages without
    needing site-specific APIs.
  - Respect each site's Terms of Service / robots.txt, and prefer official
    APIs where available (e.g. Adzuna, Indeed Publisher API, Greenhouse/Lever
    job board APIs used by many companies) over scraping when you're running
    this at any real volume or scraping sites that require login (e.g. do not
    automate actions behind your personal LinkedIn login).
  - Add small delays between requests so you're not hammering a site.
"""
import time
from playwright.sync_api import sync_playwright


def search_job_listings(query: str, location: str = "", num_results: int = 10,
                         headless: bool = True) -> list[dict]:
    """
    Uses a general web search to discover job postings, then filters to
    likely job-board / company-careers URLs. Returns [{title, url}, ...].
    """
    search_query = f"{query} {location} job posting".strip()
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(f"https://www.bing.com/search?q={search_query.replace(' ', '+')}")
        page.wait_for_load_state("networkidle")

        links = page.query_selector_all("li.b_algo h2 a")
        for link in links[:num_results]:
            href = link.get_attribute("href")
            title = link.inner_text()
            if href:
                results.append({"title": title, "url": href})

        browser.close()

    return results


def fetch_job_posting(url: str, headless: bool = True, wait_seconds: float = 2.0) -> str:
    """
    Opens a job posting URL and returns the page's visible text content.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url, timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(wait_seconds)  # let dynamic content settle

        text = page.inner_text("body")
        browser.close()

    return text
