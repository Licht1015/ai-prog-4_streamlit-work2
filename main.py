# =============================================================================
# 国会議事録検索・分析アプリケーション - メインファイル
# =============================================================================
# 
# 概要:
# このファイルは国会議事録検索・分析アプリケーションのエントリーポイントです。
# Streamlitを使用してWebアプリケーションを構築し、国会議事録APIを活用した
# 検索・分析機能を提供します。
# 
# 課題2: Streamlitを使ったアプリの開発 + 公開
# 学籍番号: [学籍番号]
# 作成者: [名前]
# 作成日: 2024年8月
# 
# 主要機能:
# - 国会議事録の高度な検索機能
# - 検索結果の統計分析・可視化
# - キーワード分析・ワードクラウド生成
# - 検索履歴の管理・保存
# 
# 依存関係:
# - streamlit: Webアプリケーションフレームワーク
# - requests: HTTP通信
# - pandas: データ処理
# - plotly: データ可視化
# - janome: 日本語形態素解析（オプション）
# - wordcloud: ワードクラウド生成（オプション）
# 
# 開発環境:
# - Anaconda仮想環境
# - Python 3.8+
# - Streamlit Cloud（デプロイ先）
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
# 各ライブラリの利用可能性をチェックし、適切な警告を表示します。

# Janome（日本語形態素解析）の条件付きインポート
try:
    from janome.tokenizer import Tokenizer
    st.success("✅ Janomeライブラリが正常に読み込まれました。形態素解析機能が利用可能です。")
except ImportError:
    st.warning("⚠️ Janomeライブラリがインストールされていません。形態素解析機能は無効です。")
    st.info("💡 形態素解析機能を有効にするには: pip install janome")

# WordCloud（ワードクラウド生成）の条件付きインポート
try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import numpy as np
    st.success("✅ WordCloudライブラリが正常に読み込まれました。ワードクラウド機能が利用可能です。")
except ImportError:
    st.warning("⚠️ WordCloudライブラリがインストールされていません。ワードクラウド機能は無効です。")
    st.info("💡 ワードクラウド機能を有効にするには: pip install wordcloud matplotlib")

# =============================================================================
# ローカルモジュールのインポート
# =============================================================================
from components import show_sidebar
from logic import KokkaiSearchApp

# =============================================================================
# アプリケーション設定
# =============================================================================
# 
# ページ設定:
# - page_title: ブラウザタブに表示されるタイトル
# - page_icon: ブラウザタブに表示されるアイコン
# - layout: レイアウトモード（"wide"で横幅を最大活用）
# - initial_sidebar_state: サイドバーの初期状態

