"""
Crash Signals - Fixed: missing data handling, stablecoin, OI, validation
"""
import numpy as np
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class SignalResult:
    name: str
    score: float
    level: str
    reason: str
    details: Dict
    weight: float = 1.0
    data_quality: float = 1.0  # how reliable this signal is

    def to_dict(self):
        return {
            "name": self.name,
            "score": round(self.score,1),
            "level": self.level,
            "reason": self.reason,
            "details": self.details,
            "weight": self.weight,
            "data_quality": round(self.data_quality,2)
        }

def _level(score: float) -> str:
    if score >= 80: return "CRITICAL"
    if score >= 60: return "HIGH"
    if score >= 35: return "MEDIUM"
    return "LOW"

def calc_price_drop_signal(tickers: Dict) -> SignalResult:
    if not tickers or len(tickers) < 2:
        return SignalResult("price_drop", 15, "LOW", "No/insufficient ticker data - uncertain", {"avg_drop": 0, "min_drop": 0, "count_down": 0, "count_crash": 0, "warning": "missing data"}, 1.2, data_quality=0.2)
    drops=[]
    for sym, d in tickers.items():
        try:
            pct = float(d.get("change_pct",0) or 0)
            if abs(pct) < 100:  # sanity: no >100% drop in 24h normally
                drops.append(pct)
        except (ValueError, TypeError):
            continue
    if not drops:
        return SignalResult("price_drop", 10, "LOW", "No valid price data", {}, 1.2, data_quality=0.1)
    avg_drop = float(np.mean(drops))
    min_drop = float(np.min(drops))
    count_down = sum(1 for x in drops if x < -5)
    count_crash = sum(1 for x in drops if x < -10)
    score=0
    if avg_drop < -1: score+=20
    if avg_drop < -3: score+=25
    if avg_drop < -5: score+=30
    if min_drop < -10: score+=15
    if count_down > 5: score+=10
    if count_crash > 2: score+=20
    score=min(100, score)
    quality = min(1.0, len(drops)/10)
    reason=f"Avg {avg_drop:.1f}% | Min {min_drop:.1f}% | {count_down} coins <-5% | {count_crash} <-10% | {len(drops)} coins"
    return SignalResult("price_drop", score, _level(score), reason, {"avg_drop": avg_drop, "min_drop": min_drop, "count_down": count_down, "count_crash": count_crash, "total": len(drops)}, weight=1.5, data_quality=quality)

def calc_liquidation_signal(liquidations: Dict) -> SignalResult:
    if not liquidations:
        return SignalResult("liquidation", 10, "LOW", "No liquidation data - uncertain", {"total_liq": 0, "long_liq": 0, "warning": "missing"}, 1.3, data_quality=0.2)
    total_long=0.0
    total=0.0
    valid=0
    for sym, d in liquidations.items():
        try:
            tl = float(d.get("long_liq",0) or 0)
            tt = float(d.get("total",0) or 0)
            if tt>0:
                total_long+=tl
                total+=tt
                valid+=1
        except (ValueError, TypeError):
            continue
    if valid==0 or total==0:
        return SignalResult("liquidation", 5, "LOW", "No valid liquidation", {"total_liq": 0, "long_liq": 0}, 1.3, data_quality=0.2)
    score=0
    if total>1_000_000: score+=20
    if total>5_000_000: score+=25
    if total>20_000_000: score+=30
    if total_long>total*0.7 and total>1_000_000: score+=15
    score=min(100, score)
    long_pct = total_long/total*100 if total else 0
    reason=f"Total liq ${total/1e6:.1f}M | Long ${total_long/1e6:.1f}M ({long_pct:.0f}% longs) | {valid} symbols"
    quality = min(1.0, valid/3)
    return SignalResult("liquidation", score, _level(score), reason, {"total_liq": total, "long_liq": total_long, "long_pct": long_pct, "valid_symbols": valid}, weight=1.3, data_quality=quality)

