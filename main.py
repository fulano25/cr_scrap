import asyncio
import csv
import os
import re
import requests
import aiohttp
from urllib.parse import urljoin

import html2text
from bs4 import BeautifulSoup
from jikanpy import AioJikan
import time


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

class CRListRequest:
    def __init__(self):
        page_url = urljoin(SITE, LANG + '/videos/anime/alpha?group=all')
        r = requests.get(page_url)
        self.code = r.status_code
        if self.code != 200:
            raise Exception(str(r.status_code) + 'Error')
        self.content = r.content


class CRList:
    def __init__(self, page):
        soup = BeautifulSoup(page, 'html.parser')
        raw = soup.find('div', class_='videos-column-container')
        self.raw_items = raw.find_all('li')
        self.items_md = [_html_to_markdown(i.a, baseurl=SITE) for i in self.raw_items]
        self.items = [_md_to_tuple(i) for i in self.items_md]


def _html_to_markdown(value, baseurl=None, ignore_links=False):
    h = html2text.HTML2Text()
    h.ignore_links = ignore_links
    h.baseurl = baseurl
    h.body_width = 0
    return h.handle(str(value))

def _md_to_tuple(a):
    """
    Gambiarra pra transformar os links em markdown que são gerados nesse
    projeto em um tuple contendo a mensagem que aparece quando aponta o
    mouse e o link respectivamente
    """
    b = re.split('\]\(', a, 1)
    b = re.split('\s\"', b[1], 1)
    c, d = b
    return d[0:-3], c

async def fetch_anime_(anime, client):
    cr_title, cr_url = anime
    search_result = await client.search(search_type='anime', query=cr_title)
    search_result_id = search_result['results'][0]['mal_id']
    mal_anime = await client.anime(search_result_id)
    # print(mal_anime)
    mal_title = mal_anime['title']
    mal_url = mal_anime['url']
    mal_genres = [genre['name'] for genre in mal_anime['genres']]
    entry = (cr_title, cr_url, mal_title, mal_url, mal_genres)
    with open(CSV_FILE, 'a', encoding='utf-8', newline='') as output:
        csv_out = csv.writer(output, delimiter=';')
        csv_out.writerow(entry)
    print(entry[0])

async def fetch_anime(client, anime):
    cr_title, cr_url = anime
    search_result = None
    try:
        search_result = await client.search(search_type='anime', query=cr_title)
        search_result_id = search_result['results'][0]['mal_id']
        mal_anime = await client.anime(search_result_id)
        mal_title = mal_anime['title']
        mal_url = mal_anime['url']
        mal_genres = [genre['name'] for genre in mal_anime['genres']]
        entry = (cr_title, cr_url, mal_title, mal_url, mal_genres)
        print(entry)
        with open(CSV_FILE, 'a', encoding='utf-8', newline='') as output:
            csv_out = csv.writer(output, delimiter=';')
            csv_out.writerow(entry)
    except Exception as e:
        entry = (cr_title, e)
        print(entry)
        with open(CSV_FILE, 'a', encoding='utf-8', newline='') as output:
            csv_out = csv.writer(output, delimiter=';')
            csv_out.writerow(entry)

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
    print(cr_list)

    loop = asyncio.get_event_loop()

    connector = aiohttp.TCPConnector(limit=1)
    session = aiohttp.ClientSession(loop=loop, connector=connector)
    aio_jikan = AioJikan(session=session)

    try:
        loop.run_until_complete(main(aio_jikan))
    except Exception as e:
        print(e)
    loop.close()


