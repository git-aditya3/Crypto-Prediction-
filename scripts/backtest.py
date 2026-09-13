"""
Backtesting script
Usage: python scripts/backtest.py --symbol BTC-USD --strategy ensemble
"""
import sys
import argparse
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from crypto_prediction.data.fetcher import CryptoDataFetcher
from crypto_prediction.features.technical import FeatureEngineer
from crypto_prediction.backtesting.engine import BacktestEngine
from crypto_prediction.backtesting.strategies import MovingAverageStrategy, RSIStrategy, EnsembleSignalStrategy, PredictionStrategy
from crypto_prediction.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Backtest crypto strategies")
    parser.add_argument("--symbol", type=str, default="BTC-USD")
    parser.add_argument("--strategy", type=str, default="ensemble", choices=["ma","rsi","ensemble","prediction","all"])
    parser.add_argument("--period", type=str, default="2y")
    parser.add_argument("--initial-capital", type=float, default=10000)
    args = parser.parse_args()

    fetcher = CryptoDataFetcher(symbol=args.symbol)
    df = fetcher.load_or_fetch(symbol=args.symbol)
    eng = FeatureEngineer()
    df = eng.engineer(df)

    engine = BacktestEngine(initial_capital=args.initial_capital)

    strategies = []
    if args.strategy == "ma" or args.strategy == "all":
        strategies.append(MovingAverageStrategy(20,50))
    if args.strategy == "rsi" or args.strategy == "all":
        strategies.append(RSIStrategy(30,70))
    if args.strategy == "ensemble" or args.strategy == "all":
        strategies.append(EnsembleSignalStrategy())

    if args.strategy == "prediction":
        # Try to use predictions if models exist
        try:
            from crypto_prediction.prediction.predictor import CryptoPredictor
            predictor = CryptoPredictor(symbol=args.symbol)
            fc = predictor.forecast(steps=len(df), period=args.period)
            import pandas as pd
            if 'ensemble' in fc:
                pred_series = pd.Series(fc['ensemble'], index=pd.to_datetime(fc['dates']))
                df['Predicted'] = pred_series.reindex(df.index, method='ffill').bfill()
                strategies.append(PredictionStrategy(prediction_col="Predicted", threshold=0.01))
        except Exception as e:
            logger.warning(f"Prediction strategy failed: {e}")
            strategies.append(MovingAverageStrategy(20,50))

    results = engine.compare_strategies(df, strategies)

    print(f"\n=== Backtest Results for {args.symbol} ===")
    for name, res in results.items():
        print(f"\n{name}:")
        for k,v in res.metrics.items():
            print(f"  {k}: {v:.2f}" if isinstance(v,float) else f"  {k}: {v}")

if __name__ == "__main__":
    main()
