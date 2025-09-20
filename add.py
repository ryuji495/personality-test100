import streamlit as st
import os
import json
import base64
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- スプレッドシート設定（必要に応じて変更） ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SPREADSHEET_NAME = "personality_test"  # ← あなたのスプレッドシート名に変更

# --- 質問ツリー（あなたの元の内容） ---
question_tree = {
    "start": {"text": "あなたはよく外出をするほうですか？", "yes": "q1", "no": "q2"},
    "q1": {"text": "コミュ力があると思う？", "yes": "q3", "no": "q4"},
    "q2": {"text": "思考力があるほうだと思う？", "yes": "q4", "no": "q5"},
    "q3": {"text": "仲間が失敗しても許してあげる?", "yes": "q6", "no": "q7"},
    "q4": {"text": "自分は聞き上手だと思う？", "yes": "q8", "no": "q9"},
    "q5": {"text": "自分には特別な力があると思う", "yes": "j", "no": "i"},
    "q6": {"text": "自分より他人のことを優先する", "yes": "a", "no": "b"},
    "q7": {"text": "失敗してしまったら落ち込むよりもイライラする", "yes": "c", "no": "d"},
    "q8": {"text": "一人よりも大人数のほうがいい", "yes": "e", "no": "f"},
    "q9": {"text": "感情的になりやすいと思う？", "yes": "g", "no": "h"},
    "a": "🌟 あなたは **ポジティブタイプ** です！/自分の人生に起きるどんな出来事でもプラスに解釈し、困難な状況に遭遇しても積極的に前進できる人",
    "b": "🌸 あなたは **優しいタイプ** です！/相手の立場を思いやり、共感する能力が高く、聞き上手で、否定的な言葉を避ける、そして自然体で穏やかな雰囲気を持っている人",
    "c": "🌧 あなたは **ネガティブタイプ** です！/常に最低の事態を想定しており、いざ何か起こったときにも、立ち直りや対策を練ることができる人",
    "d": "🔥 あなたは **怒りっぽいタイプ** です！/感情表現がストレートで人間関係を築きやすい、大切なものを守ろうとする強い意志や真剣さを持つ、不満を前向きなエネルギーに変えて行動できる人",
    "e": "❄️ あなたは**クールタイプ** です！/感情を表に出さず冷静、周りに流されずに自分のポリシーを持っている、ミステリアスな雰囲気の人",
    "f": "🌙 あなたは **おとなしいタイプ** です！/穏やかで物静か、一人の時間を大切にする、周りの状況を冷静に観察する視点を持つ人",
    "g": "🎭 あなたは **感情豊かなタイプ** です！/共感力が高く、繊細で、感情表現が豊か、芸術に感動したり、日常生活に喜びを見出したりと、様々なものに深く心を動かされる人",
    "h": "💪 あなたは **熱血タイプ** です！/エネルギッシュで情熱的、周りを鼓舞して人を巻き込む力がある人",
    "i": "🌼 あなたは **天然タイプ** です！/素直で裏表のない感情表現、独特な発想や感性、おっちょこちょいな一面、そして他人の評価を気にしないマイペースな人",
    "j": "🌀 あなたは **変人タイプ** です！/強いこだわりを持つ、特定の話題に没頭する、周囲と比べて独特な価値観や行動、考え方を持つ少し変わった人。もしかしたら✮**天才**✮かも"
}

def show_image_for_question(key):
    image_path = f"images/{key}.jpg"
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)

# --- Google Sheets helper ---
def get_gspread_client():
    """
    環境変数 SERVICE_ACCOUNT_JSON（JSON文字列 or base64）を優先読み取り。
    なければローカルの service_account.json を使う。
    """
    env = os.environ.get("SERVICE_ACCOUNT_JSON")
    if env:
        # try plain json
        try:
            info = json.loads(env)
        except Exception:
            # try base64
            try:
                decoded = base64.b64decode(env).decode("utf-8")
                info = json.loads(decoded)
            except Exception as e:
                raise RuntimeError("SERVICE_ACCOUNT_JSON の読み込みに失敗しました: " + str(e))
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        return gspread.authorize(creds)

    # local file fallback
    keyfile = "service_account.json"
    if os.path.exists(keyfile):
        creds = Credentials.from_service_account_file(keyfile, scopes=SCOPES)
        return gspread.authorize(creds)

    raise RuntimeError("認証情報が見つかりません。service_account.json を置くか環境変数 SERVICE_ACCOUNT_JSON を設定してください。")

