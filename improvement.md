# 夏休み課題の改善案

## 📋 現状分析

### 現在のアプリケーション
- **アプリ名**: 国会議事録検索・分析アプリケーション
- **主要機能**: 国会議事録APIを活用した検索・分析ツール
- **技術スタック**: Streamlit + Python + 国会議事録API

### 現状の課題
1. **ユーザー認証機能の欠如**: 個人化された検索履歴や設定の管理ができない
2. **データの永続化不足**: CSVファイルのみで、データベースを使用していない
3. **リアルタイム性の不足**: 最新の議事録情報の即時反映ができない
4. **分析機能の限界**: 基本的な統計分析のみで、高度なAI分析が不足
5. **モバイル対応の不備**: レスポンシブデザインが不完全
6. **デプロイ時の文字化け問題**: Streamlit Cloudでのワードクラウド表示の文字化け

## 🎯 改善案: 「AI議事録アナリスト」

### サービスの立ち位置の見直し

#### Who（誰の課題を解決するか）
- **主要ターゲット**: 政治ジャーナリスト、政策研究者、市民団体
- **副次ターゲット**: 一般市民、学生、メディア関係者

#### What（どんな課題を解決するか）
1. **情報の非対称性**: 国会議事録の膨大な量と複雑さによる情報アクセスの困難
2. **分析の専門性不足**: 一般市民が議事録から重要な情報を抽出する能力の不足
3. **時系列分析の困難**: 政策の変遷や議論の流れを追跡する困難
4. **バイアス検出の困難**: 発言者の立場や偏見を客観的に分析する困難

#### How（どのように解決するか）
1. **AI による自動分析**: GPT-4やClaude等のLLMを活用した議事録の自動要約・分析
2. **感情分析**: 発言者の感情や立場を数値化
3. **政策トレンド分析**: 時系列での政策議論の変化を可視化
4. **バイアス検出**: 発言の偏りや論理的な矛盾を自動検出

## 🚀 システム化に必要な追加実装

### 1. ユーザー認証・管理システム
```python
# 実装予定の機能
- Firebase Authentication による認証
- ユーザープロファイル管理
- 個人設定の保存
- 検索履歴の個人化
```

### 2. データ管理の改善
```python
# JSONファイルベースのデータ管理（DB不要）
import json
from pathlib import Path

class DataManager:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
    
    def save_user_data(self, user_id, data):
        """ユーザーデータをJSONファイルに保存"""
        file_path = self.data_dir / f"user_{user_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_user_data(self, user_id):
        """ユーザーデータをJSONファイルから読み込み"""
        file_path = self.data_dir / f"user_{user_id}.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
```

### 3. AI分析エンジン
```python
# OpenAI API を活用した分析機能
class AIAnalysisEngine:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def summarize_speech(self, speech_text):
        """発言の自動要約"""
        prompt = f"""
        以下の国会議事録発言を要約してください：
        {speech_text}
        
        要約は以下の形式で出力してください：
        - 主要な論点
        - 提案内容
        - 懸念事項
        """
        return self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
    
    def analyze_sentiment(self, speech_text):
        """感情分析"""
        # 実装予定
        pass
    
    def detect_bias(self, speech_text):
        """バイアス検出"""
        # 実装予定
        pass
```

### 4. リアルタイム更新システム
```python
# WebSocket を使用したリアルタイム更新
class RealTimeUpdateService:
    def __init__(self):
        self.websocket_manager = WebSocketManager()
    
    async def check_new_records(self):
        """新しい議事録の定期チェック"""
        # 実装予定
        pass
    
    def notify_users(self, new_data):
        """ユーザーへの通知"""
        # 実装予定
        pass
```

### 5. モバイル対応UI
```python
# Streamlit のモバイル最適化
st.set_page_config(
    page_title="AI議事録アナリスト",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"  # モバイルでサイドバーを折りたたみ
)
```