st.set_page_config(
    page_title="国会議事録検索アプリ",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# カスタムCSSスタイル定義
# =============================================================================
# 
# 説明:
# アプリケーションの見た目を改善するためのカスタムCSSを定義します。
# 各クラスは特定のUI要素のスタイリングに使用されます。

st.markdown("""
<style>
    /* メインヘッダーのスタイル */
    .main-header {
        font-size: 3rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        font-weight: bold;
    }
    
    /* サブヘッダーのスタイル */
    .sub-header {
        font-size: 1.5rem;
        color: #2e6da4;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    /* ハイライトボックスのスタイル */
    .highlight-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* メトリックカードのスタイル */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f4e79;
        margin: 10px 0;
    }
    
    /* 発言カードのスタイル */
    .speech-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #17a2b8;
        transition: all 0.3s ease;
    }
    
    .speech-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# ユーティリティ関数
# =============================================================================

def load_search_history():
    """
    検索履歴をCSVファイルから読み込む関数
    
    機能:
    - search_history.csvファイルから検索履歴を読み込み
    - JSON形式で保存されたパラメータを辞書形式に変換
    - エラーハンドリングによる安全な読み込み
    
    戻り値:
    - list: 検索履歴のリスト（辞書形式）
    
    エラー処理:
    - ファイルが存在しない場合: 空のリストを返す
    - 読み込みエラーの場合: 警告を表示して空のリストを返す
    """
    csv_file = 'search_history.csv'
    if os.path.exists(csv_file):
        try:
            # CSVファイルをUTF-8エンコーディングで読み込み
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            
            # CSVから辞書のリストに変換
            history_list = []
            for _, row in df.iterrows():
                # paramsカラムをJSONから辞書に変換
                params_str = row.get('params', '{}')
                try:
                    params = json.loads(params_str) if isinstance(params_str, str) else params_str
                except json.JSONDecodeError:
                    # JSON解析エラーの場合は空の辞書を使用
                    params = {}
                
                # 履歴アイテムを作成
                history_item = {
                    'timestamp': row.get('timestamp', ''),
                    'params': params,
                    'results_count': row.get('results_count', 0)
                }
                history_list.append(history_item)
            
            st.success(f"✅ 検索履歴を正常に読み込みました（{len(history_list)}件）")
            return history_list
            
        except Exception as e:
            st.warning(f"⚠️ 検索履歴の読み込みに失敗しました: {e}")
            return []
    else:
        st.info("ℹ️ 検索履歴ファイルが見つかりません。新しい履歴から開始します。")
        return []

# =============================================================================
# メイン関数
# =============================================================================

def main():
    """
    アプリケーションのメイン関数
    
    機能:
    - アプリケーションの初期化
    - 検索履歴の読み込み
    - ページルーティング
    - セッション状態の管理
    
    フロー:
    1. 検索履歴の初期化
    2. ヘッダー表示
    3. サイドバー表示
    4. アプリケーション初期化
    5. ページ分岐処理
    """
    
    # =====================================================================
    # セッション状態の初期化
    # =====================================================================
    
    # 検索履歴をCSVから読み込み（初回のみ）
    if 'search_history' not in st.session_state:
        st.session_state.search_history = load_search_history()
    
    # =====================================================================
    # ヘッダー表示
    # =====================================================================
    
    st.markdown('<h1 class="main-header">🏛️ 国会議事録検索・分析アプリ</h1>', unsafe_allow_html=True)
    
    # =====================================================================
    # サイドバー表示とページ選択
    # =====================================================================
    
    page = show_sidebar()
    
    # =====================================================================
    # アプリケーション初期化
    # =====================================================================
    
    app = KokkaiSearchApp()
    
    # =====================================================================
    # ページ分岐処理
    # =====================================================================
    
    # セッション状態からページを取得（再検索時の自動移動用）
    current_page = st.session_state.get('current_page', page)
    
    # ページに応じた処理の分岐
    if current_page == "🔍 検索":
        st.info("🔍 検索ページを表示しています...")
        app.search_page()
        
    elif current_page == "📊 分析":
        st.info("📊 分析ページを表示しています...")
        app.analysis_page()
        
    elif current_page == "🏛️ 会議別キーワード分析":
        # Janomeライブラリの利用可能性をチェック
        try:
            from janome.tokenizer import Tokenizer
            st.info("🏛️ 会議別キーワード分析ページを表示しています...")
            app.meeting_analysis_page()
        except ImportError:
            st.error("❌ キーワード分析機能は利用できません。Janomeライブラリがインストールされていません。")
            st.info("💡 キーワード分析機能を有効にするには: pip install janome")
            # 検索ページにリダイレクト
            st.session_state['current_page'] = "🔍 検索"
            st.rerun()
        
    elif current_page == "📚 検索履歴":
        st.info("📚 検索履歴ページを表示しています...")
        app.history_page()
        
    else:
        st.info("ℹ️ ヘルプページを表示しています...")
        app.help_page()

# =============================================================================
# アプリケーションエントリーポイント
# =============================================================================

if __name__ == "__main__":
    """
    アプリケーションのエントリーポイント
    
    実行方法:
    - 直接実行: python main.py
    - Streamlit実行: streamlit run main.py
    
    注意事項:
    - Streamlitアプリケーションとして実行することを推奨
    - デバッグ時は直接実行も可能
    """
    main()
