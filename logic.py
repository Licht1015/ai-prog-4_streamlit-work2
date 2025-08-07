# =============================================================================
# 国会議事録検索・分析アプリケーション - ビジネスロジック
# =============================================================================
# 
# 概要:
# このファイルは国会議事録検索・分析アプリケーションのコアロジックを定義します。
# 国会議事録APIとの通信、データ処理、分析機能、可視化機能を提供します。
# 
# 課題2: Streamlitを使ったアプリの開発 + 公開
# 学籍番号: [学籍番号]
# 作成者: [名前]
# 作成日: 2024年8月
# 
# 主要機能:
# - 国会議事録APIとの通信・検索
# - 検索結果のデータ処理・分析
# - キーワード抽出・形態素解析
# - 統計分析・可視化
# - 検索履歴の管理
# - データエクスポート
# 
# クラス構成:
# - KokkaiSearchApp: メインアプリケーションクラス
# 
# 依存関係:
# - streamlit: UIフレームワーク
# - requests: HTTP通信
# - pandas: データ処理
# - plotly: データ可視化
# - janome: 日本語形態素解析（オプション）
# - wordcloud: ワードクラウド生成（オプション）
# - matplotlib: グラフ描画（オプション）
# 
# API仕様:
# - エンドポイント: https://kokkai.ndl.go.jp/api/speech
# - パラメータ: keyword, from, until, speaker, meeting
# - レスポンス: JSON形式の議事録データ
# 
# 開発環境:
# - Anaconda仮想環境
# - Python 3.8+
# 
# バージョン: 1.1.0
# =============================================================================

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
import os

# =============================================================================
# 条件付きインポート設定
# =============================================================================
# 
# 説明:
# 一部のライブラリはオプション機能として実装されており、
# インストールされていない場合でもアプリケーションは動作します。
# 各ライブラリの利用可能性をチェックし、適切な初期化を行います。

# Janome（日本語形態素解析）の条件付きインポート
try:
    from janome.tokenizer import Tokenizer
except ImportError:
    pass

# WordCloud（ワードクラウド生成）の条件付きインポート
try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import numpy as np
except ImportError:
    pass

# =============================================================================
# 定数定義
# =============================================================================

# APIエンドポイント
API_URL = "https://kokkai.ndl.go.jp/api/speech"

# =============================================================================
# メインアプリケーションクラス
# =============================================================================