def get_service_account_email():
    """ユーザーがスプレッドシートに共有するための service account のメールアドレスを取得（存在すれば）"""
    env = os.environ.get("SERVICE_ACCOUNT_JSON")
    if env:
        try:
            info = json.loads(env)
        except Exception:
            info = json.loads(base64.b64decode(env).decode("utf-8"))
        return info.get("client_email")
    keyfile = "service_account.json"
    if os.path.exists(keyfile):
        with open(keyfile, "r", encoding="utf-8") as f:
            info = json.load(f)
        return info.get("client_email")
    return None

def send_to_google_sheets(nickname, password, result_text):
    client = get_gspread_client()
    sheet = client.open(SPREADSHEET_NAME).sheet1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, nickname, password, result_text], value_input_option="USER_ENTERED")

# --- 初期化 ---
if "nickname" not in st.session_state:
    st.session_state.nickname = None
if "password" not in st.session_state:
    st.session_state.password = None
if "current_key" not in st.session_state:
    st.session_state.current_key = "start"
if "sent_to_sheet" not in st.session_state:
    st.session_state.sent_to_sheet = False

st.markdown("<h1 style='text-align: center;'>🧠 性格診断テスト</h1>", unsafe_allow_html=True)
st.markdown("---")

# 小さなヘルプ（サービスアカウントのメールがわかれば表示）
sa_email = get_service_account_email()
if sa_email:
    st.caption(f"※ スプレッドシートはサービスアカウント `{sa_email}` に編集権限を与えてください（共有設定）。")
else:
    st.caption("※ スプレッドシート連携は service_account.json または SERVICE_ACCOUNT_JSON 環境変数 が必要です。")

# ニックネーム + パスワード入力フェーズ
if st.session_state.nickname is None or st.session_state.password is None:
    st.markdown(
        "<p style='color:red; font-weight:bold;'>入力したニックネームは今後シューティングゲームをプレイする際に使用するので、保存やメモなど忘れないようにしてください。</p>",
        unsafe_allow_html=True
    )
    nickname = st.text_input("ニックネームを入力してください 👇")
    password = st.text_input("パスワードを入力してください 👇", type="password")
    if st.button("診断を始める") and nickname.strip() and password.strip():
        st.session_state.nickname = nickname.strip()
        st.session_state.password = password.strip()
        st.session_state.current_key = "start"
        st.rerun()
else:
    current_key = st.session_state.current_key

    if current_key in question_tree and isinstance(question_tree[current_key], dict):
        question = question_tree[current_key]['text']

        # 画像表示
        show_image_for_question(current_key)
        with st.container():
            st.markdown(f"<div style='padding: 20px; border-radius: 10px; background-color: #f0f2f6;'><h3 style='text-align: center;'>{question}</h3></div>", unsafe_allow_html=True)
            
        st.markdown(" ")
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button("はい", use_container_width=True):
                next_key = question_tree[current_key]["yes"]
                st.session_state.current_key = next_key
                st.rerun()
            if st.button("いいえ", use_container_width=True):
                next_key = question_tree[current_key]["no"]
                st.session_state.current_key = next_key
                st.rerun()
    else:
        result_text = question_tree[current_key]
        st.success(f"{st.session_state.nickname} さんの診断結果：\n\n{result_text}", icon="✅")

        # 結果画像表示
        show_image_for_question(current_key)

        # 送信ボタン（重複送信防止）
        if not st.session_state.sent_to_sheet:
            if st.button("📤 診断結果をスプレッドシートに送信"):
                try:
                    send_to_google_sheets(st.session_state.nickname, st.session_state.password, result_text)
                    st.success("✅ スプレッドシートに送信しました！")
                    st.session_state.sent_to_sheet = True
                except Exception as e:
                    st.error(f"送信に失敗しました: {e}")
                    # よくある原因ヒント
                    sa = get_service_account_email()
                    if sa:
                        st.info(f"ヒント: スプレッドシートが `{sa}` に編集共有されているか確認してください。")
        else:
            st.info("（このセッションでは既に送信済みです）")

        if st.button("もう一度やる"):
            st.session_state.current_key = "start"
            st.session_state.nickname = None
            st.session_state.password = None
            st.session_state.sent_to_sheet = False
            st.rerun()
