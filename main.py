import csv
import os
import re
import requests

import html2text
from bs4 import BeautifulSoup

"""
Creates a list with all Crunchyroll anime titles and genres, 
which are obtained from MyAnimeList.net by using the unofficial 
api Jikan
"""

LANGUAGES = {
    'english_us': '',
    'english_uk': 'en-gb',
    'spanish': 'es',
    'spanish_es': 'es-es',
    'portuguese_br': 'pt-br',
    'portuguese_pt': 'pt-pt',
    'french': 'fr',
    'german': 'de',
    'arabic': 'ar',
    'italian': 'it',
    'russian': 'ru'
}

SITE = 'https://www.crunchyroll.com'
LANGUAGE = 'portuguese_br'
LANG = LANGUAGES[LANGUAGE]
CSV_FILE = 'anime_list_' + LANGUAGE + '.csv'

MYANIMELIST_BASE = 'https://myanimelist.net/'

class CRListRequest:
    def __init__(self):
        page_url = urljoin(SITE, LANG + '/videos/anime/alpha?group=all')
        r = requests.get(page_url)
        self.status = r.status_code
        if self.status != 200:
            raise Exception(str(r.status_code) + 'Error')
        self.content = r.content


class CRList:
    def __init__(self, page):
        soup = BeautifulSoup(page, 'html.parser')
        raw = soup.find('div', class_='videos-column-container')
        self.raw_items = raw.find_all('li')
        self.items_md = [_html_to_markdown(i.a, baseurl=SITE) for i in self.raw_items]
        self.items = [_md_to_tuple(i) for i in self.items_md]


class MyAnimeListScraper:
    URL_TYPES = {
        'search': '/anime.php?q=',
        'anime': 'anime/'
    }

    def __init__(self):
        self.status = None
        self.content = None

    def _get(self, url):
        r = requests.get(url)
        self.status = r.status_code
        if self.status != 200:
            raise Exception(str(r.status_code) + 'Error')
        self.content = r.content

    def get_url(self, url_type, value):
        url = MYANIMELIST_BASE + self.URL_TYPES[url_type] + value
        self._get(url)


    def search(self, anime_title):
        self.get_url('search', anime_title)
        soup = BeautifulSoup(self.content, 'html.parser')
        link = soup.find('a', {'class': 'hoverinfo_trigger'})
        # TODO: Finish this scraper


    def find(self, anime_title):
        self.get_url('search', anime_title)
        search_soup = BeautifulSoup(self.content, 'html.parser')
        link = search_soup.find('a', {'class': 'hoverinfo_trigger'})
        mal_url = link['href']
        self._get(mal_url)
        anime_page_soup = BeautifulSoup(self.content, 'html.parser')
        sidebar = anime_page_soup.find('td', {'class': 'borderClass'})
        sidebar_div = sidebar.find('div')
        for span in sidebar_div.findAll('span', {'itemprop':'genre'}): 
            span.decompose()
        markdown_info = _html_to_markdown(sidebar_div, ignore_links=True)
        markdown_info_list = [i.strip() for i in markdown_info.split('\n\n')]

        anime_info = {'MyAnimeList URL': mal_url}
        for info in markdown_info_list:
            pair = info.split(': ', 1)
            if len(pair) == 2:
                key, value = pair
                anime_info[key] = value
        return anime_info

    def anime(self, anime_id):
        self.get_url('anime', anime_id)
        soup = BeautifulSoup(self.content, 'html.parser')
        # TODO: Finish this scraper

def _html_to_markdown(value, baseurl=None, ignore_links=False):
    h = html2text.HTML2Text()
    h.ignore_links = ignore_links
    h.baseurl = baseurl
    h.body_width = 0
    return h.handle(str(value))

def _md_to_tuple(a):
    b = re.split('\]\(', a, 1)
    b = re.split('\s\"', b[1], 1)
    c, d = b

    search_friendly_name = d.split('/')[-1].replace('-', ' ')
    return d[0:-3], c, search_friendly_name

async def main(client):
    task_list = [] 
    for anime in cr_list:
        task_list.append(loop.create_task(fetch_anime(client, anime)))
    
    await asyncio.wait(task_list)
    await client.close()


if __name__ == "__main__":
    filePath = CSV_FILE
    if os.path.exists(filePath):
        os.remove(filePath)

    try:
        page = CRListRequest()
    except Exception as e:
        print(e)

    cr_list = CRList(page.content).items
    
    for anime in cr_list:
        try:
            mal_scraper = MyAnimeListScraper()
            anime_found = mal_scraper.find(anime[2])
            entry = (anime[0], anime[1], anime_found['English'], anime_found['MyAnimeList URL'], anime_found['Japanese'], anime_found['Genres'])
            print(entry)
            with open(CSV_FILE, 'a', encoding='utf-8', newline='') as output:
                csv_out = csv.writer(output, delimiter=';')
                csv_out.writerow(entry)
            
        except Exception as e:
            print(e)
