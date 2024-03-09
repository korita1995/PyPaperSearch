import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QClipboard, QGuiApplication
import requests
import re
from bs4 import BeautifulSoup
import feedparser

class LiteratureSearchApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('文献検索アプリ')
        self.setGeometry(100, 100, 500, 300)

        layout = QVBoxLayout()

        # プルダウンリスト
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItem('Pubmed検索')
        self.search_type_combo.addItem('Crossref検索')
        self.search_type_combo.addItem('arXiv検索')
        self.search_type_combo.addItem('GoogleScholar検索')

        # テキストボックス1
        self.textbox1 = QLineEdit()
        self.textbox1.setPlaceholderText('入力欄')
        self.textbox1.setFixedHeight(3 * self.textbox1.fontMetrics().lineSpacing())  # 3行分の縦幅

        # 検索ボタン
        search_button_layout = QHBoxLayout()
        self.search_input_button = QPushButton('入力欄から検索')
        self.search_clipboard_button = QPushButton('クリップボードから検索')
        search_button_layout.addWidget(self.search_input_button)
        search_button_layout.addWidget(self.search_clipboard_button)

        # テキストボックス2
        self.textbox2 = QTextEdit()
        self.textbox2.setPlaceholderText('検索結果がここに表示されます')
        self.textbox2.setFixedHeight(3 * self.textbox2.fontMetrics().lineSpacing())  # 3行分の縦幅

        layout.addWidget(self.search_type_combo)
        layout.addWidget(self.textbox1)
        layout.addLayout(search_button_layout)
        layout.addWidget(self.textbox2)

        self.setLayout(layout)

        self.setAcceptDrops(True)

        # シグナル・スロットの接続
        self.search_input_button.clicked.connect(self.search_from_input)
        self.search_clipboard_button.clicked.connect(self.search_from_clipboard)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() and event.mimeData().urls()[0].toString().endsWith('.pdf'):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.textbox1.setText(f'ドロップされたファイル: {file_path}')

        # ファイル名を取得
        file_name = file_path.split("/")[-1]

        # キーワード検索を行う
        self.perform_search(file_name)

    def search_from_input(self):
        search_term = self.textbox1.text()
        search_type = self.search_type_combo.currentText()
        self.perform_search(search_term, search_type)

    def search_from_clipboard(self):
        clipboard_text = QGuiApplication.clipboard().text()
        self.textbox1.setText(clipboard_text)
        search_type = self.search_type_combo.currentText()
        self.perform_search(clipboard_text, search_type)

    def perform_search(self, search_term, search_type):
        if search_type == 'Pubmed検索':
            self.pubmed_search(search_term)
        elif search_type == 'Crossref検索':
            self.crossref_search(search_term)
        elif search_type == 'arXiv検索':
            self.arxiv_search(search_term)
        elif search_type == 'GoogleScholar検索':
            self.googlescholar_search(search_term)

    def pubmed_search(self, search_term):
        # Pubmed IDかどうかの判定
        #if search_term.isdigit() and len(search_term) == 8:
        if re.match(r'^\d{8}$', search_term):
            search_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id={search_term}'
            print("Pubmed ID検索実行")
        else:
            search_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&sort=relevance&retmode=json&term={search_term}'
            self.textbox2.setText("Pubmedキーワード検索実行")

        result_data = self.perform_search_request(search_url)

        if result_data:
            self.show_pubmed_summary(result_data)
        else:
            self.textbox2.setText('エラー: 文献が見つかりませんでした')

    def crossref_search(self, search_term):
        # DOIかどうかの判定
        if 'https://doi.org/' in search_term:
            doi = search_term.replace('https://doi.org/', '')
            search_url = f'https://api.crossref.org/works/{doi}'
        elif 'doi:' in search_term:
            doi = search_term.replace('doi:', '').lstrip()
            search_url = f'https://api.crossref.org/works/{doi}'
        elif 'DOI:' in search_term:
            doi = search_term.replace('DOI:', '').lstrip()
            search_url = f'https://api.crossref.org/works/{doi}'
        else:
            search_url = f'https://api.crossref.org/works?sort=relevance&query={search_term}'

        result_data = self.perform_search_request(search_url)

        if result_data:
            self.show_crossref_summary(result_data)
        else:
            self.textbox2.setText('エラー: 文献が見つかりませんでした')

    def arxiv_search(self, search_term):
        # arXiv IDかどうかの判定
        if 'arXiv:' in search_term:
            arxiv_id = search_term.replace('arXiv:', '')
            search_url = f'http://export.arxiv.org/api/query?&sortBy=relevance&sortOrder=ascending&max_results=10&id_list={arxiv_id}'
        else:
            search_url = f'http://export.arxiv.org/api/query?&sortBy=relevance&sortOrder=ascending&max_results=10&search_query={search_term}'
            search_url = search_url.replace(" ", "%20")
            search_url = search_url.replace("-", "%20")

        result_data = feedparser.parse(search_url)

        if result_data:
            self.show_arxiv_summary(result_data)
        else:
            self.textbox2.setText('エラー: 文献が見つかりませんでした')

    def googlescholar_search(self, search_term):
        search_url = f'https://scholar.google.co.jp/scholar?hl=ja&as_sdt=0%2C5&num=10&q={search_term}'
        result_data = requests.get(search_url).text

        if result_data:
            self.show_googlescholar_summary(result_data)
        else:
            self.textbox2.setText('エラー: 文献が見つかりませんでした')

    def remove_matching_string(self, A, B):
        # 文字列Aと文字列Bを比較し、BからAと一致する文字列を削除する
        result = B
        for char in A:
            result = result.replace(char, '', 1)  # 1回だけ削除する
        return result

    def perform_search_request(self, search_url):
        try:
            response = requests.get(search_url)
            response.raise_for_status()
            result_data = response.json()
            return result_data
        except Exception as e:
            print(f'検索エラー: {e}')
            return None

    def show_pubmed_summary(self, result_data):
        try:
            # Pubmedキーワード検索の場合
            if 'esearchresult' in result_data:
                result_data = result_data['esearchresult']
                id_list = result_data.get('idlist', [])

                if not id_list:
                    self.textbox2.setText('エラー: 文献が見つかりませんでした')
                    return

                # Pubmed ID検索を行う
                pubmed_id = id_list[0]
                pubmed_id_search_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id={pubmed_id}'
                pubmed_id_result = self.perform_search_request(pubmed_id_search_url)

            # Pubmed ID検索の場合
            else:
                pubmed_id = result_data["result"]["uids"][0]
                pubmed_id_result = result_data

            pub_date, source, authors, last_author, title = (
                pubmed_id_result['result'][pubmed_id].get('pubdate', '').split()[0],
                pubmed_id_result['result'][pubmed_id].get('source', ''),
                pubmed_id_result['result'][pubmed_id].get('authors', []),
                pubmed_id_result['result'][pubmed_id].get('lastauthor', '').split()[0],
                pubmed_id_result['result'][pubmed_id].get('title', ''),
                )

            # 著者名を要約
            author_names = [f"{author.get('name', '')}" for author in authors]
            first_author = author_names[0].split()[0]

            # 要約した情報をテキストボックスに表示
            summary_text = f'{first_author} {last_author} ({source} {pub_date}) {title}'
            summary_text = self.remove_special_characters(summary_text)
            self.textbox2.setText(summary_text)

        except Exception as e:
            print(f'Pubmed検索エラー: {e}')
            self.textbox2.setText('エラー: 文献が見つかりませんでした')

    def show_crossref_summary(self, result_data):
        try:
            # Crossrefキーワード検索の場合
            print("Crossrefキーワード検索")
            if 'message' in result_data and result_data['message'].get('items'):
                items = result_data['message']['items']
                # journal-articleの最初の結果を検索
                item = next(
                    (i for i in items if i.get("type") == 'journal-article'),
                    None
                )

                # DOIを使って検索
                if 'DOI' in item:
                    print(item["DOI"])
                    doi_search_url = f'https://api.crossref.org/works/{item["DOI"]}'
                    doi_result = self.perform_search_request(doi_search_url)

            # Crossref　DOI検索の場合
            else:
                doi_result = result_data

            title = doi_result['message'].get('title', '')[0]
            author_names = [f"{author.get('family', '')}" for author in doi_result['message'].get('author', [])]
            first_author = author_names[0]
            last_author = author_names[-1]
            pub_date = doi_result['message'].get('created', {}).get('date-parts', [])[0][0] if doi_result['message'].get('created') else ''
            source = doi_result['message'].get('short-container-title', [''])[0]

            # 要約した情報をテキストボックスに表示
            summary_text = f'{first_author} {last_author} ({source} {pub_date}) {title}'
            summary_text = self.remove_special_characters(summary_text)
            print(summary_text)
            self.textbox2.setText(summary_text)
            QGuiApplication.clipboard().setText(summary_text)

        except Exception as e:
            print(f'Crossref検索エラー: {e}')
            self.textbox2.setText('エラー: 文献が見つかりませんでした')

    def show_arxiv_summary(self, result_data):
        try:
            entries = result_data['entries']
            entry = entries[0]

            authors = entry.authors
            if len(authors) == 1:
                author_summary = authors[0]["name"].split(" ")[1]
            else:
                first_author = authors[0]["name"].split(" ")[1]
                last_author = authors[-1]["name"].split(" ")[1]
                author_summary = f"{first_author} {last_author}"

            title  = entry.title.replace('\n ', '')
            date   = entry.published_parsed
            year = date[0]
            journal = "arXiv"

            summary_text = f"{author_summary} ({journal} {year}) {title}"
            summary_text = self.remove_special_characters(summary_text)
            self.textbox2.setText(summary_text)
            QGuiApplication.clipboard().setText(summary_text)

        except Exception as e:
            print(f'arXiv検索エラー: {e}')
            self.textbox2.setText('エラー: 文献が見つかりませんでした')

    def show_googlescholar_summary(self, result_data):
        try:
            # 参照：https://qiita.com/kuto/items/9730037c282da45c1d2b
            soup = BeautifulSoup(result_data, "html.parser") # BeautifulSoupの初期化
            tags1 = soup.find_all("h3", {"class": "gs_rt"}) # title
            title = tags1[0].text.replace("[HTML]","").lstrip()

            tags2 = soup.find_all("div", {"class": "gs_fmaa"})  # writer
            authors = tags2[0].text
            if len(authors.split(","))==1:
                author_summary = authors.split(" ")[1]
            else:
                first_author = authors.split(",")[0].lstrip().split(" ")[1]
                last_author = authors.split(",")[-1].lstrip().split(" ")[1]
                author_summary = f"{first_author} {last_author}"

            tags3 = soup.find_all("div", {"class": "gs_a gs_fma_p"})  # writer&year
            author_year = tags3[0].text
            A = authors
            B = author_year
            dif = self.remove_matching_string(A, B)
            journal_title = dif.split(",")[0]
            year = re.sub(r'\D', '', author_year)

            # 要約した情報をテキストボックスに表示
            summary_text = f"{author_summary} ({journal_title} {year}) {title}"
            summary_text = self.remove_special_characters(summary_text)
            self.textbox2.setText(summary_text)
            QGuiApplication.clipboard().setText(summary_text)

        except Exception as e:
            print(f'GoogleScholar検索エラー: {e}')
            self.textbox2.setText('エラー: 文献が見つかりませんでした')

    def remove_special_characters(self, input_string):
        # 参照：https://x.gd/f0fcI
        pattern = r'[\\|/|:|?|.|"|<|>|\|]'
        result = re.sub(pattern, '', input_string)
        return result


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LiteratureSearchApp()
    window.show()
    sys.exit(app.exec_())
