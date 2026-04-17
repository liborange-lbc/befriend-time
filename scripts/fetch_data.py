#!/usr/bin/env python3
"""
Data fetch script for A-share and HK stocks using Tushare
"""

import os
import sys
import json
import argparse
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import tushare as ts
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CONFIG_DIR = Path('data/config')
DATA_DIR = Path('data/indices')
STATUS_DIR = Path('data/status')
INDICES_FILE = CONFIG_DIR / 'indices.json'
UPDATE_LOG_FILE = STATUS_DIR / 'update-log.json'

# SMA periods
SMA_PERIODS = [30, 60, 90, 180, 240, 360]

# Retry settings
MAX_RETRIES = 10
RETRY_INTERVAL = 30 * 60  # 30 minutes in seconds


def load_indices() -> list:
    """Load indices from config file."""
    if not INDICES_FILE.exists():
        logger.warning(f"Indices config not found: {INDICES_FILE}")
        return []

    with open(INDICES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('indices', [])


def get_indices_by_region(indices: list, region: str) -> list:
    """Filter indices by region."""
    return [idx for idx in indices if idx.get('region') == region]


def calculate_sma(close_prices: list, period: int) -> list:
    """Calculate SMA series."""
    if len(close_prices) < period:
        return [None] * len(close_prices)

    result = [None] * (period - 1)
    for i in range(period - 1, len(close_prices)):
        result.append(sum(close_prices[i - period + 1:i + 1]) / period)
    return result


def calculate_deviation(close: float, sma: Optional[float]) -> Optional[float]:
    """Calculate deviation (close - SMA)."""
    if sma is None:
        return None
    return round(close - sma, 2)


def process_stock_data(df: pd.DataFrame) -> dict:
    """Process stock data and calculate SMAs and deviations."""
    if df.empty:
        return {'data': []}

    df = df.sort_values('trade_date')
    close_prices = df['close'].tolist()

    # Calculate SMAs for all periods
    sma_data = {}
    for period in SMA_PERIODS:
        sma_data[f'sma{period}'] = calculate_sma(close_prices, period)

    # Build result data
    result = []
    for i, row in df.iterrows():
        data_point = {
            'date': row['trade_date'],
            'close': round(row['close'], 2),
        }

        # Add SMAs and deviations
        for period in SMA_PERIODS:
            sma_val = sma_data[f'sma{period}'][i]
            data_point[f'sma{period}'] = round(sma_val, 2) if sma_val is not None else None
            data_point[f'deviation{period}'] = calculate_deviation(row['close'], sma_val)

        result.append(data_point)

    return {'data': result}


def fetch_tushare_data(code: str, start_date: str, end_date: str, retry_count: int = 0) -> Optional[pd.DataFrame]:
    """Fetch data from Tushare API with retry logic."""
    try:
        token = os.environ.get('TUSHARE_TOKEN')
        if not token:
            logger.error("TUSHARE_TOKEN not found in environment variables")
            return None

        pro = ts.pro_api(token)

        # Determine ts_code format
        if '.SH' in code:
            ts_code = code
        elif '.SZ' in code:
            ts_code = code
        else:
            ts_code = code

        logger.info(f"Fetching data for {ts_code} from {start_date} to {end_date}")

        df = pro.daily(
            ts_code=ts_code,
            start_date=start_date.replace('-', ''),
            end_date=end_date.replace('-', '')
        )

        if df is None or df.empty:
            logger.warning(f"No data returned for {code}")
            return None

        return df

    except Exception as e:
        logger.error(f"Error fetching data for {code}: {e}")

        if retry_count < MAX_RETRIES:
            logger.info(f"Retrying in {RETRY_INTERVAL} seconds... ({retry_count + 1}/{MAX_RETRIES})")
            time.sleep(RETRY_INTERVAL)
            return fetch_tushare_data(code, start_date, end_date, retry_count + 1)
        else:
            logger.error(f"Max retries reached for {code}")
            return None


def save_data_by_year(code: str, data: dict) -> int:
    """Save data split by year."""
    if not data.get('data'):
        return 0

    # Group data by year
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

        # Check if file exists and merge
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
        logger.info(f"Saved {len(records)} records for {code}-{year}")

    return saved_count


def update_log(region: str, status: str, indices_updated: int, message: str, retry_count: int = 0):
    """Update the log file."""
    STATUS_DIR.mkdir(parents=True, exist_ok=True)

    log_entry = {
        'region': region,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'status': status,
        'indicesUpdated': indices_updated,
        'message': message,
        'retryCount': retry_count if retry_count > 0 else None
    }

    # Read existing logs
    logs = []
    if UPDATE_LOG_FILE.exists():
        with open(UPDATE_LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f).get('logs', [])

    # Add new entry and keep last 100
    logs.append(log_entry)
    logs = logs[-100:]

    with open(UPDATE_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump({'logs': logs}, f, ensure_ascii=False, indent=2)


def get_date_range(init_mode: bool) -> tuple:
    """Get date range for fetching."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # Default: last 7 days

    if init_mode:
        # Full historical data - last 5 years
        start_date = end_date - timedelta(days=365 * 5)

    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


def main():
    parser = argparse.ArgumentParser(description='Fetch stock data from Tushare')
    parser.add_argument('--region', type=str, required=True, choices=['CN', 'HK'],
                        help='Region: CN for A-share, HK for HK stocks')
    parser.add_argument('--init', type=str, default='false',
                        help='Initial full fetch (true/false)')
    args = parser.parse_args()

    init_mode = args.init.lower() == 'true'
    region = args.region

    logger.info(f"Starting data fetch for region: {region}, init: {init_mode}")

    # Load indices
    indices = load_indices()
    region_indices = get_indices_by_region(indices, region)

    if not region_indices:
        logger.warning(f"No indices found for region {region}")
        update_log(region, 'success', 0, 'No indices configured')
        return

    # Get date range
    start_date, end_date = get_date_range(init_mode)

    total_updated = 0
    failed_indices = []

    for idx in region_indices:
        code = idx.get('code')
        name = idx.get('name', code)

        logger.info(f"Processing {name} ({code})")

        df = fetch_tushare_data(code, start_date, end_date)

        if df is not None and not df.empty:
            processed_data = process_stock_data(df)
            saved = save_data_by_year(code, processed_data)
            total_updated += saved
            logger.info(f"Successfully processed {code}: {saved} records")
        else:
            failed_indices.append(code)
            logger.error(f"Failed to fetch data for {code}")

    # Update log
    if failed_indices:
        update_log(region, 'failed', total_updated, f"Failed indices: {', '.join(failed_indices)}")
    else:
        update_log(region, 'success', total_updated, '')

    logger.info(f"Data fetch completed. Updated {total_updated} records.")


if __name__ == '__main__':
    main()