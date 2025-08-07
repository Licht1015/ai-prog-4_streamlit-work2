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

def main():
    # ヘッダー
    st.markdown('<h1 class="main-header">🏛️ 国会議事録検索・分析アプリ</h1>', unsafe_allow_html=True)
    
    # サイドバー表示
    page = show_sidebar()
    
    # アプリケーション初期化
    app = KokkaiSearchApp()
    
    # ページ分岐
    if page == "🔍 検索":
        app.search_page()
    elif page == "📊 分析":
        app.analysis_page()
    elif page == "🏛️ 会議別キーワード分析" and JANOME_AVAILABLE:
        app.meeting_analysis_page()
    elif page == "📚 検索履歴":
        app.history_page()
    else:
        app.help_page()

if __name__ == "__main__":
    main()
