"""
Prediction script entry point
Usage: python scripts/predict.py --symbol BTC-USD --steps 7
"""
import sys
import argparse
from pathlib import Path
import json
sys.path.append(str(Path(__file__).parent.parent / "src"))

from crypto_prediction.prediction.predictor import CryptoPredictor
from crypto_prediction.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Predict crypto prices")
    parser.add_argument("--symbol", type=str, default="BTC-USD")
    parser.add_argument("--steps", type=int, default=7, help="Forecast horizon")
    parser.add_argument("--period", type=str, default="1y")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    predictor = CryptoPredictor(symbol=args.symbol)
    
    try:
        next_preds = predictor.predict_next(period=args.period)
        forecast = predictor.forecast(steps=args.steps, period=args.period)
        signal = predictor.get_trading_signal(forecast)

        if args.json:
            print(json.dumps({"next": next_preds, "forecast": forecast, "signal": signal}, indent=2))
        else:
            print(f"\n=== {args.symbol} Prediction ===")
            print(f"Current Price: ${forecast.get('current_price', 0):,.2f}")
            print("\nNext Price Predictions:")
            for model, price in next_preds.items():
                print(f"  {model:10s}: ${price:,.2f}")
            print(f"\n{args.steps}-Day Forecast (Ensemble):")
            ensemble = forecast.get('ensemble', [])
            dates = forecast.get('dates', [])
            for d, p in zip(dates, ensemble):
                print(f"  {d}: ${p:,.2f}")
            print(f"\nTrading Signal: {signal['signal']} ({signal['confidence']}% confidence)")
            print(f"  {signal['reason']}")

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        print(f"Error: {e}")
        print("Hint: Train models first with `python scripts/train.py --symbol {}`".format(args.symbol))

if __name__ == "__main__":
    main()
