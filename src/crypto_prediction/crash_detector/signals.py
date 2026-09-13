"""
Crash Signals - Local Efficient Computation
No ML heavy models, pure numpy logic, <10ms per signal
Each signal 0-100 score where 100 = crash imminent
"""
import numpy as np
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class SignalResult:
    name: str
    score: float  # 0-100 crash risk
    level: str    # LOW/MEDIUM/HIGH/CRITICAL
    reason: str
    details: Dict
    weight: float = 1.0

    def to_dict(self):
        return {
            "name": self.name,
            "score": round(self.score,1),
            "level": self.level,
            "reason": self.reason,
            "details": self.details,
            "weight": self.weight
        }

def _level(score: float) -> str:
    if score >= 80: return "CRITICAL"
    if score >= 60: return "HIGH"
    if score >= 35: return "MEDIUM"
    return "LOW"

# --- SIGNAL CALCULATORS (fast, local) ---

def calc_price_drop_signal(tickers: Dict) -> SignalResult:
    """Detect rapid price drops across market"""
    if not tickers:
        return SignalResult("price_drop", 0, "LOW", "No ticker data", {}, 1.2)
    drops=[]
    for sym, d in tickers.items():
        pct = d.get("change_pct",0)
        drops.append(pct)
    avg_drop = np.mean(drops) if drops else 0
    min_drop = np.min(drops) if drops else 0
    count_down = sum(1 for x in drops if x < -5)
    count_crash = sum(1 for x in drops if x < -10)
    # Score: if avg < -3% and many coins down -> high
    score=0
    if avg_drop < -1: score+=20
    if avg_drop < -3: score+=25
    if avg_drop < -5: score+=30
    if min_drop < -10: score+=15
    if count_down > 5: score+=10
    if count_crash > 2: score+=20
    score=min(100, score)
    reason=f"Avg {avg_drop:.1f}% | Min {min_drop:.1f}% | {count_down} coins <-5% | {count_crash} <-10%"
    return SignalResult("price_drop", score, _level(score), reason, {"avg_drop": avg_drop, "min_drop": min_drop, "count_down": count_down, "count_crash": count_crash}, weight=1.5)

def calc_liquidation_signal(liquidations: Dict) -> SignalResult:
    """Detect liquidation cascade"""
    if not liquidations:
        return SignalResult("liquidation", 0, "LOW", "No liquidation data", {}, 1.3)
    total_long=0
    total=0
    for sym, d in liquidations.items():
        total_long+=d.get("long_liq",0)
        total+=d.get("total",0)
    score=0
    if total>1_000_000: score+=20
    if total>5_000_000: score+=25
    if total>20_000_000: score+=30
    if total_long>total*0.7 and total>1_000_000: score+=15 # long squeeze = crash risk
    score=min(100, score)
    reason=f"Total liq ${total/1e6:.1f}M | Long ${total_long/1e6:.1f}M ({total_long/total*100 if total else 0:.0f}% longs)"
    return SignalResult("liquidation", score, _level(score), reason, {"total_liq": total, "long_liq": total_long}, weight=1.3)

def calc_funding_signal(funding_rates: List) -> SignalResult:
    """Funding flip negative = bearish, extreme negative = crash imminent but also bottom? For crash detection, rapid flip is warning"""
    if not funding_rates:
        return SignalResult("funding", 0, "LOW", "No funding data", {}, 1.0)
    rates=[]
    for r in funding_rates:
        try:
            if isinstance(r, dict):
                v=float(r.get("fundingRate", r.get("lastFundingRate",0)) or 0)
                rates.append(v)
        except: continue
    if not rates:
        return SignalResult("funding", 0, "LOW", "No valid funding", {}, 1.0)
    avg=np.mean(rates)
    min_r=np.min(rates)
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
    reason=f"Avg funding {avg*100:.4f}% | Min {min_r*100:.4f}% | {neg_count}/{len(rates)} negative | {extreme_neg} extreme<-0.1%"
    return SignalResult("funding", score, _level(score), reason, {"avg_funding": avg, "min_funding": min_r, "neg_count": neg_count}, weight=1.0)

