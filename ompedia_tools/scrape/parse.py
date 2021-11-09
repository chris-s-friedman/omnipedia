"""
Parsers

Functions related to parsing things out of bs4 objects from omnipedia.
"""
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from ompedia_tools.utils.common import is_date, to_bool
from ompedia_tools.utils.logging import get_logger

logger = get_logger(__name__, testing_mode=False)


def parse_infobox(soup):
    """
    Parse a wiki page's infobox

    :param soup: beutiful soup object to parse
    :type soup: bs4.BeautifulSoup
    :return: dict containing information from the infobox. Minimally has a
    `name` (containing the name of the infobox) and an `infobox_table` - a dict
    where each key/value is a key/value in the infobox. May also contain `media`
    which is information about the media inside the infobox
    :rtype: dict
    """
    logger.debug("Parsing infobox")
    infobox = soup.find("div", {"class": "omnipedia-infobox"})
    if infobox is None:
        logger.warning("No infobox found")
        return None
    infobox_dict = {}
    infobox_dict["name"] = infobox.find(
        "strong", {"class": "omnipedia-infobox__name"}
    ).get_text()
    infobox_dict["infobox_table"] = {}
    for dt in infobox.find_all("dt"):
        title_text = dt.get_text()
        if title_text == "Media":
            media_dd = infobox.find("dt").find_next("dd")
            val = {
                "text": media_dd.get_text(" ", strip=True),
                "src": media_dd.find("a").find("img").get("src"),
                "alt_text": media_dd.find("a").find("img").get("alt"),
            }
            infobox_dict[title_text] = val
        else:
            val = dt.find_next("dd").get_text(" ", strip=True)
            infobox_dict["infobox_table"][title_text] = val
    return infobox_dict


def parse_toc(soup):
    """
    Parse a page's Table of Contents

    :param soup: beautiful soup object to parse
    :type soup: bs4.BeautifulSoup
    :return: dict where each keys are the text of the toc list item and the
    value is the link to the section.
    :rtype: dict
    """
    logger.debug("Parsing Table of Contents")
    toc = soup.find("div", {"class": "table-of-contents"})
    toc_dict = {}
    for link in toc.find_all("a"):
        toc_dict[link.get_text()] = link.get("href")
    return toc_dict


def url_type(url):
    parsed_url = urlparse(url)
    if parsed_url.path == "":
        return "main_page"
    else:
        return urlparse(url).path[1:-1].partition("/")[0]


def parse_link(soup_link):
    """
    Parse a single link from a page

    :param soup_link: beautiful soup object with information from a link. e.g.
    `soup.find("a")`
    :type soup_link: bs4.BeautifulSoup
    :return: A dict of information about the link.
    :rtype: dict
    """
    logger.debug("Parsing Link")
    is_wikimedia_link = to_bool(soup_link.get("data-is-wikimedia-link"))
    if is_wikimedia_link:
        wikimedia_data = {
            "is_wikimedia_link": is_wikimedia_link,
            "title": soup_link.get("data-omnipedia-attached-data-title"),
            "content": soup_link.get("data-original-title"),
            "content_formatted": soup_link.get(
                "data-omnipedia-attached-data-content"
            ),
        }
    else:
        wikimedia_data = None

    def link_type(link_dict):
        if is_wikimedia_link:
            return "wikimedia_link"
        if isinstance(link_dict["url"], str):
            if link_dict["url"].startswith("#backreference"):
                return "backreference"
            elif link_dict["url"].startswith("#"):
                return "page_nav"
            elif (
                link_dict["url"]
                in [
                    "/user/login",
                    "/privacy",
                    "/support",
                    "/privacy",
                    "https://creativecommons.org/licenses/by-nc/4.0/",
                    "/join",
                ]
                or "Main_Page" in link_dict["url"]
            ):
                return "site_nav"
        if isinstance(link_dict["link_text"], str):
            if (
                link_dict["link_text"]
                in [
                    "About Omnipedia",
                    "View changes",
                    "Random article",
                    "Log in",
                    "Privacy policy",
                    "Close",
                    "Support",
                    "Privacy policy",
                    "Copyright",
                    "Join Omnipedia",
                ]
                or is_date(link_dict["link_text"])
            ):
                return "site_nav"
            elif link_dict["link_text"] == "Main page":
                return "main_page"
        if hasattr(link_dict["class"], "__iter__"):
            if "ambientimpact-is-image-link" in link_dict["class"]:
                return "image"
        if link_dict["link_text"] == "" and link_dict["url"] is None:
            return "None"
        else:
            return "wiki_page_link"

    link_dict = {
        "link_text": soup_link.get_text(" ", strip=True),
        "url": soup_link.get("href"),
        "class": soup_link.get("class"),
        "wikimedia_data": wikimedia_data,
    }
    # if hasattr(link_dict["class"], "__iter__"):
    #     if "references__backreference-link" in link_dict["class"]:
    #         breakpoint()
    link_dict["type"] = link_type(link_dict)
    return link_dict


def parse_main_page(client, url):
    page = client.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    parsed_url = urlparse(url)

    def parse_news_item(li):
        return {
            "text": li.get_text(),
            "links": [parse_link(link) for link in li.find_all("a")],
        }

    return {
        "url": url,
        "url_scheme": parsed_url.scheme,
        "url_host": parsed_url.netloc,
        "url_path": parsed_url.path,
        "page_title": soup.find("title").get_text(),
        "page_date": soup.find("time", {"class": "omnipedia-current-date"}).get(
            "datetime"
        ),
        "featured_article": {
            "text": soup.find(
                "div",
                {"class": "omnipedia-main-page__featured-article-content"},
            ).get_text(),
            "link": parse_link(
                soup.find(
                    "a", {"class": "omnipedia-main-page__featured-article-link"}
                )
            ),
        },
        "news": {
            "items": [
                parse_news_item(item)
                for item in soup.find(
                    "div",
                    {
                        "class": "omnipedia-main-page__content omnipedia-main-page__news-content"  # noqa
                    },
                ).find_all("li")
            ]
        },
        "links": [parse_link(link) for link in soup.find_all("a")],
    }


def parse_wiki_page(client, url):
    """
    Parse a wiki page

    :param client: client to use to connect to site with.
    :type client: requests.sessions.Session
    :param url: URL of the wiki page.
    :type url: str
    :return: Information extracted from the wiki page. This is:
    - Information about the page
    - Information from the infobox
    - Information from the table of contents
    - List of links found in the page
    :rtype: dict
    """
    logger.info(f"Parsing {url}")
    page = client.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    parsed_url = urlparse(url)
    return {
        "url": url,
        "url_scheme": parsed_url.scheme,
        "url_host": parsed_url.netloc,
        "url_path": parsed_url.path,
        "page_title": soup.find("title").get_text(),
        "page_date": soup.find("time", {"class": "omnipedia-current-date"}).get(
            "datetime"
        ),
        "entry_title": soup.find(
            "span",
            {
                "class": "field field--name-title field--type-string field--label-hidden"  # noqa
            },
        ).get_text(),
        # extract info from the infobox
        "infobox_dict": parse_infobox(soup),
        "toc": parse_toc(soup),
        "links": [parse_link(link) for link in soup.find_all("a")],
    }
