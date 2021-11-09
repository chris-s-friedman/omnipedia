import time

from ompedia_tools.scrape.parse import (
    parse_main_page,
    parse_wiki_page,
    url_type,
)
from ompedia_tools.utils.logging import get_logger

logger = get_logger(__name__, testing_mode=False)


def parse_wiki(client, url):
    """
    recursively parse omnipedia from a seed url

    :param client: client to use to connect to site with.
    :type client: requests.sessions.Session
    :param url: URL of the seed wiki page to start parsing.
    :type url: str
    :return: list of information scraped from each page, where each list item
    is information scraped from the page
    :rtype: list
    """
    urls = []
    res = []

    def wiki_parser(client, url):
        if url not in urls:
            if len(urls) > 0:
                logger.debug("Waiting a moment to parse the next page")
                time.sleep(1)
            if url_type(url) == "main_page":
                page_data = parse_main_page(client, url)
            elif url_type(url) == "wiki":
                page_data = parse_wiki_page(client, url)
            else:
                logger.info("page type not recognized:")
                logger.info(url)
            urls.append(url)
            res.append(page_data)
            links = [
                page_data["url_scheme"]
                + "://"
                + page_data["url_host"]
                + link["url"]
                for link in page_data["links"]
                if link["type"] == "wiki_page_link"
            ]
            for link in links:
                wiki_parser(client, link)

    wiki_parser(client, url)
    return res
