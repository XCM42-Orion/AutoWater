import html
import json

from ..login import *

class InfoBotNewsWrapper:
    def __init__(self, infosession):
        self.infosession = infosession

        self.news_list = None

    def get_news_list(self, page):
        if not self.infosession.logged_in:
            self.infosession.login()

        
        def get_news_list_(csrf_token, page):
            url = NEWS_LIST_URL + f'&lmid=all&currentPage={page}&length=20&_csrf=' + csrf_token
            news_list_response = self.infosession.session.get(url)
            return news_list_response.text

        csrf_token = self.infosession.get_csrf_token()

        return json.loads(get_news_list_(csrf_token, page))["object"]["dataList"]
    
    def get_news_details(self, url):
        policy = [
["jwcbg", ["td.TD4", "td[colspan='4']:not([height])"]],
["kybg", ["tr.style1", "table[width='95%'][cellpadding='3'] tr:nth-of-type(1)"]],
["gjc", ["td.style11", "td[width='85%']"]],
["77726476706e69737468656265737421f2fa598421322653770bc7b88b5c2d32530b094045c3bd5cabf3", 
    ["td.TD1", "td[colspan='4']:not([height])"]],
["77726476706e69737468656265737421e0f852882e3e6e5f301c9aa596522b2043f84ba24ebecaf8", 
    ["div.cont_doc_box h5 span", "div.field-item"]],
["77726476706e69737468656265737421e9fd528569336153301c9aa596522b20735d12f268e561f0", 
    ["h3", "div[style*='text-align:left'][style*='width:90%']"]],
["77726476706e69737468656265737421f8e60f8834396657761d88e29d51367b523e", 
    ["h1", "div.r_cont > ul"]],
["77726476706e69737468656265737421e8ef439b69336153301c9aa596522b20e1a870705b76e399", 
    ["td.TD1", "td.td4"]],
["rscbg", ["tr[height='40']", "table[width='95%'] > tbody > tr:nth-of-type(3)"]],
["77726476706e69737468656265737421e7e056d234297b437c0bc7b88b5c2d32112b31e4d37621d4714d6", 
    ["", "[style*='text-align:left']"]],
["ghxt", ["", "td[valign='top']:not([class])"]],
["fgc", ["div.title_b", 
        "div[style*='width:647px'][style*='margin-left:6px'][style*='font-size:13px'][style*='line-height:20px'][style*='text-align:justify']"]],
["77726476706e69737468656265737421e8e442d23323615e79009cadd6502720f9b87b", 
    ["div.bt", "div.xqbox"]],
["77726476706e69737468656265737421e4ff459d207e6b597d469dbf915b243de94c4812e5c2e1599f", 
    ["td.TD_right > font", "td[colspan='4']:not([height])"]],
["jdbsc", ["td.TD1", "table[width='95%']:nth-of-type(2) > tr:nth-of-type(1)"]],
["xsglxt", ["div.sideleft p:first-child", "div.sideleft"]],
["77726476706e69737468656265737421fdee49932a3526446d0187ab9040227bca90a6e14cc9", 
    ["", "div.box3 table"]],
["77726476706e69737468656265737421fcfe43d23323615e79009cadd6502720703f47", 
    ["h2", "div.concon"]],
["77726476706e69737468656265737421f3f65399222226446d0187ab9040227b8e4026c4ffd2", 
    ["h1", "div.WordSection1"]]
]







        html = self.infosession.session.get(url).text

        csrf = self.infosession.get_csrf_token()

        xxid = re.search(r'var xxid = "(.*?)";', html)

        if not xxid:
            redirect_url = self.infosession.get_redirect_url(url)
            if "_playFile" in html:
                file_id_pos = redirect_url.find("fileId=")
                file_id = redirect_url[file_id_pos + 7:]
                #完啦，是pdf

                pdf = self.infosession.session.get(PDF_NEWS_PREFIX + file_id + '?_csrf' + csrf)

                return pdf.text
            else:
                if redirect_url.endswith('.pdf'):
                    return html
                    
                else:
                    selected_policy = ''
                    content_text = ''
                    for i, each in enumerate(policy):
                        if each[0] in html:
                            selected_policy = each[1]


                            soup = BeautifulSoup(html, 'html.parser')
                            title_element = soup.select_one(selected_policy[0])
                            content_element = soup.select_one(selected_policy[1])
                            if content_element:
                                content_text += content_element.get_text(strip=True)

                    return content_text
                    
        else:
            response = self.infosession.session.get(f'{NEWS_DETAIL_URL}?xxid={xxid.group(1)}&preview=&_csrf={csrf}')

            details = json.loads(response.text)

            return details
        
    def on_get_news_list(self, page):
        news_list = self.get_news_list(page)

        ret = {
            "list_of_news": list()
        }

        for index, each in enumerate(news_list):
            ret["list_of_news"].append({'index':index,
                                        'title':html.unescape(each["bt"].strip())})
        self.news_list = news_list

        return ret
    
    def on_get_news_details(self, index):
        details = self.get_news_details(NEWS_REDIRECT_URL + self.news_list[index]["url"])

        if isinstance(details,dict):

            raw_title = details['object']['xxDto']['bt']
            raw_content = details['object']['xxDto']['nr']
            
            title = html.unescape(raw_title)
            content = html.unescape(raw_content)

            soup_title = BeautifulSoup(title, 'html.parser')
            soup_content = BeautifulSoup(content, 'html.parser')

            title = soup_title.get_text()
            content = soup_content.get_text()

            content = f"标题:{title}\n正文:{content}"

        else:
            title = ''
            content = str(details)

        return {
            "body": content
        }

    