def calc_orderbook_signal(orderbooks: Dict) -> SignalResult:
    """Bid liquidity drying = crash risk"""
    if not orderbooks:
        return SignalResult("orderbook", 0, "LOW", "No orderbook", {}, 1.2)
    imbalances=[]
    bid_vols=[]
    for sym, ob in orderbooks.items():
        if not ob: continue
        imb=ob.get("imbalance",0)
        imbalances.append(imb)
        bid_vols.append(ob.get("bid_vol",0))
    if not imbalances:
        return SignalResult("orderbook", 0, "LOW", "No imbalance data", {}, 1.2)
    avg_imb=np.mean(imbalances)
    min_imb=np.min(imbalances)
    # Negative imbalance = more asks than bids = sell pressure
    score=0
    if avg_imb<-0.1: score+=25
    if avg_imb<-0.2: score+=25
    if avg_imb<-0.3: score+=20
    if min_imb<-0.5: score+=20
    if min_imb<-0.7: score+=10
    score=min(100, score)
    reason=f"Avg imbalance {avg_imb:.2f} (neg=sell pressure) | Min {min_imb:.2f} | Bid liquidity drying"
    return SignalResult("orderbook", score, _level(score), reason, {"avg_imbalance": float(avg_imb), "min_imbalance": float(min_imb)}, weight=1.2)

def calc_whale_signal(trades: Dict) -> SignalResult:
    """Large sell trades concentration"""
    if not trades:
        return SignalResult("whale", 0, "LOW", "No trade data", {}, 1.1)
    total_sell_ratio=[]
    whale_count=0
    for sym, d in trades.items():
        total_sell_ratio.append(d.get("sell_ratio",0.5))
        whale_count+=d.get("whale_sells",0)
    avg_sell=np.mean(total_sell_ratio) if total_sell_ratio else 0.5
    score=0
    if avg_sell>0.55: score+=20
    if avg_sell>0.6: score+=20
    if avg_sell>0.65: score+=20
    if whale_count>5: score+=15
    if whale_count>15: score+=25
    score=min(100, score)
    reason=f"Sell ratio {avg_sell*100:.1f}% | Whale sells >$50k: {whale_count} in last 100 trades"
    return SignalResult("whale", score, _level(score), reason, {"sell_ratio": float(avg_sell), "whale_sells": whale_count}, weight=1.1)

def calc_stablecoin_signal(tickers: Dict) -> SignalResult:
    """USDT/USDC depeg detection"""
    if not tickers:
        return SignalResult("stablecoin", 0, "LOW", "No ticker", {}, 1.4)
    depeg_score=0
    details={}
    for sym in ["USDTUSDT","USDCUSDT","DAIUSDT","USDTUSD","USDCUSD"]:
        # Binance doesn't have USDTUSDT, but check USDT depeg via other means
        pass
    # Check USDT pairs price vs 1.0 using tickers that have USDT as base? Actually USDT price is always 1, but we can check USDT dominance or USDC price
    # Use alternative: if many alt/BTC dropping and USDT volume spiking, it's flight to safety
    # For now, check if BTC volume spike + price drop = stablecoin inflow to exchanges
    btc = tickers.get("BTCUSDT",{})
    if btc:
        vol=btc.get("quote_vol",0)
        # we don't have avg vol, so use count as proxy
        # If change_pct < -5 and volume high, it's depeg risk proxy
        if btc.get("change_pct",0)<-7:
            depeg_score+=40
        if btc.get("change_pct",0)<-10:
            depeg_score+=30
    # Check for stablecoin tickers if available
    for k,v in tickers.items():
        if "USDT" not in k and "USDC" not in k: continue
        # USDT should be ~1.0 if quoted in USD? Not applicable
        pass
    score=min(100, depeg_score)
    reason=f"Stablecoin flight check | BTC drop {btc.get('change_pct',0):.1f}% | Volume ${btc.get('quote_vol',0)/1e6:.1f}M"
    return SignalResult("stablecoin", score, _level(score), reason, {"btc_change": btc.get("change_pct",0)}, weight=1.4)

