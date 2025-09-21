import streamlit as st
import os, json, base64
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# =============================
# 設定
# =============================
SPREADSHEET_NAME = "personality_test"  # ←あなたのスプレッドシート名に変更
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# =============================
# 質問ツリー
# =============================
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
    "a": "🌟 あなたは **ポジティブタイプ** です！",
    "b": "🌸 あなたは **優しいタイプ** です！",
    "c": "🌧 あなたは **ネガティブタイプ** です！",
    "d": "🔥 あなたは **怒りっぽいタイプ** です！",
    "e": "❄️ あなたは **クールタイプ** です！",
    "f": "🌙 あなたは **おとなしいタイプ** です！",
    "g": "🎭 あなたは **感情豊かなタイプ** です！",
    "h": "💪 あなたは **熱血タイプ** です！",
    "i": "🌼 あなたは **天然タイプ** です！",
    "j": "🌀 あなたは **変人タイプ** です！",
}

# =============================
# Google Sheets 接続
# =============================
def get_gspread_client():
    """
    Streamlit Cloud → GitHub Secrets に設定した SERVICE_ACCOUNT_JSON を使用。
    JSON文字列かbase64文字列のどちらでもOK。
    """
    raw = os.environ.get("SERVICE_ACCOUNT_JSON")
    if not raw and os.path.exists("service_account.json"):
        # ローカルファイルがある場合
        creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
        return gspread.authorize(creds)
    if not raw:
        raise RuntimeError("Google認証情報が設定されていません。")

    try:
        info = json.loads(raw)
    except json.JSONDecodeError:
        # base64 形式ならデコード
        info = json.loads(base64.b64decode(raw).decode("utf-8"))
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)

def send_to_sheet(nickname, password, result_text):
    client = get_gspread_client()
    sheet = client.open(SPREADSHEET_NAME).sheet1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, nickname, password, result_text], value_input_option="USER_ENTERED")

# =============================
# UI 初期化
# =============================
st.set_page_config(page_title="性格診断テスト", page_icon="🧠")
st.title("🧠 性格診断テスト")
if "nickname" not in st.session_state:
    st.session_state.update({
        "nickname": None,
        "password": None,
        "current": "start",
        "sent": False
    })

# =============================
# 入力フォーム
# =============================
if not st.session_state.nickname or not st.session_state.password:
    st.warning("※ニックネームは後で確認できるようにメモしておいてください。")
    nick = st.text_input("ニックネーム")
    pw = st.text_input("パスワード", type="password")
    if st.button("診断スタート") and nick and pw:
        st.session_state.nickname = nick
        st.session_state.password = pw
        st.rerun()
else:
    key = st.session_state.current
    node = question_tree[key]

    if isinstance(node, dict):
        st.subheader(node["text"])
        col1, col2 = st.columns(2)
        if col1.button("はい"):
            st.session_state.current = node["yes"]
            st.rerun()
        if col2.button("いいえ"):
            st.session_state.current = node["no"]
            st.rerun()
    else:
        # 診断結果表示
        st.success(f"{st.session_state.nickname} さんの結果：\n\n{node}")
        if not st.session_state.sent:
            if st.button("📤 スプレッドシートに送信"):
                try:
                    send_to_sheet(st.session_state.nickname,
                                  st.session_state.password,
                                  node)
                    st.success("送信しました ✅")
                    st.session_state.sent = True
                except Exception as e:
                    st.error(f"送信に失敗しました: {e}")
        if st.button("もう一度やる"):
            st.session_state.update({
                "nickname": None,
                "password": None,
                "current": "start",
                "sent": False
            })
            st.rerun()