def calc_funding_signal(funding_rates: List) -> SignalResult:
    if not funding_rates or len(funding_rates) < 3:
        return SignalResult("funding", 10, "LOW", "No/insufficient funding data - uncertain", {"avg_funding": 0, "min_funding": 0, "neg_count": 0, "warning": "missing"}, 1.0, data_quality=0.2)
    rates=[]
    for r in funding_rates:
        try:
            if isinstance(r, dict):
                v=r.get("fundingRate", r.get("lastFundingRate"))
                if v is not None:
                    fv=float(v)
                    if abs(fv) < 0.05:  # sanity <5%
                        rates.append(fv)
        except (ValueError, TypeError):
            continue
    if len(rates) < 3:
        return SignalResult("funding", 10, "LOW", f"Only {len(rates)} valid funding rates", {}, 1.0, data_quality=0.3)
    avg=float(np.mean(rates))
    min_r=float(np.min(rates))
    neg_count=sum(1 for x in rates if x<0)
    extreme_neg=sum(1 for x in rates if x<-0.001)
    score=0
    if avg<0: score+=20
    if avg<-0.0005: score+=20
    if avg<-0.001: score+=20
    if min_r<-0.002: score+=15
    if neg_count>len(rates)*0.6: score+=10
    if extreme_neg>3: score+=15
    score=min(100, score)
    quality = min(1.0, len(rates)/20)
    reason=f"Avg funding {avg*100:.4f}% | Min {min_r*100:.4f}% | {neg_count}/{len(rates)} negative | {extreme_neg} extreme<-0.1%"
    return SignalResult("funding", score, _level(score), reason, {"avg_funding": avg, "min_funding": min_r, "neg_count": neg_count, "extreme": extreme_neg, "total": len(rates)}, weight=1.0, data_quality=quality)

def calc_orderbook_signal(orderbooks: Dict) -> SignalResult:
    if not orderbooks:
        return SignalResult("orderbook", 15, "LOW", "No orderbook data - uncertain, possible liquidity issue", {"avg_imbalance": 0, "min_imbalance": 0, "warning": "missing"}, 1.2, data_quality=0.2)
    imbalances=[]
    for sym, ob in orderbooks.items():
        try:
            if not ob or ob.get("error"):
                continue
            imb=float(ob.get("imbalance",0) or 0)
            if -1 <= imb <= 1:
                imbalances.append(imb)
        except (ValueError, TypeError):
            continue
    if not imbalances:
        return SignalResult("orderbook", 10, "LOW", "No valid imbalance", {}, 1.2, data_quality=0.2)
    avg_imb=float(np.mean(imbalances))
    min_imb=float(np.min(imbalances))
    score=0
    if avg_imb<-0.1: score+=25
    if avg_imb<-0.2: score+=25
    if avg_imb<-0.3: score+=20
    if min_imb<-0.5: score+=20
    if min_imb<-0.7: score+=10
    score=min(100, score)
    quality = min(1.0, len(imbalances)/3)
    reason=f"Avg imbalance {avg_imb:.2f} (neg=sell pressure) | Min {min_imb:.2f} | {len(imbalances)} books"
    return SignalResult("orderbook", score, _level(score), reason, {"avg_imbalance": avg_imb, "min_imbalance": min_imb, "count": len(imbalances)}, weight=1.2, data_quality=quality)

def calc_whale_signal(trades: Dict) -> SignalResult:
    if not trades:
        return SignalResult("whale", 10, "LOW", "No trade data - uncertain", {"sell_ratio": 0.5, "whale_sells": 0, "warning": "missing"}, 1.1, data_quality=0.2)
    total_sell_ratio=[]
    whale_count=0
    valid=0
    for sym, d in trades.items():
        try:
            ratio=float(d.get("sell_ratio",0.5) or 0.5)
            if 0 <= ratio <= 1:
                total_sell_ratio.append(ratio)
                valid+=1
            whale_count+=int(d.get("whale_sells",0) or 0)
        except (ValueError, TypeError):
            continue
    if valid==0:
        return SignalResult("whale", 5, "LOW", "No valid trade data", {}, 1.1, data_quality=0.2)
    avg_sell=float(np.mean(total_sell_ratio))
    score=0
    if avg_sell>0.55: score+=20
    if avg_sell>0.6: score+=20
    if avg_sell>0.65: score+=20
    if whale_count>5: score+=15
    if whale_count>15: score+=25
    score=min(100, score)
    quality = min(1.0, valid/3)
    reason=f"Sell ratio {avg_sell*100:.1f}% | Whale sells >$50k: {whale_count} in last 100 trades | {valid} symbols"
    return SignalResult("whale", score, _level(score), reason, {"sell_ratio": avg_sell, "whale_sells": whale_count, "valid": valid}, weight=1.1, data_quality=quality)

