import streamlit as st
import requests
import time
import re
from datetime import date, datetime
import json
import pandas as pd
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go

# 条件付きインポート（janome関連）
try:
    from janome.tokenizer import Tokenizer
    JANOME_AVAILABLE = True
except ImportError:
    JANOME_AVAILABLE = False
    st.warning("janomeライブラリがインストールされていません。形態素解析機能は無効です。")

try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import numpy as np
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WORDCLOUD_AVAILABLE = False

# ページ設定
st.set_page_config(
    page_title="国会議事録検索アプリ",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2e6da4;
        margin-bottom: 1rem;
    }
    .highlight-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 20px 0;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f4e79;
    }
    .speech-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

# APIのエンドポイント
API_URL = "https://kokkai.ndl.go.jp/api/speech"

class KokkaiSearchApp:
    def __init__(self):
        if 'search_history' not in st.session_state:
            st.session_state.search_history = []
        if 'search_results' not in st.session_state:
            st.session_state.search_results = None
        if 'analytics_data' not in st.session_state:
            st.session_state.analytics_data = {}

        # janome初期化（利用可能な場合のみ）
        if JANOME_AVAILABLE:
            self.tokenizer = Tokenizer()

            # ストップワード（除外する単語）
            self.stop_words = {
                'する', 'ある', 'いる', 'なる', 'れる', 'この', 'その', 'あの', 'という', 'といった',
                'として', 'について', 'において', 'に対して', 'というふうに', 'だと', 'である', 'です',
                'ます', 'でき', 'よう', 'もの', 'こと', '場合', '中', '私', '我々', '皆さん', '皆様',
                '今', '現在', '今回', '今度', '先ほど', '先程', '本日', '今日', '昨日', '明日',
                'はい', 'いえ', 'ええ', 'うん', 'そう', 'いや', 'まあ', 'ちょっと', 'やはり', 'やっぱり',
                '委員', '大臣', '議員', '先生', '総理', '副', '会長', '理事', '長', '部長', '課長',
                '時間', '分', '秒', '年', '月', '日', '週', '回', '度', '番', '号', '第', '章', '条',
                '思う', '考える', '感じる', '見る', '聞く', '言う', '話す', '述べる', '申し上げる'
            }
        else:
            self.tokenizer = None
            self.stop_words = set()

    def highlight_text(self, text, keywords_str):
        """テキスト内のキーワードをハイライト"""
        if not keywords_str or not text:
            return text

        keywords = keywords_str.split()
        highlighted_text = text

        for keyword in keywords:
            highlighted_text = re.sub(
                re.escape(keyword),
                lambda m: f'<span style="background-color: #fff3cd; padding: 2px 4px; border-radius: 3px; font-weight: bold;">{m.group(0)}</span>',
                highlighted_text,
                flags=re.IGNORECASE
            )
        return highlighted_text

    def search_speeches(self, params):
        """国会会議録API検索"""
        try:
            api_params = {
                "maximumRecords": 30,
                "recordPacking": "json"
            }
            api_params.update(params)

            response = requests.get(API_URL, params=api_params, timeout=15.0)
            response.raise_for_status()

            if response.text:
                return response.json()
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"APIへの接続中にエラーが発生しました: {e}")
            return None
        except ValueError:
            st.error("APIからの応答が不正な形式です。")
            return None

    def extract_keywords(self, text, min_length=2, top_n=50):
        """janomeを使って形態素解析し、キーワードを抽出"""
        if not JANOME_AVAILABLE or not text:
            return {}

        keywords = []

        # テキストを形態素解析
        tokens = self.tokenizer.tokenize(text)

        for token in tokens:
            # 品詞情報を取得
            features = token.part_of_speech.split(',')
            word = token.surface.strip()

            # 条件でフィルタリング
            if (len(word) >= min_length and  # 指定文字数以上
                word not in self.stop_words and  # ストップワード除外
                not word.isdigit() and  # 数字のみ除外
                features[0] in ['名詞', '動詞', '形容詞'] and  # 品詞フィルタ
                features[1] not in ['代名詞', '数', '接尾'] and  # 細分類フィルタ
                not re.match(r'^[ぁ-ん]+$', word)):  # ひらがなのみ除外

                # 動詞の場合は原形に変換
                if features[0] == '動詞' and len(features) >= 7 and features[6] != '*':
                    keywords.append(features[6])
                else:
                    keywords.append(word)

        # 単語の出現回数をカウント
        keyword_counts = Counter(keywords)
        return dict(keyword_counts.most_common(top_n))

    def analyze_meeting_keywords(self, data):
        """会議別のキーワード分析"""
        if not data or "speechRecord" not in data:
            return {}

        records = data["speechRecord"]
        meeting_analysis = {}

        # 会議別に発言をグループ化
        meeting_groups = {}
        for record in records:
            meeting_name = record.get('nameOfMeeting', '不明')
            if meeting_name not in meeting_groups:
                meeting_groups[meeting_name] = []
            meeting_groups[meeting_name].append(record)

        # 各会議のキーワード分析
        for meeting_name, meeting_records in meeting_groups.items():
            # 全発言を結合
            all_speeches = ' '.join([record.get('speech', '') for record in meeting_records])

            # キーワード抽出
            keywords = self.extract_keywords(all_speeches)

            # 発言者リスト
            speakers = list(set([record.get('speaker', '不明') for record in meeting_records]))

            meeting_analysis[meeting_name] = {
                'keywords': keywords,
                'speakers': speakers,
                'total_speeches': len(meeting_records),
                'total_characters': len(all_speeches),
                'speeches': meeting_records
            }

        return meeting_analysis

    def create_wordcloud(self, keywords):
        """ワードクラウドを生成"""
        if not WORDCLOUD_AVAILABLE or not keywords:
            return None

        try:
            # 日本語フォントの設定
            font_path = None
            # システムの日本語フォントを探す
            fonts = fm.findSystemFonts()
            for font in fonts:
                if any(jp_font in font.lower() for jp_font in ['noto', 'hiragino', 'yu', 'meiryo', 'msgothic']):
                    font_path = font
                    break

            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color='white',
                font_path=font_path,
                colormap='viridis',
                max_words=100,
                relative_scaling=0.5,
                random_state=42
            ).generate_from_frequencies(keywords)

            return wordcloud
        except Exception as e:
            st.warning(f"ワードクラウドの生成に失敗しました: {e}")
            return None

    def analyze_search_results(self, data):
        """検索結果の分析"""
        if not data or "speechRecord" not in data:
            return {}

        records = data["speechRecord"]

        # 発言者の分析
        speakers = [record.get('speaker', '不明') for record in records]
        speaker_counts = Counter(speakers)

        # 会議の分析
        meetings = [record.get('nameOfMeeting', '不明') for record in records]
        meeting_counts = Counter(meetings)

        # 日付の分析
        dates = []
        for record in records:
            date_str = record.get('date', '')
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    dates.append(date_obj)
                except:
                    pass

        # 発言の長さ分析
        speech_lengths = [len(record.get('speech', '')) for record in records]

        return {
            'total_records': len(records),
            'speaker_counts': dict(speaker_counts.most_common(10)),
            'meeting_counts': dict(meeting_counts.most_common(10)),
            'dates': dates,
            'speech_lengths': speech_lengths,
            'avg_speech_length': sum(speech_lengths) / len(speech_lengths) if speech_lengths else 0
        }

    def create_visualizations(self, analytics):
        """データ可視化"""
        if not analytics:
            return

        col1, col2 = st.columns(2)

        with col1:
            if analytics.get('speaker_counts'):
                st.subheader("📊 発言者別件数")
                speakers_df = pd.DataFrame(
                    list(analytics['speaker_counts'].items()),
                    columns=['発言者', '件数']
                )
                fig = px.bar(speakers_df, x='件数', y='発言者', orientation='h',
                           color='件数', color_continuous_scale='Blues')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if analytics.get('meeting_counts'):
                st.subheader("🏛️ 会議別件数")
                meetings_df = pd.DataFrame(
                    list(analytics['meeting_counts'].items()),
                    columns=['会議名', '件数']
                )
                fig = px.pie(meetings_df, values='件数', names='会議名',
                           color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

        # 時系列分析
        if analytics.get('dates'):
            st.subheader("📅 時系列分析")
            dates_df = pd.DataFrame({'日付': analytics['dates']})
            dates_df['年月'] = dates_df['日付'].dt.to_period('M')
            monthly_counts = dates_df.groupby('年月').size().reset_index(name='件数')
            monthly_counts['年月'] = monthly_counts['年月'].astype(str)

            fig = px.line(monthly_counts, x='年月', y='件数',
                         title='月別発言件数の推移',
                         markers=True)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    def export_results(self, data, search_params):
        """検索結果のエクスポート"""
        if not data or "speechRecord" not in data:
            return None

        records = data["speechRecord"]
        export_data = []

        for record in records:
            export_data.append({
                '発言日': record.get('date', ''),
                '発言者': record.get('speaker', ''),
                '会議名': record.get('nameOfMeeting', ''),
                '院名': record.get('nameOfHouse', ''),
                '発言内容': record.get('speech', '')[:500] + '...' if len(record.get('speech', '')) > 500 else record.get('speech', ''),
                'URL': record.get('speechURL', '')
            })

        df = pd.DataFrame(export_data)
        return df

    def main(self):
        # ヘッダー
        st.markdown('<h1 class="main-header">🏛️ 国会議事録検索・分析アプリ</h1>', unsafe_allow_html=True)

        # サイドバー
        with st.sidebar:
            st.markdown("### 🔍 検索メニュー")
            page_options = ["🔍 検索", "📊 分析", "📚 検索履歴", "ℹ️ 使い方"]

            # janome利用可能な場合のみキーワード分析を追加
            if JANOME_AVAILABLE:
                page_options.insert(2, "🏛️ 会議別キーワード分析")

            page = st.selectbox("ページを選択", page_options)

        if page == "🔍 検索":
            self.search_page()
        elif page == "📊 分析":
            self.analysis_page()
        elif page == "🏛️ 会議別キーワード分析" and JANOME_AVAILABLE:
            self.meeting_analysis_page()
        elif page == "📚 検索履歴":
            self.history_page()
        else:
            self.help_page()

    def search_page(self):
        st.markdown('<h2 class="sub-header">🔍 国会議事録検索</h2>', unsafe_allow_html=True)

        # 検索フォーム
        with st.form("search_form"):
            keyword = st.text_input("🔎 検索キーワード（AND検索）",
                                  placeholder="例：デジタル改革 規制緩和",
                                  help="複数のキーワードをスペースで区切って入力")

            col1, col2, col3 = st.columns(3)
            with col1:
                speaker = st.text_input("👤 発言者名", placeholder="例：岸田文雄")
            with col2:
                name_of_meeting = st.text_input("🏛️ 会議名", placeholder="例：予算委員会")
            with col3:
                name_of_house = st.selectbox("🏢 院名", ("指定しない", "衆議院", "参議院", "両院"))

            col4, col5 = st.columns(2)
            with col4:
                from_date = st.date_input("📅 検索期間（開始日）", value=None)
            with col5:
                until_date = st.date_input("📅 検索期間（終了日）", value=None)

            search_button = st.form_submit_button("🔍 検索実行", type="primary")

        if search_button:
            # 検索パラメータの構築
            search_params = {}

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

            if search_params:
                with st.spinner("🔍 検索中です..."):
                    time.sleep(1)
                    data = self.search_speeches(search_params)

                    if data and "speechRecord" in data and data["speechRecord"]:
                        st.session_state.search_results = data
                        st.session_state.analytics_data = self.analyze_search_results(data)

                        # janome利用可能な場合のみキーワード分析を実行
                        if JANOME_AVAILABLE:
                            st.session_state.meeting_analysis = self.analyze_meeting_keywords(data)

                        # 検索履歴に追加
                        search_history_item = {
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'params': search_params,
                            'results_count': data['numberOfRecords']
                        }
                        st.session_state.search_history.insert(0, search_history_item)
                        if len(st.session_state.search_history) > 10:
                            st.session_state.search_history.pop()

                        # 成功メッセージ
                        st.success(f"✅ 検索結果が {data['numberOfRecords']} 件見つかりました。（最大30件表示）")

                        # エクスポート機能
                        export_df = self.export_results(data, search_params)
                        if export_df is not None:
                            csv = export_df.to_csv(index=False, encoding='utf-8-sig')
                            st.download_button(
                                label="📄 検索結果をCSVでダウンロード",
                                data=csv,
                                file_name=f"kokkai_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )

                        # 検索結果表示
                        for i, record in enumerate(data["speechRecord"]):
                            with st.expander(f"📝 {record['speaker']}（{record['nameOfMeeting']}）- {record['date']}"):
                                col1, col2 = st.columns([3, 1])

                                with col1:
                                    st.markdown(f"**📅 発言日:** {record['date']}")
                                    st.markdown(f"**👤 発言者:** {record['speaker']}")
                                    st.markdown(f"**🏛️ 会議:** {record['nameOfMeeting']}")
                                    st.markdown(f"**🏢 院:** {record.get('nameOfHouse', '不明')}")

                                with col2:
                                    speech_length = len(record['speech'])
                                    st.metric("文字数", f"{speech_length:,}")

                                st.markdown("---")

                                # 発言内容のハイライト表示
                                speech_text = record['speech']
                                highlighted_speech = self.highlight_text(speech_text, keyword)

                                st.markdown(
                                    f'<div class="speech-card" style="height: 300px; overflow-y: auto;">{highlighted_speech}</div>',
                                    unsafe_allow_html=True
                                )

                                st.markdown(f"🔗 [発言の全文と周辺議事を読む]({record['speechURL']})")
                    else:
                        st.warning("⚠️ 検索結果が見つかりませんでした。条件を変えて試してください。")
            else:
                st.error("❌ 検索条件を何か一つ以上入力してください。")

    def meeting_analysis_page(self):
        st.markdown('<h2 class="sub-header">🏛️ 会議別キーワード分析</h2>', unsafe_allow_html=True)

        if not JANOME_AVAILABLE:
            st.error("❌ この機能を使用するには janome ライブラリが必要です。")
            st.code("pip install janome")
            return

        if 'meeting_analysis' not in st.session_state or not st.session_state.meeting_analysis:
            st.info("🔍 分析データがありません。まず検索を実行してください。")
            return

        meeting_analysis = st.session_state.meeting_analysis

        # 会議選択
        selected_meeting = st.selectbox(
            "📋 分析する会議を選択してください",
            list(meeting_analysis.keys()),
            help="検索結果に含まれる会議から選択"
        )

        if selected_meeting:
            meeting_data = meeting_analysis[selected_meeting]

            # 会議の基本情報
            st.markdown("### 📊 会議基本情報")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("発言数", f"{meeting_data['total_speeches']}件")
            with col2:
                st.metric("発言者数", f"{len(meeting_data['speakers'])}人")
            with col3:
                st.metric("総文字数", f"{meeting_data['total_characters']:,}字")
            with col4:
                avg_chars = meeting_data['total_characters'] // meeting_data['total_speeches']
                st.metric("平均文字数", f"{avg_chars:,}字/発言")

            # 発言者一覧
            st.markdown("### 👥 発言者一覧")
            speakers_text = "、".join(meeting_data['speakers'])
            st.write(speakers_text)

            st.markdown("---")

            # キーワード分析
            if meeting_data['keywords']:
                st.markdown("### 🔤 キーワード分析")

                # タブで表示方法を切り替え
                tab1, tab2, tab3 = st.tabs(["📊 ランキング", "☁️ ワードクラウド", "📈 詳細分析"])

                with tab1:
                    # キーワードランキング
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        keywords_df = pd.DataFrame(
                            list(meeting_data['keywords'].items())[:20],
                            columns=['キーワード', '出現回数']
                        )

                        fig = px.bar(
                            keywords_df,
                            x='出現回数',
                            y='キーワード',
                            orientation='h',
                            title=f"{selected_meeting} - 主要キーワード Top20",
                            color='出現回数',
                            color_continuous_scale='Viridis'
                        )
                        fig.update_layout(height=600)
                        st.plotly_chart(fig, use_container_width=True)

                    with col2:
                        st.markdown("#### 📋 キーワード一覧")
                        for i, (keyword, count) in enumerate(list(meeting_data['keywords'].items())[:15], 1):
                            st.write(f"{i:2d}. **{keyword}** ({count}回)")

                with tab2:
                    # ワードクラウド
                    st.markdown("#### ☁️ ワードクラウド")
                    if WORDCLOUD_AVAILABLE:
                        wordcloud = self.create_wordcloud(meeting_data['keywords'])

                        if wordcloud:
                            fig, ax = plt.subplots(figsize=(12, 6))
                            ax.imshow(wordcloud, interpolation='bilinear')
                            ax.axis('off')
                            st.pyplot(fig)
                            plt.close()
                        else:
                            st.warning("ワードクラウドを生成できませんでした。")
                    else:
                        st.warning("ワードクラウド機能を使用するには wordcloud ライブラリが必要です。")
                        st.code("pip install wordcloud")

                with tab3:
                    # 詳細分析
                    st.markdown("#### 📈 キーワード詳細分析")

                    # キーワード長別分布
                    keyword_lengths = [len(k) for k in meeting_data['keywords'].keys()]
                    length_counts = Counter(keyword_lengths)

                    col1, col2 = st.columns(2)

                    with col1:
                        length_df = pd.DataFrame(
                            list(length_counts.items()),
                            columns=['文字数', '単語数']
                        ).sort_values('文字数')

                        fig = px.bar(
                            length_df,
                            x='文字数',
                            y='単語数',
                            title="キーワード文字数分布"
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    with col2:
                        # 出現頻度分布
                        freq_counts = Counter(meeting_data['keywords'].values())
                        freq_df = pd.DataFrame(
                            list(freq_counts.items()),
                            columns=['出現回数', '単語数']
                        ).sort_values('出現回数')

                        fig = px.bar(
                            freq_df,
                            x='出現回数',
                            y='単語数',
                            title="出現頻度分布"
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    # 統計情報
                    st.markdown("#### 📊 統計サマリー")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        total_keywords = len(meeting_data['keywords'])
                        st.metric("ユニーク単語数", f"{total_keywords}")

                    with col2:
                        total_occurrences = sum(meeting_data['keywords'].values())
                        st.metric("総出現回数", f"{total_occurrences}")

                    with col3:
                        avg_occurrence = total_occurrences / total_keywords if total_keywords > 0 else 0
                        st.metric("平均出現回数", f"{avg_occurrence:.1f}")

                # キーワード検索機能
                st.markdown("---")
                st.markdown("### 🔍 キーワード検索")
                search_keyword = st.text_input("特定のキーワードを検索", placeholder="例：デジタル")

                if search_keyword:
                    matching_keywords = {
                        k: v for k, v in meeting_data['keywords'].items()
                        if search_keyword.lower() in k.lower()
                    }

                    if matching_keywords:
                        st.success(f"'{search_keyword}' に関連するキーワードが {len(matching_keywords)} 個見つかりました。")

                        for keyword, count in sorted(matching_keywords.items(), key=lambda x: x[1], reverse=True):
                            st.write(f"• **{keyword}**: {count}回")
                    else:
                        st.warning(f"'{search_keyword}' に関連するキーワードは見つかりませんでした。")

            else:
                st.warning("キーワードが抽出できませんでした。")

    def analysis_page(self):
        st.markdown('<h2 class="sub-header">📊 検索結果分析</h2>', unsafe_allow_html=True)

        if st.session_state.analytics_data:
            analytics = st.session_state.analytics_data

            # サマリー表示
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(
                    f'<div class="metric-card"><h3>📊 総件数</h3><h2>{analytics["total_records"]}</h2></div>',
                    unsafe_allow_html=True
                )

            with col2:
                avg_length = int(analytics.get("avg_speech_length", 0))
                st.markdown(
                    f'<div class="metric-card"><h3>📝 平均文字数</h3><h2>{avg_length:,}</h2></div>',
                    unsafe_allow_html=True
                )

            with col3:
                unique_speakers = len(analytics.get("speaker_counts", {}))
                st.markdown(
                    f'<div class="metric-card"><h3>👥 発言者数</h3><h2>{unique_speakers}</h2></div>',
                    unsafe_allow_html=True
                )

            with col4:
                unique_meetings = len(analytics.get("meeting_counts", {}))
                st.markdown(
                    f'<div class="metric-card"><h3>🏛️ 会議数</h3><h2>{unique_meetings}</h2></div>',
                    unsafe_allow_html=True
                )

            st.markdown("---")

            # 可視化
            self.create_visualizations(analytics)

        else:
            st.info("📊 分析データがありません。まず検索を実行してください。")

    def history_page(self):
        st.markdown('<h2 class="sub-header">📚 検索履歴</h2>', unsafe_allow_html=True)

        if st.session_state.search_history:
            for i, item in enumerate(st.session_state.search_history):
                with st.expander(f"🕐 {item['timestamp']} - {item['results_count']}件"):
                    st.json(item['params'])
        else:
            st.info("📚 検索履歴がありません。")

    def help_page(self):
        st.markdown('<h2 class="sub-header">ℹ️ 使い方ガイド</h2>', unsafe_allow_html=True)

        st.markdown("""
        ### 🔍 検索機能
        - **キーワード検索**: 発言内容から複数キーワードで AND 検索
        - **発言者検索**: 特定の政治家名で検索
        - **会議名検索**: 委員会名などで検索
        - **期間指定**: 日付範囲での絞り込み
        - **院別検索**: 衆議院・参議院での絞り込み

        ### 🏛️ 会議別キーワード分析機能
        - **形態素解析**: janomeライブラリによる日本語テキスト解析
        - **キーワード抽出**: 名詞・動詞・形容詞から重要語句を抽出
        - **ワードクラウド**: 視覚的なキーワード表示
        - **詳細統計**: 文字数分布、出現頻度分析
        - **キーワード検索**: 特定語句の関連キーワード検索

        ### 📊 分析機能
        - **統計サマリー**: 検索結果の基本統計
        - **発言者分析**: 発言者別の件数グラフ
        - **会議分析**: 会議別の分類円グラフ
        - **時系列分析**: 月別発言件数の推移

        ### 💾 エクスポート機能
        - **CSV出力**: 検索結果をCSVファイルでダウンロード
        - **検索履歴**: 過去の検索条件を保存・確認

        ### 🎨 特徴
        - **キーワードハイライト**: 検索語句を結果内で強調表示
        - **レスポンシブデザイン**: 美しいUI/UX
        - **リアルタイム分析**: 検索と同時にデータ分析

        ### 📦 必要なライブラリ
        ```bash
        pip install streamlit requests pandas plotly janome wordcloud matplotlib numpy
        ```
        """)

        st.markdown("---")
        st.info("""
        **【ご利用上の注意】**
        - このアプリは、国立国会図書館の[国会会議録検索システム検索用API](https://kokkai.ndl.go.jp/api.html)を利用しています。
        - サーバーに負荷をかけないよう、連続での検索はお控えください。
        - 国会議事録における各発言の著作権は、原則としてそれぞれの発言者に帰属します。
        - 形態素解析機能を使用するには janome ライブラリのインストールが必要です。
        - ワードクラウド機能を使用するには wordcloud ライブラリのインストールが必要です。
        """)

# アプリ実行
if __name__ == "__main__":
    app = KokkaiSearchApp()
    app.main()
