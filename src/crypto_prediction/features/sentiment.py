"""
Sentiment analysis for crypto: News, Reddit, Twitter
- Lexicon-based VADER-like (no external deps)
- Optional FinBERT integration if transformers available
- Aggregates daily sentiment score to merge with price features
"""
import re
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests
from pathlib import Path

from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

# ---------- Lexicon based sentiment (VADER-inspired, lightweight) ----------
POSITIVE_WORDS = {
    "bullish": 3, "moon": 3, "pump": 2, "buy": 2, "long": 1, "up": 1, "rise": 2, "rising": 2,
    "gain": 2, "gains": 2, "profit": 2, "surge": 3, "rally": 3, "breakout": 2, "support": 1,
    "strong": 2, "growth": 2, "optimistic": 2, "positive": 2, "good": 1, "great": 2,
    "excellent": 3, "amazing": 3, "awesome": 2, "love": 2, "hodl": 2, "accumulate": 2,
    "adoption": 2, "partnership": 2, "launch": 1, "upgrade": 1
}
NEGATIVE_WORDS = {
    "bearish": -3, "crash": -3, "dump": -3, "sell": -2, "short": -1, "down": -1, "fall": -2,
    "falling": -2, "loss": -2, "losses": -2, "fear": -2, "panic": -3, "drop": -2, "plunge": -3,
    "correction": -1, "resistance": -1, "weak": -2, "decline": -2, "negative": -2, "bad": -1,
    "terrible": -3, "awful": -3, "hate": -2, "scam": -3, "fraud": -3, "hack": -3, "ban": -2,
    "regulation": -1, "lawsuit": -2, "bear": -2
}
BOOSTERS = {"very": 1.5, "extremely": 2.0, "really": 1.5, "super": 1.8, "absolutely": 2.0}

