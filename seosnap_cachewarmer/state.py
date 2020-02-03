import os
from typing import Dict, Union, Iterable
from urllib.parse import urlparse

from seosnap_cachewarmer.service import SeosnapService


class SeosnapState:
    website: dict
    website_id: int
    follow_next: bool
    recache: bool
    use_queue: bool

    cacheserver_url: str
    service: SeosnapService
    extract_fields: Dict[str, str]

    def __init__(self, website_id, follow_next=True, recache=True, use_queue=False) -> None:
        self.service = SeosnapService()
        self.website_id = website_id
        self.use_queue = parse_bool(use_queue)
        self.follow_next = parse_bool(follow_next) and not self.use_queue
        self.recache = parse_bool(recache)

        self.cacheserver_url = os.getenv('CACHEWARMER_CACHE_SERVER_URL').rstrip('/')
        self.website = self.service.get_website(self.website_id)
        self.extract_fields = {field['name']: field["css_selector"] for field in self.website["extract_fields"]}

    def get_name(self) -> str:
        return f'Cachewarm: {self.website["name"]}'

    def sitemap_urls(self) -> Iterable[str]:
        if not self.use_queue:
            yield self.website["sitemap"]

    def extra_pages(self) -> Iterable[str]:
        if not self.use_queue:
            yield self.website["domain"]
        else:
            for url in self.get_queue(): yield url

    def get_queue(self) -> Iterable[str]:
        # Retrieve queue items while queue is not empty
        uri = urlparse(self.website['domain'])
        root_domain = f'{uri.scheme}://{uri.netloc}'
        while True:
            items = self.service.get_queue(self.website_id)
            # Empty queue
            if len(items) == 0: break

            for item in items:
                path = item['page']['address']
                yield f'{root_domain}{path}'


def parse_bool(s: Union[str, bool]) -> bool:
    if isinstance(s, bool): return s
    return s not in ['false', '0']
