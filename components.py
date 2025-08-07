# app/components.py
import streamlit as st

def show_sidebar():
    """サイドバーの表示とページ選択"""
    with st.sidebar:
        st.markdown("### 🔍 検索メニュー")
        page_options = ["🔍 検索", "📊 分析", "📚 検索履歴", "ℹ️ 使い方"]
        
        # janome利用可能な場合のみキーワード分析を追加
        try:
            from janome.tokenizer import Tokenizer
            page_options.insert(2, "🏛️ 会議別キーワード分析")
        except ImportError:
            pass
        
        page = st.selectbox("ページを選択", page_options)
        return page
