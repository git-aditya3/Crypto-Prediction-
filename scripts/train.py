"""
Training script entry point
Usage: python scripts/train.py --symbol BTC-USD --period 2y --models all
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
    parser = argparse.ArgumentParser(description="Train crypto prediction models")
    parser.add_argument("--symbol", type=str, default="BTC-USD", help="Crypto symbol e.g. BTC-USD")
    parser.add_argument("--period", type=str, default="2y", help="Data period e.g. 6mo,1y,2y,5y")
    parser.add_argument("--interval", type=str, default="1d", help="Data interval")
    parser.add_argument("--models", type=str, default="all", choices=["all","lstm","xgboost","arima","ensemble"], help="Which models to train")
    parser.add_argument("--epochs", type=int, default=None, help="LSTM epochs override")
    parser.add_argument("--force-refresh", action="store_true", help="Force refetch data")
    args = parser.parse_args()

    config = get_config()
    logger.info(f"Starting training for {args.symbol} | period={args.period} | models={args.models}")

    trainer = Trainer(symbol=args.symbol)

    if args.models == "all":
        results = trainer.train_all(period=args.period, interval=args.interval, force_refresh=args.force_refresh)
    else:
        data_dict = trainer.prepare_data(period=args.period, interval=args.interval, force_refresh=args.force_refresh)
        if args.models == "lstm":
            trainer.train_lstm(data_dict, epochs=args.epochs)
        elif args.models == "xgboost":
            trainer.train_xgboost(data_dict)
        elif args.models == "arima":
            trainer.train_arima(data_dict)
        elif args.models == "ensemble":
            trainer.train_lstm(data_dict, epochs=args.epochs)
            trainer.train_xgboost(data_dict)
            trainer.train_arima(data_dict)
            trainer.train_ensemble(data_dict)

    logger.info("Training complete!")

if __name__ == "__main__":
    main()
