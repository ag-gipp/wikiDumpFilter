import re
from html import unescape
from urllib.request import Request, urlopen


def get_titles_and_lang_from_qid(qids, langs=None):
    """Converts list of QIDs to a dictionary mapping language to it's corresponding titles, for all specified languages.
    If no languages are specified, all languages available for a QID will be included.
    Titles returned will be unescaped (e.g. "&#039;" becomes "'").
    Only gets titles for languages named "enwiki", "dewiki",...; does not work for "enwikiquote", "enwikibooks",...!"""

    if langs is None:
        langs = []

    def get_html_code(qid):
        """returns html code from Wikidata"""

        def open_url(url):
            try:
                req = Request(url)
                http_response = urlopen(req)
                return http_response
            except Exception as e:
                print("Error with url: " + url)
                print(e)
                print()

        wikidata_url = 'https://www.wikidata.org/w/api.php?action=wbgetentities&format=xml&props=sitelinks&ids=' + qid

        http_response_object = open_url(wikidata_url)
        html_as_bytes = http_response_object.read()  # type: bytes
        html_str = html_as_bytes.decode("utf8")  # type: str

        return html_str

    lang_with_titles = {}
    for QID in qids:
        # search html code and look for titles
        html_code = get_html_code(QID)
        html_code = html_code.split("\n")
        for line in html_code:
            if "<sitelink site=" in line:
                wikis = re.findall('site=\"(.*?)\"', line)
                titles = re.findall('title=\"(.*?)\"', line)

                # exctract languages from wikis
                wiki_languages = []
                new_titles = []  # only includes titles from desired wikis
                for i, wiki in enumerate(wikis):
                    # only matches wikis named "enwiki", "dewiki",...; does not match "enwikiquote", "enwikibooks",...!
                    if wiki.endswith('wiki'):
                        wiki_languages.append(wiki[:-4])
                        new_titles.append(titles[i])
                titles = new_titles

                for lang, title in zip(wiki_languages, titles):
                    # languages == [] in case you want to get the titles of all languages
                    if (lang in langs) or langs == []:
                        if lang_with_titles.get(lang) is None:
                            lang_with_titles[lang] = []
                        unescaped_title = unescape(title)  # unescapes title, e.g. "&#039;" becomes "'"
                        lang_with_titles[lang].append(unescaped_title)

    return lang_with_titles
