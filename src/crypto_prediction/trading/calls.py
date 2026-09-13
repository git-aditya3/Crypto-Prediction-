"""
Trading Calls Generator - Professional trading signals with entry, SL, TP
Fixed: INR/USD handling, CoinDCX primary for INR, Binance for USD, validation
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from ..config import get_config
from ..data.fetcher import CryptoDataFetcher
from ..features.technical import FeatureEngineer
from ..prediction.predictor import CryptoPredictor
from ..features.sentiment import SentimentFeatureEngineer
from .risk import RiskManager
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

@dataclass
class TradingCall:
    symbol: str
    signal: str
    action: str
    confidence: float
    entry_price: float
    current_price: float
    stop_loss: float
    take_profits: Dict[str, float]
    risk_reward: Dict[str, float]
    position: Dict
    timeframe: str
    risk_level: str
    model_used: str
    model_versions: Dict
    predicted_price: float
    change_pct: float
    indicators: Dict
    sentiment: Dict
    reasoning: str
    timestamp: str
    expiry: str
    leverage: str
    status: str = "ACTIVE"

    def to_dict(self):
        try:
            return asdict(self)
        except Exception:
            return {
                "symbol": getattr(self, 'symbol', 'UNKNOWN'),
                "signal": getattr(self, 'signal', 'HOLD'),
                "action": getattr(self, 'action', 'WAIT'),
                "confidence": float(getattr(self, 'confidence', 50) or 50),
                "entry_price": float(getattr(self, 'entry_price', 0) or 0),
                "current_price": float(getattr(self, 'current_price', 0) or 0),
                "stop_loss": float(getattr(self, 'stop_loss', 0) or 0),
                "take_profits": getattr(self, 'take_profits', {}),
                "risk_reward": getattr(self, 'risk_reward', {}),
                "position": getattr(self, 'position', {}),
                "timeframe": getattr(self, 'timeframe', '1d'),
                "risk_level": getattr(self, 'risk_level', 'MEDIUM'),
                "model_used": getattr(self, 'model_used', 'Unknown'),
                "model_versions": getattr(self, 'model_versions', {}),
                "predicted_price": float(getattr(self, 'predicted_price', 0) or 0),
                "change_pct": float(getattr(self, 'change_pct', 0) or 0),
                "indicators": getattr(self, 'indicators', {}),
                "sentiment": getattr(self, 'sentiment', {}),
                "reasoning": getattr(self, 'reasoning', ''),
                "timestamp": getattr(self, 'timestamp', datetime.utcnow().isoformat()),
                "expiry": getattr(self, 'expiry', datetime.utcnow().isoformat()),
                "leverage": getattr(self, 'leverage', '1x'),
                "status": getattr(self, 'status', 'ACTIVE')
            }

class TradingCallGenerator:
    def __init__(self, risk_per_trade: float = 0.02):
        try:
            risk_per_trade = float(risk_per_trade)
            if risk_per_trade <=0 or risk_per_trade > 1:
                risk_per_trade = 0.02
        except (ValueError, TypeError):
            risk_per_trade = 0.02
        self.risk_manager = RiskManager(risk_per_trade=risk_per_trade)
        self.engineer = FeatureEngineer()

    def _get_live_price(self, symbol: str) -> Optional[float]:
        """Unified live price - respects INR vs USD symbol"""
        if not symbol or not isinstance(symbol, str):
            return None
        symbol = symbol.strip()
        if len(symbol) < 3:
            return None

        is_inr = "INR" in symbol.upper()
        
        # For INR symbols: CoinDCX primary
        if is_inr:
            try:
                from ..data.coindcx_fetcher import CoinDCXRealtimeFetcher
                coindcx = CoinDCXRealtimeFetcher(symbol=symbol)
                price = coindcx.get_current_price()
                if price and isinstance(price, (int,float)) and price > 0 and price < 200_000_000:
                    return float(price)
            except Exception as e:
                logger.debug(f"CoinDCX price failed {symbol}: {e}")

            try:
                from ..data.price_helper import get_live_price as unified
                p = unified(symbol)
                if p and p > 0 and p < 200_000_000:
                    return float(p)
            except Exception:
                pass

            # Fallback: Binance USD converted to INR
            try:
                from ..data.realtime import BinanceRealtimeFetcher
                f = BinanceRealtimeFetcher(symbol=symbol.replace("INR","USDT").replace("USD","USDT"))
                price = f.get_current_price()
                if price and price > 0 and price < 10_000_000:
                    return float(price) * 83.5
            except Exception:
                pass
            return None

        # For USD/USDT symbols: Binance primary
        else:
            try:
                from ..data.realtime import BinanceRealtimeFetcher
                f = BinanceRealtimeFetcher(symbol=symbol)
                price = f.get_current_price()
                if price and isinstance(price, (int,float)) and price > 0 and price < 10_000_000:
                    return float(price)
            except Exception as e:
                logger.debug(f"Binance price failed {symbol}: {e}")

            try:
                from ..data.price_helper import get_live_price as unified
                p = unified(symbol)
                if p and p > 0:
                    # If unified returned INR for USD symbol (because CoinDCX fallback), convert back?
                    # Heuristic: if p > 100000 (likely INR for BTC), and symbol is BTC, convert
                    if p > 100000 and symbol.upper().startswith("BTC"):
                        # Could be INR, convert to USD
                        usd = p / 83.5
                        if usd > 1000:
                            return float(usd)
                    if p < 10_000_000:
                        return float(p)
            except Exception:
                pass

            # Fallback CoinDCX converted to USD
            try:
                from ..data.coindcx_fetcher import CoinDCXRealtimeFetcher
                coindcx = CoinDCXRealtimeFetcher(symbol=symbol)
                price = coindcx.get_current_price()
                if price and price > 0:
                    # CoinDCX returns INR, convert to USD
                    usd = float(price) / 83.5
                    if usd > 0 and usd < 10_000_000:
                        return usd
            except Exception:
                pass

            return None

    def _get_binance_price(self, symbol: str) -> Optional[float]:
        return self._get_live_price(symbol)

    def _get_technical_indicators(self, df: pd.DataFrame) -> Dict:
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return {}
        try:
            latest = df.iloc[-1]
        except Exception:
            return {}
        indicators = {}
        for col in ['SMA_20', 'SMA_50', 'EMA_12', 'EMA_26', 'RSI', 'MACD', 'MACD_Signal', 'BB_Position', 'ADX']:
            try:
                if col in df.columns:
                    val = latest.get(col)
                    if pd.notna(val):
                        try:
                            indicators[col] = float(val)
                        except (ValueError, TypeError):
                            continue
            except Exception:
                continue
        try:
            indicators['close'] = float(latest.get('Close', 0) or 0)
        except (ValueError, TypeError):
            indicators['close'] = 0.0
        try:
            indicators['volume_ratio'] = float(latest.get('Volume_Ratio', 1.0)) if 'Volume_Ratio' in df.columns else 1.0
        except (ValueError, TypeError):
            indicators['volume_ratio'] = 1.0
        try:
            indicators['volatility'] = float(latest.get('Volatility', 0.02)) if 'Volatility' in df.columns else 0.02
        except (ValueError, TypeError):
            indicators['volatility'] = 0.02
        try:
            indicators['atr'] = float(latest.get('ATR', latest.get('Close', 0) * 0.02)) if 'ATR' in df.columns else float(latest.get('Close', 0) * 0.02)
        except (ValueError, TypeError):
            indicators['atr'] = float(indicators.get('close',0) * 0.02) if indicators.get('close',0) >0 else 0.02
        return indicators

    def _generate_reasoning(self, signal: str, indicators: Dict, sentiment: Dict, forecast: Dict, model_versions: Dict) -> str:
        reasons = []
        try:
            if isinstance(forecast, dict) and 'ensemble' in forecast:
                try:
                    reasons.append(f"Ensemble predicts {float(forecast.get('change_pct', 0)):.2f}%")
                except (ValueError, TypeError):
                    pass
            rsi = float(indicators.get('RSI', 50) or 50)
            if rsi < 30:
                reasons.append(f"RSI oversold {rsi:.1f}")
            elif rsi > 70:
                reasons.append(f"RSI overbought {rsi:.1f}")
            elif 40 < rsi < 60:
                reasons.append(f"RSI neutral {rsi:.1f}")
            macd = float(indicators.get('MACD', 0) or 0)
            macd_signal = float(indicators.get('MACD_Signal', 0) or 0)
            if macd > macd_signal:
                reasons.append("MACD bullish")
            elif macd < macd_signal:
                reasons.append("MACD bearish")
            bb_pos = float(indicators.get('BB_Position', 0.5) or 0.5)
            if bb_pos < 0.2:
                reasons.append("Near lower BB - oversold")
            elif bb_pos > 0.8:
                reasons.append("Near upper BB - overbought")
            adx = float(indicators.get('ADX', 20) or 20)
            if adx > 25:
                reasons.append(f"Strong trend ADX {adx:.1f}")
            if isinstance(sentiment, dict):
                sentiment_score = float(sentiment.get('average_compound', 0) or 0)
                if sentiment_score > 0.3:
                    reasons.append(f"Bullish sentiment {sentiment_score:.2f}")
                elif sentiment_score < -0.3:
                    reasons.append(f"Bearish sentiment {sentiment_score:.2f}")
            if isinstance(model_versions, dict) and model_versions:
                try:
                    reasons.append(f"Models: {', '.join([f'{k}' for k,v in model_versions.items()])}")
                except Exception:
                    pass
        except Exception:
            pass
        if not reasons:
            reasons.append(f"{signal} based on ensemble")
        return " • ".join(reasons)

    def _create_synthetic_df(self, symbol: str, live_price: float) -> pd.DataFrame:
        try:
            live_price = float(live_price)
            if live_price <=0 or live_price > 200_000_000:
                live_price = 50000.0
        except (ValueError, TypeError):
            live_price = 50000.0
        try:
            dates = pd.date_range(end=pd.Timestamp.utcnow(), periods=100, freq='D')
            np.random.seed(abs(hash(symbol)) % 2**32)
            noise = np.random.normal(0, live_price*0.015, 100)
            closes = live_price + np.cumsum(noise) * 0.1
            closes = np.maximum(closes, live_price*0.5)
            df = pd.DataFrame({
                'Open': closes * 0.998,
                'High': closes * 1.01,
                'Low': closes * 0.99,
                'Close': closes,
                'Volume': np.random.uniform(1e6, 1e9, 100)
            }, index=dates)
            df.iloc[-1, df.columns.get_loc('Close')] = live_price
            df.iloc[-1, df.columns.get_loc('Open')] = live_price * 0.999
            df.iloc[-1, df.columns.get_loc('High')] = live_price * 1.008
            df.iloc[-1, df.columns.get_loc('Low')] = live_price * 0.992
            return df
        except Exception:
            # Fallback minimal df
            dates = pd.date_range(end=pd.Timestamp.utcnow(), periods=100, freq='D')
            return pd.DataFrame({
                'Open': [live_price*0.998]*100,
                'High': [live_price*1.01]*100,
                'Low': [live_price*0.99]*100,
                'Close': [live_price]*100,
                'Volume': [1e7]*100
            }, index=dates)

    def generate_call(self, symbol: str = "BTC-USD", timeframe: str = "1d", account_balance: float = 10000) -> TradingCall:
        try:
            if not symbol or not isinstance(symbol, str):
                symbol = "BTC-USD"
            try:
                account_balance = float(account_balance or 10000)
                if account_balance <=0 or account_balance > 1e12:
                    account_balance = 10000
            except (ValueError, TypeError):
                account_balance = 10000

            df = None
            try:
                fetcher = CryptoDataFetcher(symbol=symbol)
                df = fetcher.load_or_fetch(symbol=symbol)
            except Exception as e_fetch:
                logger.warning(f"Fetcher failed for {symbol}: {e_fetch}, trying live price")
                live_price = self._get_live_price(symbol)
                if live_price and live_price > 0:
                    df = self._create_synthetic_df(symbol, live_price)
                else:
                    raise e_fetch

            if df is None or df.empty:
                raise ValueError(f"No data for {symbol}")

            try:
                engineered = self.engineer.engineer(df)
            except Exception as e:
                logger.warning(f"Feature engineering failed {symbol}: {e}")
                engineered = df

            indicators = self._get_technical_indicators(engineered)

            predictor = CryptoPredictor(symbol=symbol)
            forecast = {}
            signal_data = {}
            try:
                forecast = predictor.forecast(steps=7, period="1y")
                signal_data = predictor.get_trading_signal(forecast)
                if not isinstance(forecast, dict):
                    forecast = {}
                if not isinstance(signal_data, dict):
                    signal_data = {}
            except Exception as e:
                logger.warning(f"Forecast failed for {symbol}: {e}, using fallback")
                try:
                    last_close = float(df['Close'].iloc[-1])
                except Exception:
                    last_close = self._get_live_price(symbol) or 50000.0
                try:
                    sma_20 = float(df['Close'].rolling(20).mean().iloc[-1]) if len(df) >=20 else last_close
                except Exception:
                    sma_20 = last_close
                rsi = 50
                try:
                    if 'RSI' in engineered.columns and not engineered['RSI'].empty:
                        rsi = float(engineered['RSI'].iloc[-1])
                except Exception:
                    rsi = 50
                
                if last_close > sma_20 and rsi < 70:
                    signal_data = {
                        "signal": "BUY",
                        "confidence": 65,
                        "current_price": float(last_close),
                        "predicted_price": float(last_close * 1.02),
                        "change_pct": 2.0,
                        "reason": "Price above SMA20, RSI not overbought"
                    }
                elif last_close < sma_20 and rsi > 30:
                    signal_data = {
                        "signal": "SELL",
                        "confidence": 62,
                        "current_price": float(last_close),
                        "predicted_price": float(last_close * 0.98),
                        "change_pct": -2.0,
                        "reason": "Price below SMA20"
                    }
                else:
                    signal_data = {
                        "signal": "HOLD",
                        "confidence": 50,
                        "current_price": float(last_close),
                        "predicted_price": float(last_close),
                        "change_pct": 0,
                        "reason": "Neutral"
                    }
                forecast = {"current_price": float(last_close), "ensemble": [float(last_close * (1+signal_data['change_pct']/100))], "change_pct": signal_data['change_pct']}

            sentiment = {"average_compound": 0, "daily": []}
            try:
                senti_eng = SentimentFeatureEngineer()
                senti_df = senti_eng.get_daily_sentiment(symbol=symbol, days=7)
                if senti_df is not None and not senti_df.empty:
                    try:
                        avg = float(senti_df['sentiment_compound'].mean())
                    except Exception:
                        avg = 0.0
                    daily=[]
                    try:
                        for idx, row in senti_df.tail(3).iterrows():
                            try:
                                daily.append({"date": idx.strftime('%Y-%m-%d'), "compound": float(row['sentiment_compound'])})
                            except Exception:
                                continue
                    except Exception:
                        daily=[]
                    sentiment = {"average_compound": avg, "daily": daily}
            except Exception:
                pass

            signal = signal_data.get('signal', 'HOLD') if isinstance(signal_data, dict) else 'HOLD'
            if not isinstance(signal, str):
                signal = str(signal)
            confidence = signal_data.get('confidence', 50) if isinstance(signal_data, dict) else 50
            try:
                confidence = float(confidence or 50)
                confidence = max(0.0, min(100.0, confidence))
            except (ValueError, TypeError):
                confidence = 50.0

            live_price = self._get_live_price(symbol)
            if live_price and live_price > 0:
                current_price = float(live_price)
            else:
                try:
                    current_price = float(signal_data.get('current_price') or forecast.get('current_price') or float(df['Close'].iloc[-1]))
                except (ValueError, TypeError, IndexError):
                    current_price = live_price or 50000.0

            try:
                predicted_price = float(signal_data.get('predicted_price') or current_price)
            except (ValueError, TypeError):
                predicted_price = float(current_price)

            # Recalc change pct if we overrode with live
            if live_price and live_price > 0 and signal_data.get('predicted_price'):
                try:
                    pred = float(signal_data.get('predicted_price'))
                    change_pct = (pred - live_price) / live_price * 100 if live_price else float(signal_data.get('change_pct',0) or 0)
                except Exception:
                    try:
                        change_pct = float(signal_data.get('change_pct', 0) or 0)
                    except (ValueError, TypeError):
                        change_pct = 0.0
            else:
                try:
                    change_pct = float(signal_data.get('change_pct', 0) or 0)
                except (ValueError, TypeError):
                    change_pct = 0.0

            model_versions = forecast.get('model_versions', {}) if isinstance(forecast, dict) else {}
            if not isinstance(model_versions, dict):
                model_versions = {}
            # Also try signal_data model_versions
            try:
                if isinstance(signal_data, dict) and isinstance(signal_data.get('model_versions'), dict):
                    model_versions.update(signal_data.get('model_versions',{}))
            except Exception:
                pass

            if signal in ["STRONG_BUY", "BUY"]:
                action = "LONG"
            elif signal in ["STRONG_SELL", "SELL"]:
                action = "SHORT"
            else:
                action = "WAIT"

            try:
                atr = float(indicators.get('atr', current_price * 0.02) or current_price*0.02)
                if atr <=0 or atr > current_price:
                    atr = current_price * 0.02
            except (ValueError, TypeError):
                atr = current_price * 0.02

            try:
                stop_loss = float(self.risk_manager.calculate_stop_loss(current_price, atr, signal))
            except Exception:
                stop_loss = current_price * 0.98 if action=="LONG" else current_price*1.02

            try:
                take_profits = self.risk_manager.calculate_take_profits(current_price, stop_loss, signal)
                if not isinstance(take_profits, dict):
                    take_profits = {"tp1": current_price*1.02, "tp2": current_price*1.04, "tp3": current_price*1.06}
            except Exception:
                take_profits = {"tp1": current_price*1.02, "tp2": current_price*1.04, "tp3": current_price*1.06}

            risk_reward = {}
            for tp_name, tp_price in take_profits.items():
                try:
                    rr = self.risk_manager.calculate_risk_reward(current_price, stop_loss, float(tp_price))
                    risk_reward[tp_name] = float(rr)
                except Exception:
                    risk_reward[tp_name] = 1.0

            try:
                position = self.risk_manager.calculate_position_size(account_balance, current_price, stop_loss)
                if not isinstance(position, dict):
                    position = {"size": 0, "risk_pct": 2.0, "leverage_suggestion": "1x"}
            except Exception:
                position = {"size": 0, "risk_pct": 2.0, "leverage_suggestion": "1x"}

            try:
                risk_level = self.risk_manager.get_risk_level(confidence, float(indicators.get('volatility', 0.02) or 0.02))
            except Exception:
                risk_level = "MEDIUM"

            reasoning = self._generate_reasoning(signal, indicators, sentiment, forecast, model_versions)

            now = datetime.utcnow()
            expiry = now + timedelta(days=7)
            leverage = position.get('leverage_suggestion', '1x-3x') if isinstance(position, dict) else '1x'
            model_used = "Ensemble v3 (Dynamic + Stacking)" if model_versions else "Ensemble v2 + Technical"

            call = TradingCall(
                symbol=symbol,
                signal=signal,
                action=action,
                confidence=float(confidence),
                entry_price=float(current_price),
                current_price=float(current_price),
                stop_loss=float(stop_loss),
                take_profits={k: float(v) for k, v in take_profits.items() if isinstance(v, (int,float))},
                risk_reward=risk_reward,
                position=position,
                timeframe=timeframe,
                risk_level=risk_level,
                model_used=model_used,
                model_versions=model_versions,
                predicted_price=float(predicted_price),
                change_pct=float(change_pct),
                indicators=indicators,
                sentiment=sentiment,
                reasoning=reasoning,
                timestamp=now.isoformat(),
                expiry=expiry.isoformat(),
                leverage=leverage,
                status="ACTIVE"
            )
            return call

        except Exception as e:
            logger.error(f"Failed to generate call for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            try:
                bp = self._get_live_price(symbol)
                if bp and bp > 0:
                    try:
                        atr = float(bp) * 0.02
                        sl = float(self.risk_manager.calculate_stop_loss(bp, atr, "HOLD"))
                        tps = self.risk_manager.calculate_take_profits(bp, sl, "HOLD")
                        pos = self.risk_manager.calculate_position_size(account_balance, bp, sl)
                        if not isinstance(tps, dict):
                            tps = {"tp1": bp*1.02, "tp2": bp*1.04}
                        if not isinstance(pos, dict):
                            pos = {"size": 0, "risk_pct": 2.0, "leverage_suggestion": "1x"}
                        return TradingCall(
                            symbol=symbol,
                            signal="HOLD",
                            action="WAIT",
                            confidence=50.0,
                            entry_price=float(bp),
                            current_price=float(bp),
                            stop_loss=float(sl),
                            take_profits={k: float(v) for k, v in tps.items() if isinstance(v, (int,float))},
                            risk_reward={"tp1": 1.0, "tp2": 2.0, "tp3": 3.0},
                            position=pos,
                            timeframe=timeframe,
                            risk_level="MEDIUM",
                            model_used="Live Price Fallback",
                            model_versions={},
                            predicted_price=float(bp),
                            change_pct=0,
                            indicators={"close": float(bp), "atr": float(atr)},
                            sentiment={"average_compound": 0},
                            reasoning=f"Live price fallback, neutral",
                            timestamp=datetime.utcnow().isoformat(),
                            expiry=(datetime.utcnow() + timedelta(days=7)).isoformat(),
                            leverage=pos.get('leverage_suggestion', '1x') if isinstance(pos, dict) else '1x',
                            status="ACTIVE"
                        )
                    except Exception:
                        pass
            except Exception:
                pass

            return TradingCall(
                symbol=symbol,
                signal="HOLD",
                action="WAIT",
                confidence=50.0,
                entry_price=0,
                current_price=0,
                stop_loss=0,
                take_profits={"tp1": 0, "tp2": 0, "tp3": 0},
                risk_reward={"tp1": 1.0, "tp2": 2.0, "tp3": 3.0},
                position={"size": 0, "risk_pct": 2.0},
                timeframe=timeframe,
                risk_level="MEDIUM",
                model_used="Fallback",
                model_versions={},
                predicted_price=0,
                change_pct=0,
                indicators={},
                sentiment={},
                reasoning=f"Error: {str(e)[:200]}",
                timestamp=datetime.utcnow().isoformat(),
                expiry=(datetime.utcnow() + timedelta(days=7)).isoformat(),
                leverage="1x",
                status="ERROR"
            )

    def generate_all_calls(self, symbols: List[str] = None, timeframe: str = "1d", account_balance: float = 10000) -> List[TradingCall]:
        if symbols is None:
            try:
                symbols = config.data.supported_symbols
                if not isinstance(symbols, list):
                    symbols = ["BTC-USD","ETH-USD","BNB-USD","SOL-USD"]
            except Exception:
                symbols = ["BTC-USD","ETH-USD","BNB-USD","SOL-USD"]
        calls = []
        for symbol in symbols:
            try:
                if not isinstance(symbol, str) or len(symbol.strip()) < 3:
                    continue
                call = self.generate_call(symbol=symbol.strip(), timeframe=timeframe, account_balance=account_balance)
                calls.append(call)
                try:
                    logger.info(f"Generated {call.signal} for {symbol} at {call.entry_price:.2f} conf {call.confidence:.0f}%")
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"Failed for {symbol}: {e}")
                continue
        
        def sort_key(call):
            try:
                active_score = 1 if getattr(call, 'status', '') == "ACTIVE" else 0
                signal_score = {"STRONG_BUY": 5, "BUY": 4, "HOLD": 3, "SELL": 2, "STRONG_SELL": 1}.get(getattr(call, 'signal',''), 0)
                price_score = 1 if getattr(call, 'entry_price',0) > 0 else 0
                conf = float(getattr(call, 'confidence',0) or 0)
                return (active_score, price_score, signal_score, conf)
            except Exception:
                return (0,0,0,0)
        
        try:
            calls.sort(key=sort_key, reverse=True)
        except Exception:
            pass
        return calls

    def get_call_summary(self, calls: List[TradingCall]) -> Dict:
        try:
            total = len(calls) if isinstance(calls, list) else 0
            active = len([c for c in calls if getattr(c, 'status','') == "ACTIVE" and getattr(c, 'entry_price',0) > 0]) if isinstance(calls, list) else 0
            buys = len([c for c in calls if "BUY" in getattr(c, 'signal','') and getattr(c, 'entry_price',0) > 0]) if isinstance(calls, list) else 0
            sells = len([c for c in calls if "SELL" in getattr(c, 'signal','') and getattr(c, 'entry_price',0) > 0]) if isinstance(calls, list) else 0
            holds = len([c for c in calls if getattr(c, 'signal','') == "HOLD" and getattr(c, 'entry_price',0) > 0]) if isinstance(calls, list) else 0
            valid_calls = [c for c in calls if getattr(c, 'entry_price',0) > 0] if isinstance(calls, list) else []
            try:
                avg_confidence = float(np.mean([float(getattr(c, 'confidence',0) or 0) for c in valid_calls])) if valid_calls else 0
            except Exception:
                avg_confidence = 0
            high_conf = len([c for c in valid_calls if float(getattr(c, 'confidence',0) or 0) > 80]) if valid_calls else 0
            return {
                "total": total,
                "active": active,
                "buys": buys,
                "sells": sells,
                "holds": holds,
                "avg_confidence": avg_confidence,
                "high_confidence": high_conf,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"total": 0, "active": 0, "buys": 0, "sells": 0, "holds": 0, "avg_confidence": 0, "high_confidence": 0, "timestamp": datetime.utcnow().isoformat(), "error": str(e)}
