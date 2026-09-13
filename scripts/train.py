"""
Training script entry point v2
Usage: python scripts/train.py --symbol BTC-USD --period 2y --models all --use-sentiment
"""
import sys
import argparse
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from crypto_prediction.training.trainer import Trainer
from crypto_prediction.config import get_config
from crypto_prediction.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Train crypto prediction models v2")
    parser.add_argument("--symbol", type=str, default="BTC-USD", help="Crypto symbol e.g. BTC-USD")
    parser.add_argument("--period", type=str, default="2y", help="Data period e.g. 6mo,1y,2y,5y")
    parser.add_argument("--interval", type=str, default="1d", help="Data interval")
    parser.add_argument("--models", type=str, default="all", choices=["all","lstm","transformer","xgboost","arima","ensemble"], help="Which models to train")
    parser.add_argument("--epochs", type=int, default=None, help="Epochs override for DL models")
    parser.add_argument("--force-refresh", action="store_true", help="Force refetch data")
    parser.add_argument("--use-sentiment", action="store_true", default=True, help="Use sentiment enrichment")
    parser.add_argument("--no-sentiment", action="store_true", help="Disable sentiment")
    args = parser.parse_args()

    use_sentiment = args.use_sentiment and not args.no_sentiment

    config = get_config()
    logger.info(f"Starting training v2 for {args.symbol} | period={args.period} | models={args.models} | sentiment={use_sentiment}")

    trainer = Trainer(symbol=args.symbol, use_sentiment=use_sentiment)

    if args.models == "all":
        results = trainer.train_all(period=args.period, interval=args.interval, force_refresh=args.force_refresh)
    else:
        data_dict = trainer.prepare_data(period=args.period, interval=args.interval, force_refresh=args.force_refresh)
        if args.models == "lstm":
            trainer.train_lstm(data_dict, epochs=args.epochs)
        elif args.models == "transformer":
            trainer.train_transformer(data_dict, epochs=args.epochs)
        elif args.models == "xgboost":
            trainer.train_xgboost(data_dict)
        elif args.models == "arima":
            trainer.train_arima(data_dict)
        elif args.models == "ensemble":
            trainer.train_lstm(data_dict, epochs=args.epochs)
            trainer.train_transformer(data_dict, epochs=args.epochs)
            trainer.train_xgboost(data_dict)
            trainer.train_arima(data_dict)
            trainer.train_ensemble(data_dict)

    logger.info("Training complete!")

if __name__ == "__main__":
    main()
