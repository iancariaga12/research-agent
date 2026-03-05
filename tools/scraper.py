import requests
from bs4 import BeautifulSoup

def scrape_page(url: str) -> str:
    """Scrape the text content of a webpage."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove junk elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        
        return text[:1500]

    except Exception as e:
        return f"Error scraping {url}: {str(e)}"