### 6. ワードクラウド文字化け問題の解決
```python
# Streamlit Cloud での日本語フォント問題の解決策
import os
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import base64
from io import BytesIO

class WordCloudManager:
    def __init__(self):
        self.font_path = self._get_japanese_font()
    
    def _get_japanese_font(self):
        """日本語フォントの取得（デプロイ環境対応）"""
        # Streamlit Cloud環境でのフォント設定
        if os.path.exists('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
            return '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        
        # Google Fonts の Noto Sans JP を使用
        try:
            import urllib.request
            font_url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJK-Regular.otf"
            font_path = "NotoSansCJK-Regular.otf"
            urllib.request.urlretrieve(font_url, font_path)
            return font_path
        except:
            # フォールバック: システムフォント
            return None
    
    def create_wordcloud_image(self, keywords):
        """文字化けしないワードクラウド画像の生成"""
        if not keywords:
            return None
        
        try:
            # WordCloudの設定
            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color='white',
                font_path=self.font_path,
                colormap='viridis',
                max_words=100,
                relative_scaling=0.5,
                random_state=42
            ).generate_from_frequencies(keywords)
            
            # 画像をメモリ上に生成
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            
            # 画像をBase64エンコードして返す
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            st.warning(f"ワードクラウドの生成に失敗しました: {e}")
            return None
    
    def display_wordcloud(self, keywords):
        """Streamlitでワードクラウドを表示"""
        image_base64 = self.create_wordcloud_image(keywords)
        if image_base64:
            st.markdown(
                f'<img src="data:image/png;base64,{image_base64}" style="width:100%;">',
                unsafe_allow_html=True
            )
        else:
            st.warning("ワードクラウドを表示できませんでした。")
```

## 📊 競合分析

### 既存サービス
1. **国会議事録検索システム（国立国会図書館）**
   - 強み: 公式データ、完全性
   - 弱み: 分析機能不足、UI/UX の古さ

2. **政治データベース（各種メディア）**
   - 強み: 専門性、信頼性
   - 弱み: 有料、一般アクセス困難

### 差別化要因
1. **AI による自動分析**: 既存サービスにはない高度な分析機能
2. **無料アクセス**: 一般市民でも利用可能
3. **リアルタイム性**: 最新情報の即時反映
4. **感情分析**: 発言者の立場や感情の数値化

## 🎯 後期開発計画

### Phase 1: 基盤整備（1-2ヶ月）
- ユーザー認証システムの実装
- JSONファイルベースのデータ管理システム
- ワードクラウド文字化け問題の解決
- 基本的なAI分析機能の実装

### Phase 2: 高度な分析機能（2-3ヶ月）
- 感情分析エンジンの開発
- バイアス検出機能の実装
- 政策トレンド分析の実装

### Phase 3: ユーザー体験向上（1-2ヶ月）
- モバイル対応の完全実装
- リアルタイム通知機能
- パーソナライゼーション機能

## 💡 技術的革新点

### 1. マルチモーダル分析
- テキスト分析 + 音声分析（将来）
- 画像認識（資料の自動読み取り）

### 2. 軽量アーキテクチャ
- ファイルベースのキャッシュシステム
- メモリ内データ処理の最適化
- Docker によるコンテナ化

### 3. 機械学習パイプライン
- MLOps によるモデル管理
- A/B テストによる機能改善
- 継続的学習システム

## 📈 期待される効果

### 社会的インパクト
1. **民主主義の深化**: 市民の政治参加の促進
2. **透明性の向上**: 政治プロセスの可視化
3. **教育効果**: 政治教育ツールとしての活用

### 技術的インパクト
1. **AI活用の先例**: 公共データのAI分析のモデルケース
2. **オープンデータ活用**: 政府データの有効活用
3. **市民参加型開発**: オープンソース開発の促進

## 🔮 将来展望

### 5年後のビジョン
- **全国自治体への展開**: 地方議会の分析機能
- **国際展開**: 他国の議会データとの比較分析
- **予測機能**: 政策の将来予測
- **VR/AR対応**: 没入型の議事録体験

### 技術的進化
- **量子コンピューティング**: 大規模データの高速処理
- **脳科学連携**: 認知バイアスの科学的分析
- **ブロックチェーン**: 議事録の改ざん防止

## 📝 まとめ

この改善案は、単なる検索ツールから「AI議事録アナリスト」への進化を目指しています。技術的な革新と社会的な意義を両立させ、民主主義の深化に貢献するアプリケーションの開発を提案します。

特に、AI技術を活用した自動分析機能により、一般市民でも政治の動向を理解しやすくし、より多くの人が政治に参加できる環境を構築することが最大の目標です。

---

**作成者**: [学籍番号_名前]  
**作成日**: 2024年9月  
**バージョン**: 1.0.0
