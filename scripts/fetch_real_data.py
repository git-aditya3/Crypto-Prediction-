"""
Real historical data collection via Coinbase API
Proven working with fetch_page tool - bypasses SSL issues with yfinance/CoinGecko

Coinbase endpoint: https://api.exchange.coinbase.com/products/{SYMBOL}/candles
Params: granularity=86400 (daily), start/end ISO8601, max 300 days per request
Response: [[time,low,high,open,close,volume], ...] newest first

This script combines 90-day windows (to stay <300 and single chunk) into full history
and converts to CSV format expected by CryptoDataFetcher:
- data/raw/{SYMBOL}_1d.csv with index timestamp and columns Open,High,Low,Close,Volume
- data/raw/{SYMBOL}_d.csv with columns timestamp,open,high,low,close,volume (ISO date)

Usage:
  python scripts/fetch_real_data.py --symbol BTC-USD --start 2023-01-01 --end 2025-09-13
  # Or use pre-fetched /tmp/btc_90d_*.json files (from fetch_page tool)

Proven: BTC-USD 2023-01-01→2025-09-13 987 candles via 11x90d windows
"""

import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

def combine_json_files(pattern: str = "/tmp/btc_90d_*.json"):
    import glob
    all_data = []
    for p in sorted(glob.glob(pattern)):
        data = json.loads(Path(p).read_text())
        print(f"{p}: {len(data)} rows {data[0][0]} -> {data[-1][0]}")
        all_data.extend(data)
    # Dedup by timestamp
    dedup = {e[0]: e for e in all_data}
    sorted_entries = sorted(dedup.values(), key=lambda x: x[0])
    print(f"Combined {len(all_data)} -> deduped {len(sorted_entries)}")
    return sorted_entries

def entries_to_df(entries):
    rows = []
    for ts, low, high, open_, close_, vol in entries:
        dt = datetime.utcfromtimestamp(ts)
        rows.append({
            'timestamp': dt,
            'open': open_,
            'high': high,
            'low': low,
            'close': close_,
            'volume': vol
        })
    df = pd.DataFrame(rows).sort_values('timestamp')
    return df

def save_csv(df, symbol: str):
    # Format for fetcher: data/raw/BTC_USD_1d.csv
    raw_dir = Path("data/raw")
    proc_dir = Path("data/processed")
    raw_dir.mkdir(parents=True, exist_ok=True)
    proc_dir.mkdir(parents=True, exist_ok=True)

    # Fetcher format: index timestamp, columns Open,High,Low,Close,Volume
    df_raw = pd.DataFrame({
        'Open': df['open'].values,
        'High': df['high'].values,
        'Low': df['low'].values,
        'Close': df['close'].values,
        'Volume': df['volume'].values
    }, index=pd.to_datetime(df['timestamp']))
    df_raw = df_raw.sort_index()

    out1 = raw_dir / f"{symbol.replace('-','_')}_1d.csv"
    df_raw.to_csv(out1)
    print(f"Saved {out1} {len(df_raw)} rows")

    out2 = raw_dir / f"{symbol}_d.csv"
    df2 = pd.DataFrame({
        'timestamp': df['timestamp'].dt.strftime('%Y-%m-%d'),
        'open': df['open'],
        'high': df['high'],
        'low': df['low'],
        'close': df['close'],
        'volume': df['volume']
    })
    df2.to_csv(out2, index=False)
    print(f"Saved {out2}")

    # Processed copies
    df_raw.to_csv(proc_dir / f"{symbol.replace('-','_')}_1d.csv")
    df2.to_csv(proc_dir / f"{symbol}_d.csv", index=False)
    print(f"Saved processed copies")

def fetch_via_coinbase_api(symbol: str, start: str, end: str):
    """
    Example of how to fetch via Coinbase using requests
    Note: In this sandbox, requests fails with SSL, so use fetch_page tool instead
    This function is for documentation and for environments where SSL works
    """
    import requests
    from datetime import datetime
    # Split into 90-day windows
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    delta = timedelta(days=90)
    all_entries = []
    cur = start_dt
    while cur < end_dt:
        nxt = min(cur + delta, end_dt)
        url = f"https://api.exchange.coinbase.com/products/{symbol}/candles"
        params = {
            "granularity": 86400,
            "start": cur.isoformat(),
            "end": nxt.isoformat()
        }
        print(f"Fetching {symbol} {cur.date()} -> {nxt.date()}")
        # In sandbox, use fetch_page tool: https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400&start=2023-01-01T00:00:00&end=2023-04-01T00:00:00
        # For local env with working SSL:
        try:
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            all_entries.extend(data)
        except Exception as e:
            print(f"Fetch failed (expected in sandbox): {e}")
            print("Use fetch_page tool with URL: " + url + "?granularity=86400&start=" + cur.isoformat() + "&end=" + nxt.isoformat())
        cur = nxt
    return all_entries

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC-USD")
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default="2025-09-13")
    parser.add_argument("--pattern", default="/tmp/btc_90d_*.json", help="Glob for pre-fetched JSON files from fetch_page")
    args = parser.parse_args()

    # Try to combine from pre-fetched files
    entries = combine_json_files(args.pattern)
    if not entries:
        print("No pre-fetched files found, attempting direct fetch (will fail in sandbox, use fetch_page)")
        entries = fetch_via_coinbase_api(args.symbol, args.start, args.end)

    if entries:
        df = entries_to_df(entries)
        print(f"DataFrame {len(df)} from {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
        save_csv(df, args.symbol)
    else:
        print("No data collected")