def calc_stablecoin_signal(tickers: Dict) -> SignalResult:
    """Improved: check USDT volume dominance + BTC drop + alt drop"""
    if not tickers:
        return SignalResult("stablecoin", 10, "LOW", "No ticker for stablecoin check - uncertain", {"btc_change": 0, "warning": "missing"}, 1.4, data_quality=0.2)
    btc = tickers.get("BTCUSDT",{})
    btc_change = float(btc.get("change_pct",0) or 0)
    btc_vol = float(btc.get("quote_vol",0) or 0)

    # Count how many alts are dropping significantly
    alt_drops = sum(1 for k,v in tickers.items() if "USDT" in k and k != "BTCUSDT" and float(v.get("change_pct",0) or 0) < -5)

    score=0
    if btc_change<-3: score+=15
    if btc_change<-5: score+=20
    if btc_change<-7: score+=25
    if btc_change<-10: score+=20
    if alt_drops>=5 and btc_change<-3: score+=20  # flight to stablecoins
    if btc_vol>500_000_000 and btc_change<-5: score+=10  # high volume crash = panic to stable

    score=min(100, score)
    quality = 0.8 if btc else 0.3
    reason=f"BTC {btc_change:.1f}% | {alt_drops} alts <-5% | Vol ${btc_vol/1e6:.1f}M | Stable flight"
    return SignalResult("stablecoin", score, _level(score), reason, {"btc_change": btc_change, "alt_drops": alt_drops, "btc_vol": btc_vol}, weight=1.4, data_quality=quality)

def calc_fear_greed_signal(fng: Dict) -> SignalResult:
    if not fng or fng.get("error"):
        return SignalResult("fear_greed", 10, "LOW", "No Fear&Greed data - uncertain", {"value": 50, "warning": "missing"}, 0.8, data_quality=0.2)
    try:
        val=int(fng.get("value",50))
        val=max(0, min(100, val))
    except (ValueError, TypeError):
        val=50
    score=0
    if val<50: score+=10
    if val<40: score+=15
    if val<30: score+=20
    if val<20: score+=25
    if val<10: score+=30
    score=min(100, score)
    classification=fng.get("classification","Neutral")
    history = fng.get("history",[])
    # Check if dropping fast
    if len(history)>=2:
        try:
            prev = history[1].get("value", val) if isinstance(history[1], dict) else 50
            if val < prev - 10:
                score+=10
        except Exception:
            pass
    reason=f"Fear & Greed {val} - {classification} | Low = panic risk"
    quality = 0.9 if not fng.get("error") else 0.3
    return SignalResult("fear_greed", score, _level(score), reason, {"value": val, "classification": classification, "history": history[:3]}, weight=0.8, data_quality=quality)

def calc_correlation_signal(tickers: Dict) -> SignalResult:
    if not tickers or len(tickers) < 5:
        return SignalResult("correlation", 10, "LOW", "Insufficient data for correlation - uncertain", {"down_ratio": 0, "warning": "missing"}, 1.0, data_quality=0.3)
    downs=0
    total=0
    for sym, d in tickers.items():
        try:
            if "USDT" not in sym:
                continue
            if sym in ["USDTUSDT","USDCUSDT"]:
                continue
            pct = float(d.get("change_pct",0) or 0)
            if abs(pct) > 100:  # sanity
                continue
            total+=1
            if pct<-3:
                downs+=1
        except (ValueError, TypeError):
            continue
    if total < 3:
        return SignalResult("correlation", 10, "LOW", "Too few coins for correlation", {}, 1.0, data_quality=0.3)
    ratio=downs/total if total else 0
    score=0
    if ratio>0.5: score+=20
    if ratio>0.7: score+=30
    if ratio>0.8: score+=30
    if ratio>0.9: score+=20
    score=min(100, score)
    quality = min(1.0, total/10)
    reason=f"{downs}/{total} coins <-3% | {ratio*100:.0f}% dropping together = systemic"
    return SignalResult("correlation", score, _level(score), reason, {"down_ratio": ratio, "down_count": downs, "total": total}, weight=1.0, data_quality=quality)