class KokkaiSearchApp:
    """
    国会議事録検索・分析アプリケーションのメインクラス
    
    機能:
    - 国会議事録APIとの通信
    - 検索機能の実装
    - データ分析・可視化
    - 検索履歴の管理
    - キーワード分析
    - ワードクラウド生成
    
    属性:
    - tokenizer: Janomeトークナイザー（オプション）
    - stop_words: ストップワードセット
    - session_state: Streamlitセッション状態
    
    メソッド:
    - __init__: 初期化
    - search_speeches: 議事録検索
    - analyze_search_results: 検索結果分析
    - extract_keywords: キーワード抽出
    - create_visualizations: 可視化作成
    - 各ページ表示メソッド
    """
    
    def __init__(self):
        """
        アプリケーションの初期化
        
        機能:
        - セッション状態の初期化
        - Janomeトークナイザーの初期化（利用可能な場合）
        - ストップワードの設定
        - 基本設定の読み込み
        
        セッション状態:
        - search_history: 検索履歴
        - search_results: 検索結果
        - analytics_data: 分析データ
        """
        
        # =====================================================================
        # セッション状態の初期化
        # =====================================================================
        
        # 検索履歴の初期化
        if 'search_history' not in st.session_state:
            st.session_state.search_history = []
        
        # 検索結果の初期化
        if 'search_results' not in st.session_state:
            st.session_state.search_results = None
        
        # 分析データの初期化
        if 'analytics_data' not in st.session_state:
            st.session_state.analytics_data = {}
        
        # =====================================================================
        # Janome初期化（利用可能な場合のみ）
        # =====================================================================
        
        # Janomeライブラリの利用可能性をチェック
        try:
            from janome.tokenizer import Tokenizer
            self.tokenizer = Tokenizer()
            
            # ストップワード（除外する単語）の定義
            # 日本語の議事録に特化したストップワードセット
            self.stop_words = {
                # 基本動詞・助動詞
                'する', 'ある', 'いる', 'なる', 'れる', 'られる', 'せる', 'させる',
                
                # 指示詞・接続詞
                'この', 'その', 'あの', 'どの', 'という', 'といった', 'として', 'について',
                'において', 'に対して', 'というふうに', 'だと', 'である', 'です', 'ます',
                
                # 助詞・副詞
                'でき', 'よう', 'もの', 'こと', '場合', '中', 'ため', 'から', 'まで',
                
                # 人称代名詞
                '私', '我々', '皆さん', '皆様', 'あなた', 'あなた方',
                
                # 時間表現
                '今', '現在', '今回', '今度', '先ほど', '先程', '本日', '今日', '昨日', '明日',
                '時間', '分', '秒', '年', '月', '日', '週', '回', '度', '番', '号',
                
                # 応答表現
                'はい', 'いえ', 'ええ', 'うん', 'そう', 'いや', 'まあ', 'ちょっと', 'やはり', 'やっぱり',
                
                # 役職・敬称
                '委員', '大臣', '議員', '先生', '総理', '副', '会長', '理事', '長', '部長', '課長',
                '様', 'さん', '氏', '君',
                
                # 法律・制度関連
                '第', '章', '条', '項', '法', '法律', '制度', '政策',
                
                # 思考・感情表現
                '思う', '考える', '感じる', '見る', '聞く', '言う', '話す', '述べる', '申し上げる',
                '知る', '分かる', '理解する', '説明する', '報告する',
                
                # その他
                'など', 'とか', 'やら', 'かも', 'かもしれない', 'でしょう', 'かもしれません'
            }
        except ImportError:
            # Janomeが利用できない場合は空のセットを使用
            self.tokenizer = None
            self.stop_words = set()

    # =============================================================================
    # 検索履歴管理メソッド
    # =============================================================================

    def save_search_history_to_csv(self):
        """
        検索履歴をCSVファイルに保存
        
        機能:
        - セッション状態の検索履歴をCSVファイルに保存
        - JSON形式のパラメータを文字列として保存
        - UTF-8エンコーディングで保存
        
        戻り値:
        - bool: 保存成功時True、失敗時False
        
        エラー処理:
        - ファイル書き込みエラーの場合: エラーメッセージを表示
        - 空の履歴の場合: 何もしない
        """
        if st.session_state.search_history:
            try:
                # 検索履歴をDataFrameに変換
                history_data = []
                for item in st.session_state.search_history:
                    history_data.append({
                        'timestamp': item.get('timestamp', ''),
                        'params': json.dumps(item.get('params', {}), ensure_ascii=False),
                        'results_count': item.get('results_count', 0)
                    })
                
                # DataFrameを作成してCSVに保存
                df = pd.DataFrame(history_data)
                df.to_csv('search_history.csv', index=False, encoding='utf-8-sig')
                
                st.success("✅ 検索履歴を正常に保存しました")
                return True
                
            except Exception as e:
                st.error(f"❌ 検索履歴の保存に失敗しました: {e}")
                return False
        else:
            st.info("ℹ️ 保存する検索履歴がありません")
            return False

    def add_to_search_history(self, search_params, results_count):
        """
        検索履歴に追加してCSVに保存
        
        機能:
        - 新しい検索条件と結果数を履歴に追加
        - 重複チェック（同じパラメータの場合は更新）
        - タイムスタンプの自動付与
        - CSVファイルへの自動保存
        
        パラメータ:
        - search_params (dict): 検索パラメータ
        - results_count (int): 検索結果数
        
        処理フロー:
        1. 新しい履歴アイテムの作成
        2. 重複チェック
        3. 履歴への追加/更新
        4. CSVファイルへの保存
        """
        
        # デバッグ情報の表示
        st.write(f"💾 検索履歴に保存: {search_params}")
        
        # 新しい履歴アイテムの作成
        search_history_item = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'params': search_params,
            'results_count': results_count
        }
        
        # 重複チェック（同じパラメータの場合は更新）
        existing_index = None
        for i, item in enumerate(st.session_state.search_history):
            if item.get('params') == search_params:
                existing_index = i
                break
        
        if existing_index is not None:
            # 既存の履歴を更新
            st.session_state.search_history[existing_index] = search_history_item
            st.info("🔄 既存の検索履歴を更新しました")
        else:
            # 新しい履歴を追加
            st.session_state.search_history.append(search_history_item)
            st.success("✅ 新しい検索履歴を追加しました")
        
        # CSVファイルに保存
        self.save_search_history_to_csv()

    def clear_search_history(self):
        """検索履歴をクリア"""
        st.session_state.search_history = []
        # CSVファイルを削除
        if os.path.exists('search_history.csv'):
            try:
                os.remove('search_history.csv')
                st.success("検索履歴をクリアしました。")
            except Exception as e:
                st.error(f"検索履歴のクリアに失敗しました: {e}")

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
        if not self.tokenizer or not text:
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
        if not keywords:
            return None
        
        # WordCloudライブラリの利用可能性をチェック
        try:
            from wordcloud import WordCloud
            import matplotlib.pyplot as plt
            import matplotlib.font_manager as fm
            import numpy as np
        except ImportError:
            st.warning("⚠️ WordCloudライブラリがインストールされていません。ワードクラウド機能は無効です。")
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
            
            # デバッグ情報を表示
            st.write(f"📊 検索結果の日付範囲: {min(dates_df['日付'])} 〜 {max(dates_df['日付'])}")
            st.write(f"📊 総日数: {len(dates_df)}日")
            
            # 日付を年月に変換（より確実な方法）
            dates_df['年月'] = dates_df['日付'].dt.strftime('%Y-%m')
            monthly_counts = dates_df.groupby('年月').size().reset_index(name='件数')
            
            # データが複数月にわたる場合のみ表示
            if len(monthly_counts) > 1:
                # 年月でソート
                monthly_counts = monthly_counts.sort_values('年月')
                
                fig = px.line(monthly_counts, x='年月', y='件数', 
                             title='月別発言件数の推移',
                             markers=True)
                fig.update_layout(
                    height=400,
                    xaxis_title="年月",
                    yaxis_title="発言件数"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 時系列分析には複数月のデータが必要です。現在の検索結果は1ヶ月のみです。")
                
                # 1ヶ月のみの場合でも、日別の推移を表示
                st.subheader("📅 日別発言件数の推移")
                daily_counts = dates_df.groupby('日付').size().reset_index(name='件数')
                daily_counts = daily_counts.sort_values('日付')
                
                fig = px.line(daily_counts, x='日付', y='件数', 
                             title='日別発言件数の推移',
                             markers=True)
                fig.update_layout(
                    height=400,
                    xaxis_title="日付",
                    yaxis_title="発言件数"
                )
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

    def search_page(self):
        st.markdown('<h2 class="sub-header">🔍 国会議事録検索</h2>', unsafe_allow_html=True)
        
        # 復元された検索条件を取得
        restored_params = st.session_state.get('re_search_params', {})
        auto_search = st.session_state.get('auto_search', False)
        
        # 復元された条件がある場合は表示
        if restored_params:
            if auto_search:
                st.info("📋 検索履歴から復元された条件で自動検索を実行します。")
            else:
                st.info("📋 検索履歴から復元された条件が設定されています。")
            # 復元された条件をセッション状態に保存
            st.session_state['current_search_params'] = restored_params
            # 復元された条件をクリア
            del st.session_state['re_search_params']
            # 自動検索フラグをクリア
            if auto_search:
                del st.session_state['auto_search']
        
        # 現在の検索条件を取得（復元された条件または保存された条件）
        current_params = st.session_state.get('current_search_params', {})
        
        # 検索フォーム
        with st.form("search_form"):
            # 復元された条件または保存された条件を設定
            default_keyword = current_params.get("any", "")
            default_speaker = current_params.get("speaker", "")
            default_meeting = current_params.get("nameOfMeeting", "")
            default_house = current_params.get("nameOfHouse", "指定しない")
            
            keyword = st.text_input("🔎 検索キーワード（AND検索）", 
                                  value=default_keyword,
                                  placeholder="例：デジタル改革 規制緩和",
                                  help="複数のキーワードをスペースで区切って入力")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                speaker = st.text_input("👤 発言者名", 
                                      value=default_speaker,
                                      placeholder="例：岸田文雄")
            with col2:
                name_of_meeting = st.text_input("🏛️ 会議名", 
                                              value=default_meeting,
                                              placeholder="例：予算委員会")
            with col3:
                # 院名の選択肢を設定
                house_options = ("指定しない", "衆議院", "参議院", "両院")
                house_index = 0
                if default_house in house_options:
                    house_index = house_options.index(default_house)
                name_of_house = st.selectbox("🏢 院名", house_options, index=house_index)
            
            col4, col5 = st.columns(2)
            with col4:
                # 日付の復元
                from_date_str = current_params.get("from", "")
                from_date = None
                if from_date_str:
                    try:
                        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                    except:
                        from_date = None
                from_date = st.date_input("📅 検索期間（開始日）", value=from_date)
            with col5:
                until_date_str = current_params.get("until", "")
                until_date = None
                if until_date_str:
                    try:
                        until_date = datetime.strptime(until_date_str, '%Y-%m-%d').date()
                    except:
                        until_date = None
                until_date = st.date_input("📅 検索期間（終了日）", value=until_date)
            
            search_button = st.form_submit_button("🔍 検索実行", type="primary")
        
        # 自動検索フラグがある場合は自動的に検索を実行
        if auto_search and current_params:
            search_button = True
            # 自動検索の場合は検索パラメータを構築
            search_params = current_params.copy()
        elif search_button:
            # 通常の検索ボタンが押された場合
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
        
        # 既存の検索結果がある場合は表示
        if st.session_state.search_results and not (search_button or (auto_search and current_params)):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.success(f"📊 前回の検索結果が表示されています。")
            with col2:
                if st.button("🗑️ 検索結果をクリア", type="secondary"):
                    st.session_state.search_results = None
                    st.session_state.analytics_data = {}
                    if 'meeting_analysis' in st.session_state:
                        del st.session_state.meeting_analysis
                    st.rerun()
            
            data = st.session_state.search_results
            current_keyword = st.session_state.get('current_search_params', {}).get('any', '')
            
            # エクスポート機能
            export_df = self.export_results(data, st.session_state.get('current_search_params', {}))
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
                    highlighted_speech = self.highlight_text(speech_text, current_keyword)
                    
                    st.markdown(
                        f'<div class="speech-card" style="height: 300px; overflow-y: auto;">{highlighted_speech}</div>',
                        unsafe_allow_html=True
                    )
                    
                    st.markdown(f"🔗 [発言の全文と周辺議事を読む]({record['speechURL']})")
        
        if search_button or (auto_search and current_params):
            # 自動検索の場合は既にsearch_paramsが設定されている
            if not auto_search:
                # 通常の検索ボタンが押された場合のパラメータ構築
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

            # 検索パラメータが空でないかチェック
            if search_params:
                # デバッグ情報を表示
                st.write(f"🔍 検索パラメータ: {search_params}")
                
                # 検索条件をセッション状態に保存
                st.session_state['current_search_params'] = search_params
                
                with st.spinner("🔍 検索中です..."):
                    time.sleep(1)
                    data = self.search_speeches(search_params)
                    
                    if data and "speechRecord" in data and data["speechRecord"]:
                        st.session_state.search_results = data
                        st.session_state.analytics_data = self.analyze_search_results(data)
                        
                        # janome利用可能な場合のみキーワード分析を実行
                        if self.tokenizer:
                            st.session_state.meeting_analysis = self.analyze_meeting_keywords(data)
                        
                        # 検索履歴に追加
                        self.add_to_search_history(search_params, data['numberOfRecords'])
                        
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
        
        if not self.tokenizer:
            st.error("❌ この機能を使用するには janome ライブラリが必要です。")
            st.code("pip install janome")
            return
        
        if 'meeting_analysis' not in st.session_state or not st.session_state.meeting_analysis:
            st.info("🔍 分析データがありません。まず検索を実行してください。")
            return
        
        meeting_analysis = st.session_state.meeting_analysis
        
        # 会議選択（すべての会議オプションを追加）
        meeting_options = ["すべての会議"] + list(meeting_analysis.keys())
        selected_meeting = st.selectbox(
            "📋 分析する会議を選択してください",
            meeting_options,
            index=0,  # デフォルトで「すべての会議」を選択
            help="検索結果に含まれる会議から選択"
        )
        
        if selected_meeting:
            if selected_meeting == "すべての会議":
                # すべての会議のデータを統合
                all_keywords = {}
                all_speakers = set()
                total_speeches = 0
                total_characters = 0
                
                for meeting_name, meeting_data in meeting_analysis.items():
                    # キーワードを統合
                    for keyword, count in meeting_data['keywords'].items():
                        if keyword in all_keywords:
                            all_keywords[keyword] += count
                        else:
                            all_keywords[keyword] = count
                    
                    # 発言者を統合
                    all_speakers.update(meeting_data['speakers'])
                    total_speeches += meeting_data['total_speeches']
                    total_characters += meeting_data['total_characters']
                
                # 統合されたデータを作成
                meeting_data = {
                    'keywords': dict(sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)),
                    'speakers': list(all_speakers),
                    'total_speeches': total_speeches,
                    'total_characters': total_characters,
                    'speeches': []  # 全発言データは重複する可能性があるため空にする
                }
            else:
                meeting_data = meeting_analysis[selected_meeting]
            
            # 会議の基本情報
            if selected_meeting == "すべての会議":
                st.markdown("### 📊 全会議基本情報")
            else:
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
            if selected_meeting == "すべての会議":
                st.markdown("### 👥 全発言者一覧")
            else:
                st.markdown("### 👥 発言者一覧")
            
            speakers_text = "、".join(meeting_data['speakers'])
            st.write(speakers_text)
            
            st.markdown("---")
            
            # キーワード分析
            if meeting_data['keywords']:
                st.markdown("### 🔤 キーワード分析")
                
                # タブで表示方法を切り替え
                tab1, tab2, tab3 = st.tabs(["🔤 ランキング", "☁️ ワードクラウド", "📈 詳細分析"])
                
                with tab1:
                    # キーワードランキング
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        keywords_df = pd.DataFrame(
                            list(meeting_data['keywords'].items())[:20], 
                            columns=['キーワード', '出現回数']
                        )
                        
                        # タイトルを動的に設定
                        if selected_meeting == "すべての会議":
                            title = "すべての会議 - 主要キーワード Top20"
                        else:
                            title = f"{selected_meeting} - 主要キーワード Top20"
                        
                        fig = px.bar(
                            keywords_df, 
                            x='出現回数', 
                            y='キーワード', 
                            orientation='h',
                            title=title,
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
                    if self.tokenizer:
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
                        st.warning("ワードクラウド機能を使用するには janome ライブラリが必要です。")
                        st.code("pip install janome")
                
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
        
        # クリアボタン
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ 履歴をクリア", type="secondary"):
                self.clear_search_history()
                st.rerun()
        
        if st.session_state.search_history:
            st.write(f"📊 検索履歴: {len(st.session_state.search_history)}件")
            
            for i, item in enumerate(st.session_state.search_history):
                with st.expander(f"🕐 {item['timestamp']} - {item['results_count']}件"):
                    # 検索条件を読みやすい形式で表示
                    params = item.get('params', {})
                    if params:
                        st.markdown("#### 📋 検索条件")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if params.get('any'):
                                st.write(f"**🔎 キーワード:** {params['any']}")
                            if params.get('speaker'):
                                st.write(f"**👤 発言者:** {params['speaker']}")
                            if params.get('nameOfMeeting'):
                                st.write(f"**🏛️ 会議名:** {params['nameOfMeeting']}")
                        
                        with col2:
                            if params.get('nameOfHouse'):
                                st.write(f"**🏢 院名:** {params['nameOfHouse']}")
                            if params.get('from'):
                                st.write(f"**📅 開始日:** {params['from']}")
                            if params.get('until'):
                                st.write(f"**📅 終了日:** {params['until']}")
                        
                        # 詳細なJSONも表示（折りたたみ）
                        with st.expander("📄 詳細データ（JSON）"):
                            st.json(params)
                    else:
                        st.warning("検索条件の詳細がありません。")
                    
                    # 再検索ボタン
                    if st.button(f"🔍 この条件で再検索", key=f"re_search_{i}"):
                        # 検索条件を復元して検索ページに移動
                        if params:  # 検索条件が存在する場合のみ
                            st.session_state.re_search_params = item['params']
                            st.session_state.auto_search = True  # 自動検索フラグを設定
                            st.session_state.current_page = "🔍 検索"  # 検索ページに移動
                            st.success("検索条件を復元しました。自動的に検索を実行します。")
                            # 検索ページに自動的に移動
                            st.rerun()
                        else:
                            st.error("検索条件が空のため、再検索できません。")
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
