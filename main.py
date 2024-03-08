import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QClipboard, QGuiApplication
import requests

class PubmedSearchApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Pubmed検索アプリ')
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
        pdf_file_path = event.mimeData().urls()[0].toLocalFile()
        self.textbox1.setText(f'ドロップされたPDFファイル: {pdf_file_path}')

        # PDFのファイル名を取得
        pdf_file_name = pdf_file_path.split("/")[-1]

        # Pubmedキーワード検索
        self.perform_pubmed_search(pdf_file_name)

    def search_from_input(self):
        search_term = self.textbox1.text()
        search_type = self.search_type_combo.currentText()
        self.perform_search(search_type, search_term)

    def search_from_clipboard(self):
        clipboard_text = QGuiApplication.clipboard().text()
        self.textbox1.setText(clipboard_text)
        search_type = self.search_type_combo.currentText()
        self.perform_search(search_type, clipboard_text)

    def perform_search(self, search_type, search_term):
        if search_term.isdigit() and len(search_term) == 8:
            # Pubmed ID検索
            search_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id={search_term}'
        else:
            # それ以外の検索
            if search_type == 'Pubmed検索':
                search_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&sort=relevance&retmode=json&term={search_term}'
            elif search_type == 'Crossref検索':
                # Crossref検索のURLを追加
                search_url = f'https://api.crossref.org/works?query={search_term}'
            elif search_type == 'arXiv検索':
                # arXiv検索のURLを追加
                search_url = f'http://export.arxiv.org/api/query?search_query={search_term}&start=0&max_results=1'
            else:
                return

        result_id_list = self.perform_search_request(search_url)

        # 検索結果から1つ目のIDを出力
        if result_id_list:
            self.textbox2.setText(f'{search_type}検索結果のIDリストの最初の値: {result_id_list[0]}')
            self.perform_pubmed_id_search(result_id_list[0])
        else:
            self.textbox2.setText('エラー: 文献が見つかりませんでした')

    def perform_search_request(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # Jsonオブジェクトから"idlist"の1つ目の値を取得
            id_list = data.get('esearchresult', {}).get('idlist', [])

            return id_list
        except Exception as e:
            print(f'検索エラー: {e}')
            return []

    def perform_pubmed_id_search(self, pubmed_id):
        try:
            # Pubmed ID検索のURLを構築
            search_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id={pubmed_id}'
            response = requests.get(search_url)
            response.raise_for_status()
            data = response.json()

            # Jsonオブジェクトから必要な情報を抽出
            result_data = data.get('result', {}).get(pubmed_id, {})
            authors = result_data.get('authors', [])
            source = result_data.get('source', '')
            pub_date = result_data.get('pubdate', '').split()[0]
            last_author = result_data.get('lastauthor', '').split()[0]
            title = result_data.get('title', '')

            
            # 著者名を要約
            author_names = [f"{author.get('name', '')}" for author in authors]
            first_author = author_names[0].split()[0]

            # 要約した情報をテキストボックスに表示
            summary_text = f'{first_author}, {last_author} ({source} {pub_date}) {title}'
            self.textbox2.setText(summary_text)

        except Exception as e:
            print(f'Pubmed ID検索エラー: {e}')
            self.textbox2.setText('エラー: 文献が見つかりませんでした')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PubmedSearchApp()
    window.show()
    sys.exit(app.exec_())
