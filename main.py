import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from constants import BASE_DIR, MAIN_DOC_URL
from configs import configure_argument_parser
from outputs import control_output

# Hello, world

def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = session.get(whats_new_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')
    li = soup.find_all('li', class_="toctree-l1")

    main_div = soup.find('section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = main_div.find('div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all('li', attrs={'class': 'toctree-l1'})
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    for section in tqdm(sections_by_python):
        version_a_tag = section.find('a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = session.get(version_link) # Загрузите все страницы со статьями. Используйте кеширующую сессию.      
        response.encoding = 'utf-8'  # Укажите кодировку utf-8.
        soup = BeautifulSoup(response.text, 'lxml')  # Сварите "супчик".
        h1 = soup.find('h1')  # Найдите в "супе" тег h1.
        dl = soup.find('dl')  # Найдите в "супе" тег dl.
        dl_text = dl.text.replace('\n', ' ')
        results.append((version_link, h1.text, dl_text)) # Добавьте в вывод на печать текст из тегов h1 и dl.
    # for result in results:
    #     print(*result)
    return results


def latest_versions(session):
    response = session.get(MAIN_DOC_URL)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')
    sidebar = soup.find('div', class_='sphinxsidebarwrapper')
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Ничего не нашлось')
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        try:
            version, status = re.search(pattern, a_tag.text).groups()
        except:
            version = a_tag.text
            status = ''
        results.append((link, version, status))
                
    # for row in results:
    #     print(*row) 
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = session.get(downloads_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')
    table = soup.find('table', class_='docutils')
    pdf_a4_tag = table.find('a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url)

    with open(archive_path, 'wb') as file:
        file.write(response.content)

MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
}


def main():    
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    session = requests_cache.CachedSession()
    
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    # Сохраняем результат вызова функции в переменную results. 
    results = MODE_TO_FUNCTION[parser_mode](session)
    
    # Если из функции вернулись какие-то результаты,
    if results is not None:
        # передаём их в функцию вывода вместе с аргументами командной строки.
        control_output(results, args)

if __name__ == '__main__':
    main() 
