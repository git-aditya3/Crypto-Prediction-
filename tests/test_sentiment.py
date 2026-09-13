import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from crypto_prediction.features.sentiment import LexiconSentiment, SentimentAnalyzer, SentimentFeatureEngineer

def test_lexicon():
    lex = LexiconSentiment()
    pos = lex.score_text("Bitcoin is bullish and going to the moon! Buy now!")
    neg = lex.score_text("Bitcoin crash, bearish dump, panic sell")
    print(f"Pos: {pos}, Neg: {neg}")
    assert pos['compound'] > 0
    assert neg['compound'] < 0
    print("Lexicon test passed")

def test_analyzer():
    analyzer = SentimentAnalyzer()
    res = analyzer.analyze("BTC is extremely bullish with strong growth")
    assert 'compound' in res
    print(f"Analyzer: {res}")
    print("Analyzer test passed")

def test_feature_engineer():
    import pandas as pd, numpy as np
    dates = pd.date_range('2023-01-01', periods=30)
    df = pd.DataFrame({
        'Open': np.random.rand(30)*100+100,
        'High': np.random.rand(30)*10+110,
        'Low': np.random.rand(30)*10+90,
        'Close': np.random.rand(30)*100+100,
        'Volume': np.random.rand(30)*10000+1000
    }, index=dates)
    eng = SentimentFeatureEngineer()
    enriched = eng.enrich_price_df(df, symbol="BTC-USD")
    assert 'Sentiment_Compound' in enriched.columns
    print("Sentiment enrichment test passed")

if __name__ == "__main__":
    test_lexicon()
    test_analyzer()
    test_feature_engineer()
