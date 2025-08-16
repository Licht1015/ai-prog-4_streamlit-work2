# 国会議事録検索・分析アプリケーション

## 📋 アプリケーション概要

このアプリケーションは、国会議事録APIを活用した検索・分析ツールです。ユーザーはキーワード、期間、発言者などの条件を指定して国会議事録を検索し、結果を分析・可視化することができます。

### 主要機能
- 🔍 **高度な検索機能**: キーワード、期間、発言者による検索
- 📊 **統計分析**: 発言者別・会議別・日付別の統計
- 🏛️ **キーワード分析**: 形態素解析によるキーワード抽出とワードクラウド生成
- 📚 **検索履歴管理**: CSVファイルによる履歴保存
- 📈 **データ可視化**: インタラクティブなグラフとチャート

### 使用しているAPI
- **国会議事録API**: https://kokkai.ndl.go.jp/api/speech
  - APIキー不要の公開API
  - JSON形式で議事録データを取得
  - 検索パラメータ: keyword, from, until, speaker, meeting

## 🏗️ システム設計図

![システム設計図](sys.drawio.png)

```mermaid
graph TB
    subgraph "ユーザー層"
        U[ユーザー]
    end
    
    subgraph "プレゼンテーション層"
        ST[Streamlit Web UI]
        SB[サイドバー]
        PG[ページ管理]
    end
    
    subgraph "アプリケーション層"
        MAIN[main.py]
        COMP[components.py]
        LOGIC[logic.py]
    end
    
    subgraph "ビジネスロジック層"
        KSA[KokkaiSearchApp]
        SEARCH[検索機能]
        ANALYTICS[分析機能]
        HISTORY[履歴管理]
    end
    
    subgraph "データ処理層"
        PD[Pandas]
        PL[Plotly]
        JN[Janome]
        WC[WordCloud]
    end
    
    subgraph "外部サービス"
        API[国会議事録API<br/>https://kokkai.ndl.go.jp/api/speech]
    end
    
    subgraph "データストレージ"
        CSV[search_history.csv]
        SESSION[Session State]
    end
    
    U --> ST
    ST --> SB
    ST --> PG
    ST --> MAIN
    MAIN --> COMP
    MAIN --> LOGIC
    LOGIC --> KSA
    KSA --> SEARCH
    KSA --> ANALYTICS
    KSA --> HISTORY
    SEARCH --> API
    ANALYTICS --> PD
    ANALYTICS --> PL
    ANALYTICS --> JN
    ANALYTICS --> WC
    HISTORY --> CSV
    KSA --> SESSION
    
    style U fill:#e1f5fe
    style ST fill:#f3e5f5
    style MAIN fill:#e8f5e8
    style LOGIC fill:#fff3e0
    style API fill:#ffebee
    style CSV fill:#f1f8e9
```

## 📁 コード説明図

![コード説明図](code.drawio.png)

```mermaid
graph LR
    subgraph "メインファイル"
        MAIN[main.py<br/>313行<br/>エントリーポイント]
    end
    
    subgraph "UIコンポーネント"
        COMP[components.py<br/>157行<br/>UI管理]
    end
    
    subgraph "ビジネスロジック"
        LOGIC[logic.py<br/>1198行<br/>コアロジック]
    end
    
    subgraph "KokkaiSearchAppクラス"
        INIT[__init__<br/>初期化]
        SEARCH[search_speeches<br/>API通信]
        ANALYZE[analyze_search_results<br/>データ分析]
        VISUALIZE[create_visualizations<br/>可視化]
        HISTORY[add_to_search_history<br/>履歴管理]
        EXPORT[export_results<br/>データ出力]
    end
    
    subgraph "主要メソッド"
        SEARCH_PAGE[search_page<br/>検索ページ]
        ANALYSIS_PAGE[analysis_page<br/>分析ページ]
        MEETING_PAGE[meeting_analysis_page<br/>会議分析]
        HISTORY_PAGE[history_page<br/>履歴ページ]
        HELP_PAGE[help_page<br/>ヘルプページ]
    end
    
    subgraph "データ処理"
        EXTRACT[extract_keywords<br/>キーワード抽出]
        WORDCLOUD[create_wordcloud<br/>ワードクラウド]
        HIGHLIGHT[highlight_text<br/>テキスト強調]
    end
    
    subgraph "外部ライブラリ"
        ST[streamlit<br/>Web UI]
        REQ[requests<br/>HTTP通信]
        PD[pandas<br/>データ処理]
        PL[plotly<br/>可視化]
        JN[janome<br/>形態素解析]
        WC[wordcloud<br/>ワードクラウド]
    end
    
    MAIN --> COMP
    MAIN --> LOGIC
    COMP --> LOGIC
    LOGIC --> INIT
    LOGIC --> SEARCH
    LOGIC --> ANALYZE
    LOGIC --> VISUALIZE
    LOGIC --> HISTORY
    LOGIC --> EXPORT
    
    SEARCH --> SEARCH_PAGE
    ANALYZE --> ANALYSIS_PAGE
    ANALYZE --> MEETING_PAGE
    HISTORY --> HISTORY_PAGE
    LOGIC --> HELP_PAGE
    
    EXTRACT --> JN
    WORDCLOUD --> WC
    SEARCH --> REQ
    ANALYZE --> PD
    VISUALIZE --> PL
    COMP --> ST
    
    style MAIN fill:#e8f5e8
    style COMP fill:#e3f2fd
    style LOGIC fill:#fff3e0
    style INIT fill:#f3e5f5
    style SEARCH fill:#e1f5fe
    style ANALYZE fill:#f1f8e9
    style VISUALIZE fill:#fff8e1
    style HISTORY fill:#fce4ec
    style EXPORT fill:#e0f2f1
```

## 🚀 セットアップと実行

### 必要な環境
- Python 3.8+
- Anaconda（推奨）

### インストール手順
```bash
# 依存関係のインストール
pip install -r requirements.txt

# アプリケーションの起動
streamlit run main.py
```

### オプション機能の有効化
```bash
# 形態素解析機能（キーワード分析）
pip install janome

# ワードクラウド機能
pip install wordcloud matplotlib
```

## 📊 機能詳細

### 検索機能
- キーワード検索
- 期間指定（開始日〜終了日）
- 発言者名指定
- 会議名指定
- 最大取得件数設定

### 分析機能
- 発言者別統計
- 会議別統計
- 日付別統計
- キーワード頻度分析
- ワードクラウド生成

### データ管理
- 検索履歴の自動保存
- CSV形式での履歴エクスポート
- セッション状態の管理

## 🔧 技術仕様

### アーキテクチャ
- **フロントエンド**: Streamlit
- **バックエンド**: Python
- **データ処理**: Pandas, NumPy
- **可視化**: Plotly
- **自然言語処理**: Janome（オプション）
- **データストレージ**: CSVファイル

### パフォーマンス
- 検索実行: 5秒以内
- ページ表示: 2秒以内
- グラフ生成: 3秒以内

## 📝 開発情報

- **課題**: Streamlitを使ったアプリの開発 + 公開
- **学籍番号**: 22060015
- **作成日**: 2025年8月
- **バージョン**: 1.1.0

## 🔗 関連リンク

- **国会議事録API**: https://kokkai.ndl.go.jp/api/speech
- **Streamlit**: https://diet-record-search-and-analysis.streamlit.app/
