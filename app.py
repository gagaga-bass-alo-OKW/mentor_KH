import streamlit as st
from supabase import create_client
import uuid

# Supabase接続
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="開邦雄飛会 メンター", page_icon="🎓")

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
                        info_col, img_col = st.columns([2, 1])
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
                        with info_col:
                            st.subheader(m["name"])
                            st.caption(f"{m['name_kana']}")
                            st.write(f"📅 第{m['entry_period']}期" if m["entry_period"] else "")
                            st.write(f"🏫 {m['course']}" if m["course"] else "")
                            st.write(f"📍 {m['location']}" if m["location"] else "")
                            st.write(f"💬 {m['bio']}" if m["bio"] else "")
