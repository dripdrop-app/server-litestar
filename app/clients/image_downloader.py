import os
from urllib import parse

import httpx
from fake_useragent import UserAgent

SUPPORTED_IMAGE_EXTENSIONS = [".jpg", ".ico", "png", ".jpeg"]

user_agent = UserAgent()


def is_image_link(response: httpx.Response):
    if content_type := response.headers.get("Content-Type", None):
        if content_type.split("/")[0] == "image":
            return True
    return None


def is_valid_url(url: str):
    u = parse.urlparse(url)
    # Check if scheme(http or https) and netloc(domain) are not empty
    return u[0] != "" and u[1] != ""


def _get_images(response: httpx.Response) -> list:
    html = response.text
    links = set()
    for element in html.split('"'):
        for img in SUPPORTED_IMAGE_EXTENSIONS:
            if element.endswith(img):
                link = element.replace("\\", "")
                if not link.startswith("http"):
                    link = os.path.join(response.url, link)
                if is_valid_url(url=link):
                    links.add(link)
    return links


async def resolve_artwork(artwork: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(artwork, headers={"User-Agent": user_agent.firefox})
        if response.is_success:
            if is_image_link(response=response):
                return artwork
            img_links = _get_images(response=response)
            for img_link in img_links:
                if "artworks" in img_link and "500x500" in img_link:
                    return img_link
        raise Exception("Cannot resolve artwork")