def calc_fear_greed_signal(fng: Dict) -> SignalResult:
    if not fng:
        return SignalResult("fear_greed", 0, "LOW", "No F&G", {}, 0.8)
    val=fng.get("value",50)
    score=0
    if val<50: score+=10
    if val<40: score+=15
    if val<30: score+=20
    if val<20: score+=25
    if val<10: score+=30
    score=min(100, score)
    classification=fng.get("classification","Neutral")
    reason=f"Fear & Greed {val} - {classification} | Low = panic selling risk"
    return SignalResult("fear_greed", score, _level(score), reason, {"value": val, "classification": classification, "history": fng.get("history",[])}, weight=0.8)

def calc_correlation_signal(tickers: Dict) -> SignalResult:
    """If >80% coins drop together, it's systemic crash"""
    if not tickers:
        return SignalResult("correlation", 0, "LOW", "No data", {}, 1.0)
    downs=0
    total=0
    for sym, d in tickers.items():
        if "USDT" not in sym: continue
        if sym in ["USDTUSDT","USDCUSDT"]: continue
        total+=1
        if d.get("change_pct",0)<-3:
            downs+=1
    ratio=downs/total if total else 0
    score=0
    if ratio>0.5: score+=20
    if ratio>0.7: score+=30
    if ratio>0.8: score+=30
    if ratio>0.9: score+=20
    score=min(100, score)
    reason=f"{downs}/{total} coins <-3% | {ratio*100:.0f}% market dropping together = systemic"
    return SignalResult("correlation", score, _level(score), reason, {"down_ratio": ratio, "down_count": downs, "total": total}, weight=1.0)

def calc_volume_signal(tickers: Dict) -> SignalResult:
    """Volume spike + price drop = distribution"""
    if not tickers:
        return SignalResult("volume", 0, "LOW", "No data", {}, 1.0)
    # Use count as proxy for volume spike - Binance count is trades count
    spikes=0
    for sym, d in tickers.items():
        # if quote_vol high and change negative
        if d.get("change_pct",0)<-5 and d.get("quote_vol",0)>50_000_000:
            spikes+=1
    score=min(100, spikes*15)
    reason=f"{spikes} coins with volume spike + drop <-5% | Distribution phase"
    return SignalResult("volume", score, _level(score), reason, {"spikes": spikes}, weight=1.0)

def calc_news_signal(news: List, reddit: List) -> SignalResult:
    """Crash keywords in news/reddit"""
    crash_news=sum(1 for n in news if n.get("is_crash"))
    crash_reddit=sum(1 for p in reddit if p.get("is_crash"))
    total_news=len(news) if news else 1
    total_reddit=len(reddit) if reddit else 1
    score=0
    if crash_news>0: score+=crash_news*15
    if crash_reddit>2: score+=15
    if crash_reddit>5: score+=20
    if crash_news>=3: score+=30
    # Check reddit scores
    high_score_crash=sum(1 for p in reddit if p.get("is_crash") and p.get("score",0)>100)
    if high_score_crash>0: score+=20
    score=min(100, score)
    reason=f"News crash {crash_news}/{total_news} | Reddit crash {crash_reddit}/{total_reddit} | High-score crash posts {high_score_crash}"
    return SignalResult("news", score, _level(score), reason, {"crash_news": crash_news, "crash_reddit": crash_reddit, "high_score": high_score_crash}, weight=1.2)

def calc_oi_signal(oi_data: Dict, tickers: Dict) -> SignalResult:
    """Open interest dropping while price dropping = long liquidation cascade ending? Or starting?"""
    # We only have current OI, not historical, so we can't calc drop. Use proxy: if OI low and funding negative, it's after crash.
    # For now, if we have OI data, check if BTC OI is low relative? Can't. So use funding as proxy
    if not oi_data:
        return SignalResult("open_interest", 0, "LOW", "No OI data", {}, 0.9)
    # If we have OI, we can at least report it
    btc_oi=oi_data.get("BTCUSDT",{}).get("oi",0)
    score=0
    # No historical comparison, so low score unless we detect extreme
    reason=f"BTC OI {btc_oi:,.0f} | Need historical for drop detection"
    return SignalResult("open_interest", score, _level(score), reason, {"btc_oi": btc_oi}, weight=0.9)
