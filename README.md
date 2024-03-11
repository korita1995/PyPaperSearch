# PyPaperSearch
## Python開発環境(Rye)
rye init PyPaperSearch<br>
cd PyPaperSearch
rye pin 3.10.13<br>
rye add requests PyQt5 feedparser python-Levenshtein pyinstaller<br>
rye sync<br>
.\\.venv\Scripts\activate<br>

## 実行ファイルの作成方法（exeファイルなど）
pyinstaller main.py --onefile --noconsole --icon=app.ico
