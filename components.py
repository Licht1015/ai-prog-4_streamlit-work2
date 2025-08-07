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
        
        # セッション状態から現在のページを取得
        current_page = st.session_state.get('current_page', "🔍 検索")
        
        # ページ選択のデフォルト値を設定
        default_index = 0
        if current_page in page_options:
            default_index = page_options.index(current_page)
        
        page = st.selectbox("ページを選択", page_options, index=default_index)
        
        # ページが変更された場合はセッション状態を更新
        if page != current_page:
            st.session_state['current_page'] = page
        
        return page
