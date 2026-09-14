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
    """Enrichment respects the CRYPTOPRED_USE_SENTIMENT gate (default off)."""
    import pandas as pd, numpy as np
    from crypto_prediction.config import get_config
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
    if not get_config().features.use_sentiment:
        # Feature off by default: input passes through untouched
        assert enriched is not None and len(enriched) == len(df)
        print("Sentiment disabled (default) - passthrough OK")
    else:
        # Enabled: enrichment must never crash, even with no network
        assert enriched is not None and len(enriched) == len(df)
        print(f"Sentiment enabled - columns added: "
              f"{[c for c in enriched.columns if c.startswith('Sentiment')]}")

if __name__ == "__main__":
    test_lexicon()
    test_analyzer()
    test_feature_engineer()
