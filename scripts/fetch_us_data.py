#!/usr/bin/env python3
"""
Data fetch script for US stocks using yfinance
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

# Constants
CONFIG_DIR = Path('data/config')
DATA_DIR = Path('data/indices')
STATUS_DIR = Path('data/status')
INDICES_FILE = CONFIG_DIR / 'indices.json'
UPDATE_LOG_FILE = STATUS_DIR / 'update-log.json'

# SMA periods
SMA_PERIODS = [30, 60, 90, 180, 240, 360]


def load_indices():
    """Load indices from config file."""
    if not INDICES_FILE.exists():
        return []

    with open(INDICES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('indices', [])


def get_us_indices(indices):
    """Filter US indices."""
    return [idx for idx in indices if idx.get('region') == 'US']


def calculate_sma(close_prices, period):
    """Calculate SMA series."""
    if len(close_prices) < period:
        return [None] * len(close_prices)

    result = [None] * (period - 1)
    for i in range(period - 1, len(close_prices)):
        result.append(sum(close_prices[i - period + 1:i + 1]) / period)
    return result


def calculate_deviation(close, sma):
    """Calculate deviation (close - SMA)."""
    if sma is None:
        return None
    return round(close - sma, 2)


def process_stock_data(df, code):
    """Process stock data and calculate SMAs and deviations."""
    if df.empty:
        return {'data': []}

    df = df.sort_values('Date')
    close_prices = df['Close'].tolist()

    # Calculate SMAs
    sma_data = {}
    for period in SMA_PERIODS:
        sma_data[f'sma{period}'] = calculate_sma(close_prices, period)

    # Build result
    result = []
    for i, row in df.iterrows():
        data_point = {
            'date': row['Date'].strftime('%Y-%m-%d'),
            'close': round(row['Close'], 2),
        }

        for period in SMA_PERIODS:
            sma_val = sma_data[f'sma{period}'][i]
            data_point[f'sma{period}'] = round(sma_val, 2) if sma_val is not None else None
            data_point[f'deviation{period}'] = calculate_deviation(row['Close'], sma_val)

        result.append(data_point)

    return {'code': code, 'data': result}


def fetch_yahoo_data(code, start_date, end_date):
    """Fetch data from Yahoo Finance."""
    try:
        ticker = yf.Ticker(code)
        df = ticker.history(start=start_date, end=end_date)

        if df.empty:
            return None

        return df
    except Exception as e:
        print(f"Error fetching {code}: {e}")
        return None


def save_data_by_year(code, data):
    """Save data split by year."""
    if not data.get('data'):
        return 0

    year_data = {}
    for item in data['data']:
        year = item['date'][:4]
        if year not in year_data:
            year_data[year] = []
        year_data[year].append(item)

    saved_count = 0
    for year, records in year_data.items():
        year_file = DATA_DIR / f"{code}-{year}.json"
        year_data_obj = {
            'code': code,
            'year': int(year),
            'data': records
        }

        if year_file.exists():
            with open(year_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
                existing_data = {item['date']: item for item in existing.get('data', [])}
                for item in records:
                    existing_data[item['date']] = item
                year_data_obj['data'] = list(existing_data.values())
                year_data_obj['data'].sort(key=lambda x: x['date'])

        with open(year_file, 'w', encoding='utf-8') as f:
            json.dump(year_data_obj, f, ensure_ascii=False, indent=2)

        saved_count += len(records)
        print(f"Saved {len(records)} records for {code}-{year}")

    return saved_count


def update_log(status, indices_updated, message):
    """Update the log file."""
    STATUS_DIR.mkdir(parents=True, exist_ok=True)

    log_entry = {
        'region': 'US',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'status': status,
        'indicesUpdated': indices_updated,
        'message': message
    }

    logs = []
    if UPDATE_LOG_FILE.exists():
        with open(UPDATE_LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f).get('logs', [])

    logs.append(log_entry)
    logs = logs[-100:]

    with open(UPDATE_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump({'logs': logs}, f, ensure_ascii=False, indent=2)


def get_date_range(init_mode):
    """Get date range for fetching."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    if init_mode:
        start_date = end_date - timedelta(days=365 * 5)

    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


def main():
    parser = argparse.ArgumentParser(description='Fetch US stock data from Yahoo Finance')
    parser.add_argument('--init', type=str, default='false', help='Initial full fetch (true/false)')
    args = parser.parse_args()

    init_mode = args.init.lower() == 'true'

    print(f"Starting US stock data fetch, init: {init_mode}")

    indices = load_indices()
    us_indices = get_us_indices(indices)

    if not us_indices:
        print("No US indices found")
        update_log('success', 0, 'No indices configured')
        return

    start_date, end_date = get_date_range(init_mode)

    total_updated = 0
    failed_indices = []

    for idx in us_indices:
        code = idx.get('code')
        name = idx.get('name', code)

        print(f"Processing {name} ({code})")

        df = fetch_yahoo_data(code, start_date, end_date)

        if df is not None and not df.empty:
            processed_data = process_stock_data(df, code)
            saved = save_data_by_year(code, processed_data)
            total_updated += saved
            print(f"Successfully processed {code}: {saved} records")
        else:
            failed_indices.append(code)
            print(f"Failed to fetch data for {code}")

    if failed_indices:
        update_log('failed', total_updated, f"Failed: {', '.join(failed_indices)}")
    else:
        update_log('success', total_updated, '')

    print(f"Data fetch completed. Updated {total_updated} records.")


if __name__ == '__main__':
    main()