class LexiconSentiment:
    def __init__(self):
        self.pos = POSITIVE_WORDS
        self.neg = NEGATIVE_WORDS

    def score_text(self, text: str) -> Dict[str, float]:
        if not text:
            return {"compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 1.0}
        text = text.lower()
        words = re.findall(r"\b\w+\b", text)
        scores = []
        for i, w in enumerate(words):
            score = 0
            if w in self.pos:
                score = self.pos[w]
            elif w in self.neg:
                score = self.neg[w]
            if score != 0 and i > 0 and words[i-1] in BOOSTERS:
                score *= BOOSTERS[words[i-1]]
            if score != 0:
                scores.append(score)
        
        if not scores:
            return {"compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 1.0}
        
        # Compound normalized to [-1,1]
        sum_s = sum(scores)
        compound = sum_s / np.sqrt(sum_s**2 + 15)  # normalization similar to VADER
        pos_count = sum(1 for s in scores if s > 0)
        neg_count = sum(1 for s in scores if s < 0)
        total = len(scores)
        return {
            "compound": float(np.clip(compound, -1, 1)),
            "pos": pos_count / total,
            "neg": neg_count / total,
            "neu": 1 - (pos_count + neg_count) / total if total else 1.0
        }

# Optional FinBERT wrapper (lazy import)
class FinBERTSentiment:
    def __init__(self):
        self.enabled = False
        try:
            from transformers import pipeline
            self.pipe = pipeline("sentiment-analysis", model="ProsusAI/finbert")
            self.enabled = True
            logger.info("FinBERT loaded")
        except Exception as e:
            logger.warning(f"FinBERT not available: {e}")

    def score_text(self, text: str) -> Dict[str, float]:
        if not self.enabled:
            return {"compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 1.0}
        try:
            res = self.pipe(text[:512])[0]
            label = res['label'].lower()
            score = res['score']
            if "positive" in label:
                return {"compound": score, "pos": score, "neg": 0, "neu": 1-score}
            elif "negative" in label:
                return {"compound": -score, "pos": 0, "neg": score, "neu": 1-score}
            else:
                return {"compound": 0.0, "pos": 0, "neg": 0, "neu": 1.0}
        except Exception as e:
            logger.warning(f"FinBERT scoring failed: {e}")
            return {"compound": 0.0, "pos": 0, "neg": 0, "neu": 1.0}

class SentimentAnalyzer:
    def __init__(self, use_finbert: bool = False):
        self.lexicon = LexiconSentiment()
        self.finbert = FinBERTSentiment() if use_finbert and config.sentiment.use_finbert else None

    def analyze(self, text: str) -> Dict[str, float]:
        lex = self.lexicon.score_text(text)
        if self.finbert and self.finbert.enabled:
            fin = self.finbert.score_text(text)
            # ensemble
            compound = 0.6*lex['compound'] + 0.4*fin['compound']
            return {"compound": compound, "lexicon": lex, "finbert": fin}
        return lex

    def analyze_batch(self, texts: List[str]) -> pd.DataFrame:
        results = []
        for t in texts:
            s = self.analyze(t)
            results.append(s)
        df = pd.DataFrame(results)
        return df

# ---------- Data Fetchers ----------
class NewsFetcher:
    def __init__(self):
        self.cryptopanic_key = config.sentiment.cryptopanic_key
        self.newsapi_key = config.sentiment.newsapi_key

    def fetch_cryptopanic(self, symbol: str = "BTC", limit: int = 50) -> List[Dict]:
        """Fetch news from CryptoPanic (free tier)"""
        try:
            url = "https://cryptopanic.com/api/v1/posts/"
            params = {
                "auth_token": self.cryptopanic_key or "free",
                "currencies": symbol.split("-")[0],
                "kind": "news",
                "public": "true"
            }
            # If no key, try without auth (limited)
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                posts = data.get('results', [])[:limit]
                return [{"title": p.get('title',''), "published_at": p.get('published_at'), "source": "cryptopanic", "url": p.get('url')} for p in posts]
        except Exception as e:
            logger.warning(f"CryptoPanic fetch failed: {e}")
        return []

    def fetch_coingecko_news(self, limit: int = 20) -> List[Dict]:
        """Fallback: use CoinGecko trending as pseudo-news sentiment proxy"""
        try:
            # Use CoinGecko global news is not available, so we simulate with status updates
            # Instead fetch Bitcoin market chart sentiment via community data
            url = "https://api.coingecko.com/api/v3/search/trending"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                coins = data.get('coins', [])
                news = []
                for c in coins[:limit]:
                    item = c.get('item', {})
                    news.append({
                        "title": f"{item.get('name','')} trending with score {item.get('score',0)}",
                        "published_at": datetime.utcnow().isoformat(),
                        "source": "coingecko_trending",
                        "url": ""
                    })
                return news
        except Exception as e:
            logger.warning(f"CoinGecko trending fetch failed: {e}")
        return []

    def fetch(self, symbol: str = "BTC-USD", limit: int = 50) -> List[Dict]:
        news = self.fetch_cryptopanic(symbol=symbol, limit=limit)
        if not news:
            news = self.fetch_coingecko_news(limit=limit)
        if not news:
            # synthetic fallback for offline demo
            logger.info("Using synthetic news fallback")
            now = datetime.utcnow()
            samples = [
                f"{symbol} shows bullish momentum as traders accumulate",
                f"{symbol} faces resistance but strong support holds",
                f"Analysts optimistic about {symbol} adoption growth",
                f"{symbol} volume surges amid positive sentiment",
                f"Market correction fears cause {symbol} to drop slightly"
            ]
            news = [{"title": s, "published_at": (now - timedelta(hours=i)).isoformat(), "source": "synthetic", "url": ""} for i, s in enumerate(samples)]
        return news

class RedditFetcher:
    def fetch(self, symbol: str = "BTC", subreddits: List[str] = None, limit: int = 30) -> List[Dict]:
        subreddits = subreddits or ["CryptoCurrency", "Bitcoin", "CryptoMarkets"]
        # If praw available and keys set, use real API
        try:
            if config.sentiment.reddit_client_id and config.sentiment.reddit_secret:
                import praw
                reddit = praw.Reddit(
                    client_id=config.sentiment.reddit_client_id,
                    client_secret=config.sentiment.reddit_secret,
                    user_agent="crypto-prediction/0.1"
                )
                posts = []
                for sub in subreddits[:2]:
                    for submission in reddit.subreddit(sub).search(symbol, limit=limit//2):
                        posts.append({
                            "title": submission.title + " " + (submission.selftext[:200] if submission.selftext else ""),
                            "published_at": datetime.utcfromtimestamp(submission.created_utc).isoformat(),
                            "source": f"reddit_{sub}",
                            "url": submission.url,
                            "score": submission.score
                        })
                return posts
        except Exception as e:
            logger.warning(f"Reddit fetch failed: {e}")

        # synthetic fallback
        now = datetime.utcnow()
        samples = [
            f"Just bought more {symbol} - feeling bullish!",
            f"{symbol} to the moon? What do you think?",
            f"Worried about {symbol} dump, should I sell?",
            f"{symbol} hodl gang, don't panic!",
            f"{symbol} technical analysis shows breakout coming"
        ]
        return [{"title": s, "published_at": (now - timedelta(hours=i*2)).isoformat(), "source": "reddit_synthetic", "url": ""} for i, s in enumerate(samples * 2)][:limit]

# ---------- Aggregator ----------
class SentimentFeatureEngineer:
    def __init__(self, use_finbert: bool = False):
        self.analyzer = SentimentAnalyzer(use_finbert=use_finbert)
        self.news_fetcher = NewsFetcher()
        self.reddit_fetcher = RedditFetcher()

    def get_daily_sentiment(self, symbol: str = "BTC-USD", days: int = 30) -> pd.DataFrame:
        """Aggregate sentiment by day for last N days"""
        # Fetch recent news/reddit
        news = self.news_fetcher.fetch(symbol=symbol, limit=50)
        reddit = self.reddit_fetcher.fetch(symbol=symbol.split("-")[0], limit=30)
        all_items = news + reddit

        if not all_items:
            # return neutral
            dates = pd.date_range(end=datetime.utcnow(), periods=days, freq='D')
            return pd.DataFrame({"date": dates, "sentiment_compound": 0.0, "sentiment_pos": 0.0, "sentiment_neg": 0.0, "sentiment_count": 0}).set_index("date")

        # Score each
        scored = []
        for item in all_items:
            score = self.analyzer.analyze(item['title'])
            dt = pd.to_datetime(item['published_at']) if item.get('published_at') else datetime.utcnow()
            scored.append({
                "date": dt.date(),
                "compound": score.get('compound', 0),
                "pos": score.get('pos', 0),
                "neg": score.get('neg', 0)
            })
        
        df = pd.DataFrame(scored)
        if df.empty:
            return pd.DataFrame()

        # Group by date
        agg = df.groupby('date').agg(
            sentiment_compound=('compound', 'mean'),
            sentiment_pos=('pos', 'mean'),
            sentiment_neg=('neg', 'mean'),
            sentiment_count=('compound', 'count')
        ).reset_index()
        agg['date'] = pd.to_datetime(agg['date'])
        agg.set_index('date', inplace=True)
        agg = agg.sort_index()

        # Reindex to full range
        full_idx = pd.date_range(end=datetime.utcnow(), periods=days, freq='D')
        agg = agg.reindex(full_idx)
        agg['sentiment_compound'] = agg['sentiment_compound'].fillna(0).rolling(3, min_periods=1).mean()
        agg['sentiment_pos'] = agg['sentiment_pos'].fillna(0)
        agg['sentiment_neg'] = agg['sentiment_neg'].fillna(0)
        agg['sentiment_count'] = agg['sentiment_count'].fillna(0)

        return agg

    def enrich_price_df(self, price_df: pd.DataFrame, symbol: str = "BTC-USD") -> pd.DataFrame:
        """Merge sentiment features into price DataFrame"""
        if not config.features.use_sentiment:
            return price_df

        try:
            days = len(price_df)
            sentiment_daily = self.get_daily_sentiment(symbol=symbol, days=min(days, 90))
            if sentiment_daily.empty:
                return price_df

            # Merge asof
            price_df = price_df.copy()
            price_df.index = pd.to_datetime(price_df.index)
            sentiment_daily.index = pd.to_datetime(sentiment_daily.index)

            # Forward fill sentiment to price index
            sentiment_reindexed = sentiment_daily.reindex(price_df.index, method='ffill').fillna(0)
            price_df['Sentiment_Compound'] = sentiment_reindexed['sentiment_compound']
            price_df['Sentiment_Pos'] = sentiment_reindexed['sentiment_pos']
            price_df['Sentiment_Neg'] = sentiment_reindexed['sentiment_neg']
            price_df['Sentiment_Count'] = sentiment_reindexed['sentiment_count']

            # Additional derived
            price_df['Sentiment_MA7'] = price_df['Sentiment_Compound'].rolling(7).mean()
            price_df['Sentiment_Diff'] = price_df['Sentiment_Compound'].diff()

            logger.info(f"Enriched with sentiment: {price_df[['Sentiment_Compound']].tail(3).to_dict()}")
        except Exception as e:
            logger.warning(f"Sentiment enrichment failed: {e}")

        return price_df

def fetch_sentiment(symbol: str = "BTC-USD", days: int = 30) -> pd.DataFrame:
    eng = SentimentFeatureEngineer()
    return eng.get_daily_sentiment(symbol=symbol, days=days)
