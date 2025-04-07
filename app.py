import os #OSに依存する機能を使用するため。
from flask import Flask, render_template, request, session, redirect, url_for
from datetime import datetime  #日付と時間を扱う
from flask_session import Session #セッション管理

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

app.secret_key = 'your_secret_key'

texts = [] #text格納用

@app.route('/set_session_folder_name', methods=['GET'])
def set_session_folder_name():
    # 現在の日時をフォルダー名として使用
    session['folder_name'] = datetime.now().strftime('%Y%m%d_%H%M%S')
    return 'Session folder name set'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form['text']
        texts.append(text)
    session_folder_name = session.get('folder_name', '')  # セッションからfolder_nameを取得
    return render_template('index.html', texts=texts, session_folder_name=session_folder_name)

@app.route('/new_session', methods=['GET'])
def new_session():
    session.clear()  # セッションをクリアする
    return redirect(url_for('index'))

@app.route('/record', methods=['POST'])
def record():
    if 'recordings' not in session:
        session['recordings'] = []

    audio_data = request.files['audio_data']
    
    is_replay = request.form.get('is_replay') == 'true'  # 文字列の'true'と比較
    
    word = get_next_word()  # text.txtから次の単語を取得する
    if word is None:
        return 'All words from text.txt have been used', 400

    session_folder = get_or_create_session_folder()
    
    # プレイ再生の場合、ファイル名の先頭に"rep_"を追加
    filename = 'rep_' + word if is_replay else word
    audio_path = os.path.join('static', 'recordings', session_folder, f'{filename}.wav')
    audio_data.save(audio_path)

    audio_path = os.path.join('static', 'recordings', session_folder, '{}.wav'.format(word))
    audio_data.save(audio_path)

    # 保存した録音ファイルをセッション内のrecordingsリストに追加
    session['recordings'].append(audio_path)

    return 'success'

def get_next_word():
    if 'recordings' not in session:
        session['recordings'] = []

    with open('static/texts/texts.txt', 'r', encoding='utf-8') as f:
        words = [word.strip() for word in f.readlines()]

    # セッションから録音されたファイルの数を取得し、次の単語を取得
    current_index = len(session['recordings'])
    if current_index < len(words):
        return words[current_index]
    else:
        return None

def get_or_create_session_folder():
    if 'folder_name' not in session:
        # 現在の日時をフォルダー名として使用
        session['folder_name'] = datetime.now().strftime('%Y%m%d_%H%M%S')

    folder_name = session['folder_name']
    folder_path = os.path.join('static', 'recordings', folder_name)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
    return folder_name


UPLOAD_FOLDER = '/var/www/html/pythonProject/pythonProject/mixvoice/static/recordings/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400

    file = request.files['file']

    if file.filename == '':
        return 'No selected file', 400

    # セッションフォルダを取得または作成
    session_folder = get_or_create_session_folder()
    session_folder_path = os.path.join(UPLOAD_FOLDER, session_folder)

    if not os.path.exists(session_folder_path):
        os.makedirs(session_folder_path)

    file.save(os.path.join(session_folder_path, file.filename))

    return 'File uploaded successfully'


if __name__ == '__main__':
    os.makedirs('static/recordings', exist_ok=True)  # recordingsフォルダを作成
    app.run(debug=True, port=5001)