def calc_volume_signal(tickers: Dict) -> SignalResult:
    if not tickers:
        return SignalResult("volume", 10, "LOW", "No volume data - uncertain", {"spikes": 0, "warning": "missing"}, 1.0, data_quality=0.2)
    spikes=0
    valid=0
    for sym, d in tickers.items():
        try:
            pct = float(d.get("change_pct",0) or 0)
            qvol = float(d.get("quote_vol",0) or 0)
            if abs(pct) > 100:
                continue
            valid+=1
            if pct<-5 and qvol>50_000_000:
                spikes+=1
        except (ValueError, TypeError):
            continue
    score=min(100, spikes*15)
    quality = min(1.0, valid/10)
    reason=f"{spikes} coins with volume spike + drop <-5% | Distribution"
    return SignalResult("volume", score, _level(score), reason, {"spikes": spikes, "valid": valid}, weight=1.0, data_quality=quality)

def calc_news_signal(news: List, reddit: List) -> SignalResult:
    if not news and not reddit:
        return SignalResult("news", 10, "LOW", "No news/reddit data - uncertain", {"crash_news": 0, "crash_reddit": 0, "warning": "missing"}, 1.2, data_quality=0.2)
    crash_news=0
    crash_reddit=0
    high_score_crash=0
    try:
        crash_news=sum(1 for n in (news or []) if n.get("is_crash"))
    except Exception:
        crash_news=0
    try:
        crash_reddit=sum(1 for p in (reddit or []) if p.get("is_crash"))
        high_score_crash=sum(1 for p in (reddit or []) if p.get("is_crash") and int(p.get("score",0) or 0)>100)
    except Exception:
        crash_reddit=0

    total_news=len(news) if news else 0
    total_reddit=len(reddit) if reddit else 0
    score=0
    if crash_news>0: score+=crash_news*15
    if crash_reddit>2: score+=15
    if crash_reddit>5: score+=20
    if crash_news>=3: score+=30
    if high_score_crash>0: score+=20
    score=min(100, score)
    quality = min(1.0, (total_news+total_reddit)/20) if (total_news+total_reddit)>0 else 0.2
    reason=f"News crash {crash_news}/{total_news} | Reddit crash {crash_reddit}/{total_reddit} | High-score {high_score_crash}"
    return SignalResult("news", score, _level(score), reason, {"crash_news": crash_news, "crash_reddit": crash_reddit, "high_score": high_score_crash, "total_news": total_news, "total_reddit": total_reddit}, weight=1.2, data_quality=quality)

def calc_oi_signal(oi_data: Dict, tickers: Dict) -> SignalResult:
    """Improved: OI with at least reporting, and check if OI data exists"""
    if not oi_data:
        return SignalResult("open_interest", 5, "LOW", "No OI data - need historical for drop detection", {"btc_oi": 0, "warning": "missing"}, 0.9, data_quality=0.2)
    btc_oi=0
    valid=0
    try:
        btc_oi=float(oi_data.get("BTCUSDT",{}).get("oi",0) or 0)
        valid=sum(1 for v in oi_data.values() if float(v.get("oi",0) or 0)>0)
    except (ValueError, TypeError, AttributeError):
        btc_oi=0

    # If OI is 0, data missing, not necessarily low risk
    if valid==0:
        return SignalResult("open_interest", 5, "LOW", "No valid OI", {"btc_oi": 0}, 0.9, data_quality=0.2)

    # We can't detect drop without history, but we can report current OI
    # Future improvement: store historical OI in manager and compare
    score=0
    # If we have OI, low score unless we have history showing drop - for now 0
    # But if BTC price dropping and OI is low, it might be after liquidation
    btc_change=0
    try:
        btc_change=float(tickers.get("BTCUSDT",{}).get("change_pct",0) or 0) if tickers else 0
    except Exception:
        btc_change=0

    # If price down and OI still high, risk of further liquidation
    if btc_change<-5 and btc_oi>100000:
        score+=20

    quality = min(1.0, valid/3)
    reason=f"BTC OI {btc_oi:,.0f} | {valid} symbols | Need historical for drop detection | BTC {btc_change:.1f}%"
    return SignalResult("open_interest", score, _level(score), reason, {"btc_oi": btc_oi, "valid": valid, "btc_change": btc_change}, weight=0.9, data_quality=quality)
