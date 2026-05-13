import streamlit as st
from supabase import create_client
import uuid

# Supabase接続
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="開邦雄飛会 メンター", page_icon="🎓")
st.markdown("""
<style>
/* メインカラー */
:root {
    --kh-main: #378ADD;
    --kh-main-light: #E6F1FB;
    --kh-main-dark: #185FA5;
    --kh-main-border: #B5D4F4;
}

/* ヘッダー */
[data-testid="stAppViewContainer"] {
    background-color: white;
}

/* ボタン */
.stButton > button {
    background-color: var(--kh-main) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
}
.stButton > button:hover {
    background-color: var(--kh-main-dark) !important;
}

/* テキスト入力・セレクトボックス */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    border-color: var(--kh-main-border) !important;
    border-radius: 8px !important;
}

/* カード */
[data-testid="stVerticalBlock"] > div[data-testid="element-container"] > div[data-testid="stVerticalBlock"] {
    border: 0.5px solid var(--kh-main-border) !important;
    border-radius: 12px !important;
    padding: 12px !important;
}

/* タグ風テキスト */
.mentor-tag {
    display: inline-block;
    background: var(--kh-main-light);
    color: var(--kh-main-dark);
    border: 0.5px solid var(--kh-main-border);
    border-radius: 99px;
    padding: 3px 10px;
    font-size: 12px;
    margin: 2px;
}

/* ヒーローセクション */
.hero-section {
    background: var(--kh-main-light);
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    margin-bottom: 20px;
}
.hero-section h2 {
    color: var(--kh-main-dark);
    font-size: 22px;
    margin-bottom: 6px;
}
.hero-section p {
    color: #555;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

params = st.query_params
token = params.get("token", None)
mode = params.get("mode", None)
page = params.get("page", "list")

# 管理者画面
if mode == st.secrets["ADMIN_SECRET"]:
    st.title("🔧 管理者画面")
    st.subheader("招待リンクの発行")

    email_input = st.text_input("招待するメンターのメールアドレス（任意）")

    if st.button("招待リンクを発行"):
        new_token = str(uuid.uuid4())
        supabase.table("invite_tokens").insert({
            "token": new_token,
            "email": email_input if email_input else None
        }).execute()
        app_url = st.secrets["APP_URL"]
        invite_url = f"{app_url}?page=register&token={new_token}"
        st.success("招待リンクを発行しました！")
        st.code(invite_url)

    st.divider()
    st.subheader("登録済みメンター一覧")
    mentors = supabase.table("mentors").select("*").execute()
    if mentors.data:
        for m in mentors.data:
            st.write(f"**{m['name']}** ({m['name_kana']}) - {m['role']} - {m['email']}")
    else:
        st.info("まだ登録されたメンターはいません。")
    st.stop()

# メンター登録ページ
if page == "register":
    def check_token(token):
        result = supabase.table("invite_tokens").select("*").eq("token", token).eq("used", False).execute()
        return len(result.data) > 0

    def mark_token_used(token):
        supabase.table("invite_tokens").update({"used": True}).eq("token", token).execute()

    if not token or not check_token(token):
        st.error("このページにアクセスする権限がありません。管理者から招待リンクを受け取ってください。")
        st.stop()

    st.markdown("""
<div class="hero-section">
    <h2>🎓 開邦雄飛会 メンター一覧</h2>
    <p>あなたの悩みに寄り添う先輩を探そう</p>
</div>
""", unsafe_allow_html=True)

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
    st.stop()

# 生徒の相談フォーム
if page == "consult":
    import datetime
    import json

    st.title("📝 メンターに相談する")
    st.write("以下のフォームに入力して送信してください。")

    with st.form("consult_form"):
        student_name = st.text_input("氏名 *")
        student_email = st.text_input("メールアドレス *")
        grade = st.selectbox("学年 *", ["中１", "中２", "中３", "高１", "高２", "高３", "保護者"])
        content = st.text_area("相談内容 *", placeholder="どんなことでも気軽に書いてください。")

        st.write("**希望日時を選んでください（複数選択可）**")
        st.caption("面談は基本的にオンラインです。可能な日時を多めに選ぶと調整しやすくなります。")

        today = datetime.date.today()
        dates = [today + datetime.timedelta(days=i) for i in range(1, 15)]
        hours = list(range(9, 22))
        day_labels = {"Mon":"月","Tue":"火","Wed":"水","Thu":"木","Fri":"金","Sat":"土","Sun":"日"}

        selected_times = []
        for date in dates:
            dow = day_labels[date.strftime("%a")]
            label = date.strftime(f"%m/%d（{dow}）")
            st.write(f"**{label}**")
            cols = st.columns(len(hours))
            for i, hour in enumerate(hours):
                with cols[i]:
                    st.caption(f"{hour}時")
                    if st.checkbox("", key=f"{date}_{hour}"):
                        selected_times.append(f"{label} {hour}:00")

        st.divider()
        st.write("**メンターの指定**")
        mentor_option = st.radio("", ["全体募集（誰でもOK）", "メンターを指名する"])

        mentor_id = None
        if mentor_option == "メンターを指名する":
            mentors = supabase.table("mentors").select("id, name, entry_period").eq("show_on_hp", True).execute()
            if mentors.data:
                mentor_options = {f"{m['name']}（第{m['entry_period']}期）": m["id"] for m in mentors.data}
                selected_mentor = st.selectbox("メンターを選んでください", list(mentor_options.keys()))
                mentor_id = mentor_options[selected_mentor]

        submitted = st.form_submit_button("送信する")

    if submitted:
        if not student_name or not student_email or not content:
            st.error("氏名・メールアドレス・相談内容は必須です。")
        elif len(selected_times) == 0:
            st.error("希望日時を1つ以上選んでください。")
        else:
            data = {
                "student_name": student_name,
                "student_email": student_email,
                "grade": grade,
                "content": content,
                "available_times": json.dumps(selected_times, ensure_ascii=False),
                "mentor_id": mentor_id,
                "is_open": mentor_option == "全体募集（誰でもOK）",
                "status": "pending",
            }
            supabase.table("consultations").insert(data).execute()
            st.success("✅ 送信完了しました！メンターからの連絡をお待ちください。")
            st.balloons()
    st.stop()
# メンター一覧ページ（デフォルト）
st.title("🎓 開邦雄飛会 メンター一覧")
st.write("在校生の相談に乗ってくれる先輩メンターたちです。")

mentors = supabase.table("mentors").select("*").eq("show_on_hp", True).execute()

if not mentors.data:
    st.info("現在登録されているメンターはいません。")
else:
    # 検索・フィルター
    col1, col2 = st.columns(2)
    with col1:
        search = st.text_input("🔍 名前で検索")
    with col2:
        course_filter = st.selectbox("コースで絞り込み", ["すべて", "理数科", "英語科", "芸術科", "学術探究科", "その他"])

    filtered = mentors.data
    if search:
        filtered = [m for m in filtered if search in m["name"] or search in m["name_kana"]]
    if course_filter != "すべて":
        filtered = [m for m in filtered if m["course"] == course_filter]

    st.write(f"**{len(filtered)}名**のメンターが登録されています。")
    st.divider()

    # カード表示
    for i in range(0, len(filtered), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j < len(filtered):
                m = filtered[i + j]
                with col:
                   with st.container(border=True):
                        # 上段：基礎情報 ＋ 写真
                        info_col, img_col = st.columns([1, 1])
                        with info_col:
                            st.markdown(f"#### {m['name']}")
                            st.write(f"{m['name_kana']}")
                            st.write(f"📅 第{m['entry_period']}期" if m["entry_period"] else "")
                            st.write(f"🏫 {m['course']}" if m["course"] else "")
                            st.write(f"📍 {m['location']}" if m["location"] else "")
                        with img_col:
                            if m.get("photo_url"):
                                try:
                                    photo = m["photo_url"]
                                    if "drive.google.com" in photo and "/file/d/" in photo:
                                        file_id = photo.split("/file/d/")[1].split("/")[0].split("?")[0]
                                        photo = f"https://drive.google.com/thumbnail?id={file_id}&sz=w200"
                                    st.image(photo, use_container_width=True)
                                except Exception as e:
                                    st.write(f"画像エラー: {e}")
                        # 下段：コメント
                        if m.get("bio"):
                            st.divider()
                            st.write(f"💬 {m['bio']}")
