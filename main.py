import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QClipboard, QGuiApplication
import requests
import re

class SearchApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('文献検索アプリ')
        self.setGeometry(100, 100, 500, 300)

        layout = QVBoxLayout()

        self.search_type_combo = QComboBox()
        self.search_type_combo.addItem('Pubmed検索')
        self.search_type_combo.addItem('Crossref検索')
        self.search_type_combo.addItem('arXiv検索')

        self.textbox1 = QLineEdit()
        self.textbox1.setPlaceholderText('入力欄')
        self.textbox1.textChanged.connect(self.update_placeholder)

        self.search_button = QPushButton('入力欄から検索')
        self.search_button.clicked.connect(self.search_from_input)

        self.clipboard_button = QPushButton('クリップボードから検索')
        self.clipboard_button.clicked.connect(self.search_from_clipboard)

        self.textbox2 = QLineEdit()
        self.textbox2.setPlaceholderText('検索結果がここに表示されます。')
        self.textbox2.setReadOnly(True)

        layout.addWidget(self.search_type_combo)
        layout.addWidget(self.textbox1)
        layout.addWidget(self.search_button)
        layout.addWidget(self.clipboard_button)
        layout.addWidget(self.textbox2)

        self.setLayout(layout)

        self.setAcceptDrops(True)

    def update_placeholder(self):
        # テキストボックスが空の場合はデフォルトのプレースホルダーを表示
        if not self.textbox1.text():
            self.textbox1.setPlaceholderText('入力欄')

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
            # Pubmed検索のURLを追加
            search_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&sort=relevance&retmode=json&term={search_term}'

            result_data = self.perform_search_request(search_url)

            # 結果がある場合は要約して表示
            if result_data:
                self.show_pubmed_summary(result_data)
            else:
                self.textbox2.setText('エラー: 文献が見つかりませんでした')

        elif search_type == 'Crossref検索':
            # Crossref検索のURLを追加
            search_url = f'https://api.crossref.org/works?sort=relevance&query={search_term}'

            result_data = self.perform_search_request(search_url)

            # 結果がある場合は要約して表示
            if result_data:
                self.show_crossref_summary(result_data)
            else:
                self.textbox2.setText('エラー: 文献が見つかりませんでした')

        elif search_type == 'arXiv検索':
            # arXiv検索のURLを追加
            search_url = f'http://export.arxiv.org/api/query?search_query={search_term}&start=0&max_results=1'

            result_data = self.perform_search_request(search_url)

            # 結果がある場合は要約して表示
            if result_data:
                self.show_arxiv_summary(result_data)
            else:
                self.textbox2.setText('エラー: 文献が見つかりませんでした')

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
            if 'esearchresult' in result_data:
                # Pubmedキーワード検索の結果から必要な情報を抽出
                result_data = result_data['esearchresult']
                id_list = result_data.get('idlist', [])

                if not id_list:
                    self.textbox2.setText('エラー: 文献が見つかりませんでした')
                    return

                # Pubmed ID検索を行う
                pubmed_id = id_list[0]
                pubmed_id_search_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id={pubmed_id}'
                pubmed_id_result = self.perform_search_request(pubmed_id_search_url)

                if pubmed_id_result:
                    # Pubmed ID検索の結果から必要な情報を抽出
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
                    summary_text = f'{first_author}, {last_author} ({source} {pub_date}) {title}'
                    self.textbox2.setText(summary_text)

        except Exception as e:
            print(f'Pubmed ID検索エラー: {e}')
            self.textbox2.setText('エラー: 文献が見つかりませんでした')

    def show_crossref_summary(self, result_data):
        try:
            if 'message' in result_data and result_data['message'].get('items'):
                # Crossref検索の結果から必要な情報を抽出
                items = result_data['message']['items']
                item = items[0]

                # DOI検索の場合はDOIを使って検索
                if 'DOI' in item:
                    doi_search_url = f'https://api.crossref.org/works/{item["DOI"]}'
                    doi_result = self.perform_search_request(doi_search_url)

                    if doi_result:
                        title = doi_result['message'].get('title', '')[0]
                        author_names = [f"{author.get('family', '')}" for author in
                                        doi_result['message'].get('author', [])]
                        first_author = author_names[0]
                        last_author = author_names[-1]
                        pub_date = doi_result['message'].get('created', {}).get('date-parts', [])[0][0] if doi_result[
                            'message'].get('created') else ''
                        source = doi_result['message'].get('container-title', [''])[0]

                        # 要約した情報をテキストボックスに表示
                        summary_text = f'{first_author} {last_author} ({source} {pub_date}) {title}'
                        self.textbox2.setText(summary_text)
                    else:
                        self.textbox2.setText('エラー: 文献が見つかりませんでした')

                else:
                    title = item.get('title', '')[0]
                    author_names = [f"{author.get('given', '')} {author.get('family', '')}" for author in
                                    item.get('author', [])]
                    pub_date = item.get('created', {}).get('date-parts', [])[0][0] if item.get('created') else ''
                    source = item.get('container-title', [''])[0]

                    # 要約した情報をテキストボックスに表示
                    summary_text = f'{", ".join(author_names)} ({source} {pub_date}) {title}'
                    self.textbox2.setText(summary_text)

            else:
                self.textbox2.setText('エラー: 文献が見つかりませんでした')

        except Exception as e:
            print(f'Crossref検索エラー: {e}')
            self.textbox2.setText('エラー: 文献が見つかりませんでした')

    def show_arxiv_summary(self, result_data):
        try:
            if 'feed' in result_data and 'entry' in result_data['feed'] and result_data['feed']['entry']:
                # arXiv検索の結果から必要な情報を抽出
                entry = result_data['feed']['entry'][0]
                title = entry.get('title', '')
                author_names = [author['name'] for author in entry.get('author', [])]
                pub_date = entry.get('published', '')
                source = entry.get('arxiv_primary_category', {}).get('term', '')

                # 要約した情報をテキストボックスに表示
                summary_text = f'{", ".join(author_names)} ({source} {pub_date}) {title}'
                self.textbox2.setText(summary_text)

            else:
                self.textbox2.setText('エラー: 文献が見つかりませんでした')

        except Exception as e:
            print(f'arXiv検索エラー: {e}')
            self.textbox2.setText('エラー: 文献が見つかりませんでした')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SearchApp()
    window.show()
    sys.exit(app.exec_())
