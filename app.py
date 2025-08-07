import streamlit as st
import requests
import time
import re #正規表現を扱うためにreモジュールをインポート
from datetime import date

# APIのエンドポイント
API_URL = "https://kokkai.ndl.go.jp/api/speech"

def highlight_text(text, keywords_str):
    """
    テキスト内のキーワードをハイライトするためのHTMLを生成する関数
    """
    if not keywords_str or not text:
        return text

    # 複数のキーワードをリストに分割
    keywords = keywords_str.split()
    highlighted_text = text

    for keyword in keywords:
        # 特殊文字をエスケープし、ハイライト用のHTMLタグで置換
        # re.IGNORECASEで大文字・小文字を区別せずに検索
        highlighted_text = re.sub(
            re.escape(keyword),
            lambda m: f'<span style="background-color: #fff8c4; padding: 2px 0;">{m.group(0)}</span>',
            highlighted_text,
            flags=re.IGNORECASE
        )
    return highlighted_text


def search_speeches(params):
    """
    国会会議録検索システムAPIを使って発言を検索する関数
    """
    try:
        response = requests.get(API_URL, params=params, timeout=10.0)
        response.raise_for_status()
        if response.text:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"APIへの接続中にエラーが発生しました: {e}")
        return None
    except ValueError:
        st.error("APIからの応答が不正な形式です。")
        return None

# --- Streamlit アプリのUI部分 ---

st.title("国会議事録 詳細検索アプリ 🏛️")

keyword = st.text_input("検索キーワード（AND検索）", placeholder="例：デジタル改革 規制緩和")

with st.expander("詳細検索オプションを開く"):
    col1, col2, col3 = st.columns(3)
    with col1:
        speaker = st.text_input("発言者名（OR検索）", placeholder="例：岸田文雄")
    with col2:
        name_of_meeting = st.text_input("会議名（OR検索）", placeholder="例：予算委員会")
    with col3:
        name_of_house = st.selectbox(
            "院名",
            ("指定しない", "衆議院", "参議院", "両院")
        )
    col4, col5 = st.columns(2)
    with col4:
        from_date = st.date_input("検索期間（開始日）", value=None)
    with col5:
        until_date = st.date_input("検索期間（終了日）", value=None)

if st.button("検索実行"):
    search_params = {
        "maximumRecords": 20,
        "recordPacking": "json"
    }

    if keyword:
        search_params["any"] = keyword
    if speaker:
        search_params["speaker"] = speaker
    if name_of_meeting:
        search_params["nameOfMeeting"] = name_of_meeting
    if name_of_house != "指定しない":
        search_params["nameOfHouse"] = name_of_house
    if from_date:
        search_params["from"] = from_date.strftime('%Y-%m-%d')
    if until_date:
        search_params["until"] = until_date.strftime('%Y-%m-%d')

    if len(search_params) > 2:
        with st.spinner("検索中です..."):
            time.sleep(1)
            data = search_speeches(search_params)

            if data and "speechRecord" in data and data["speechRecord"]:
                st.success(f"検索結果が {data['numberOfRecords']} 件見つかりました。（最大20件表示）")

                for record in data["speechRecord"]:
                    with st.expander(f"{record['speaker']}（{record['nameOfMeeting']}）"):
                        st.markdown(f"**発言日:** {record['date']}")
                        st.markdown(f"**発言者:** {record['speaker']}")
                        st.markdown("---")

                        # 発言内容を取得し、キーワードをハイライトする
                        speech_text = record['speech']
                        highlighted_speech = highlight_text(speech_text, keyword)

                        # HTMLをレンダリングするためにst.markdownを使用
                        # スクロール可能なボックスで囲む
                        st.markdown(
                            f'<div style="height: 200px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; border-radius: 5px;">{highlighted_speech}</div>',
                            unsafe_allow_html=True
                        )
                        st.markdown(f"[発言の全文と周辺議事を読む]({record['speechURL']})", unsafe_allow_html=True)
            else:
                st.warning("検索結果が見つかりませんでした。条件を変えて試してください。")
    else:
        st.error("検索条件を何か一つ以上入力してください。")

st.markdown("---")
st.info("""
**【ご利用上の注意】**
- このアプリは、国立国会図書館の[国会会議録検索システム検索用API](https://kokkai.ndl.go.jp/api.html)を利用しています。
- サーバーに負荷をかけないよう、連続での検索はお控えください。
- 国会議事録における各発言の著作権は、原則としてそれぞれの発言者に帰属します。
""")
