# app/main.py
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

from components import show_sidebar
from logic import KokkaiSearchApp

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

def load_search_history():
    """CSVファイルから検索履歴を読み込む"""
    csv_file = 'search_history.csv'
    if os.path.exists(csv_file):
        try:
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            # CSVから辞書のリストに変換
            history_list = []
            for _, row in df.iterrows():
                # paramsカラムをJSONから辞書に変換
                params_str = row.get('params', '{}')
                try:
                    params = json.loads(params_str) if isinstance(params_str, str) else params_str
                except:
                    params = {}
                
                history_item = {
                    'timestamp': row.get('timestamp', ''),
                    'params': params,
                    'results_count': row.get('results_count', 0)
                }
                history_list.append(history_item)
            return history_list
        except Exception as e:
            st.warning(f"検索履歴の読み込みに失敗しました: {e}")
            return []
    return []

def main():
    # 検索履歴をCSVから読み込み
    if 'search_history' not in st.session_state:
        st.session_state.search_history = load_search_history()
    
    # ヘッダー
    st.markdown('<h1 class="main-header">🏛️ 国会議事録検索・分析アプリ</h1>', unsafe_allow_html=True)
    
    # サイドバー表示
    page = show_sidebar()
    
    # アプリケーション初期化
    app = KokkaiSearchApp()
    
    # セッション状態からページを取得（再検索時の自動移動用）
    current_page = st.session_state.get('current_page', page)
    
    # ページ分岐
    if current_page == "🔍 検索":
        app.search_page()
    elif current_page == "📊 分析":
        app.analysis_page()
    elif current_page == "🏛️ 会議別キーワード分析" and JANOME_AVAILABLE:
        app.meeting_analysis_page()
    elif current_page == "📚 検索履歴":
        app.history_page()
    else:
        app.help_page()

if __name__ == "__main__":
    main()
