import streamlit as st
from supabase import create_client
import uuid

# Supabase接続
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="メンター登録", page_icon="🎓")

# URLのトークンを取得
params = st.query_params
token = params.get("token", None)

def check_token(token):
    result = supabase.table("invite_tokens").select("*").eq("token", token).eq("used", False).execute()
    return len(result.data) > 0

def mark_token_used(token):
    supabase.table("invite_tokens").update({"used": True}).eq("token", token).execute()

# トークンがない場合
if not token or not check_token(token):
    st.error("このページにアクセスする権限がありません。管理者から招待リンクを受け取ってください。")
    st.stop()

# 登録フォーム
st.title("🎓 メンター登録フォーム")
st.write("開邦雄飛会メンター登録へようこそ。以下の情報を入力してください。")

with st.form("mentor_form"):
    role = st.selectbox("登録区分 *", ["メンターに登録", "特設授業の講師に登録", "両方"])
    name = st.text_input("氏名 *")
    name_kana = st.text_input("ふりがな *")
    email = st.text_input("メールアドレス *")
    entry_period = st.selectbox("入学期 *", list(range(1, 39)) + ["その他"])
    course = st.selectbox("在学時のコース *", ["理数科", "英語科", "芸術科", "学術探究科", "その他"])
    location = st.text_input("現在の居住地（例：東京都）")
    bio = st.text_area("一言プロフィール（後輩が最初に目にする紹介文です）")
    photo_url = st.text_input("プロフィール写真URL（Google DriveのリンクまたはなしでもOK）")
    show_on_hp = st.radio("HPへの掲載 *", ["掲載可", "掲載不可"]) == "掲載可"

    submitted = st.form_submit_button("登録する")

if submitted:
    if not name or not name_kana or not email:
        st.error("氏名・ふりがな・メールアドレスは必須です。")
    else:
        data = {
            "name": name,
            "name_kana": name_kana,
            "email": email,
            "entry_period": int(entry_period) if entry_period != "その他" else None,
            "course": course,
            "location": location,
            "bio": bio,
            "photo_url": photo_url,
            "show_on_hp": show_on_hp,
            "role": role,
        }
        supabase.table("mentors").insert(data).execute()
        mark_token_used(token)
        st.success("✅ 登録が完了しました！ご協力ありがとうございます。")
        st.balloons()
