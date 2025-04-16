from urllib.parse import parse_qs, urlparse


def parse_youtube_video_id(url: str):
    parsed_url = urlparse(url)
    search_params = parse_qs(parsed_url.query)
    video_ids = search_params.get("v")
    return video_ids[0] if video_ids else None
