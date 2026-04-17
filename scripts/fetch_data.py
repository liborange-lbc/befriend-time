#!/usr/bin/env python3
"""
Data fetch script for multiple data sources: tushare, csindex, yfinance
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
MAX_RETRIES = 3
RETRY_DELAY = 10


def load_indices() -> list:
    """Load indices from config file."""
    if not INDICES_FILE.exists():
        logger.warning(f"Indices config not found: {INDICES_FILE}")
        return []

    with open(INDICES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('indices', [])


def get_indices_by_source(indices: list, source: str) -> list:
    """Filter indices by data source."""
    return [idx for idx in indices if idx.get('source') == source]


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

    df = df.sort_values('date')
    close_prices = df['close'].tolist()

    # Calculate SMAs for all periods
    sma_data = {}
    for period in SMA_PERIODS:
        sma_data[f'sma{period}'] = calculate_sma(close_prices, period)

    # Build result data
    result = []
    for i, row in df.iterrows():
        data_point = {
            'date': row['date'],
            'close': round(row['close'], 2),
        }

        # Add SMAs and deviations
        for period in SMA_PERIODS:
            sma_val = sma_data[f'sma{period}'][i]
            data_point[f'sma{period}'] = round(sma_val, 2) if sma_val is not None else None
            data_point[f'deviation{period}'] = calculate_deviation(row['close'], sma_val)

        result.append(data_point)

    return {'data': result}


def fetch_csindex_data(code: str, start_date: str, end_date: str, retry_count: int = 0) -> Optional[pd.DataFrame]:
    """Fetch data from CSI Index API."""
    try:
        # CSI Index API endpoint
        url = "https://www.csindex.com.cn/csindex-home/index/quotation"

        params = {
            "indexCode": code,
            "startDate": start_date.replace('-', ''),
            "endDate": end_date.replace('-', '')
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://www.csindex.com.cn"
        }

        logger.info(f"Fetching CSI data for {code} from {start_date} to {end_date}")

        response = requests.get(url, params=params, headers=headers, timeout=30)

        if response.status_code != 200:
            logger.error(f"CSI API returned status {response.status_code}")
            if retry_count < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                return fetch_csindex_data(code, start_date, end_date, retry_count + 1)
            return None

        data = response.json()

        # Check API response format
        if data.get('code') != '200' or 'data' not in data:
            logger.warning(f"CSI API error: {data.get('msg', 'Unknown error')}")
            return None

        records = data['data']

        if not records:
            logger.warning(f"No records for {code}")
            return None

        # Transform to DataFrame - field names from API response
        df = pd.DataFrame(records)
        df = df.rename(columns={
            'tradeDate': 'date',
            'close': 'close'
        })
        # Convert date from YYYYMMDD to YYYY-MM-DD
        df['date'] = df['date'].astype(str)
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
        df['close'] = df['close'].astype(float)

        return df[['date', 'close']]

    except Exception as e:
        logger.error(f"Error fetching CSI data for {code}: {e}")
        if retry_count < MAX_RETRIES:
            time.sleep(RETRY_DELAY)
            return fetch_csindex_data(code, start_date, end_date, retry_count + 1)
        return None


def fetch_yfinance_data(code: str, start_date: str, end_date: str, retry_count: int = 0) -> Optional[pd.DataFrame]:
    """Fetch data from Yahoo Finance."""
    try:
        import yfinance as yf

        logger.info(f"Fetching Yahoo Finance data for {code} from {start_date} to {end_date}")

        ticker = yf.Ticker(code)
        df = ticker.history(start=start_date, end=end_date)

        if df.empty:
            logger.warning(f"No data returned for {code}")
            if retry_count < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (retry_count + 1))
                return fetch_yfinance_data(code, start_date, end_date, retry_count + 1)
            return None

        df = df.reset_index()
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df = df.rename(columns={'Date': 'date', 'Close': 'close'})

        return df[['date', 'close']]

    except Exception as e:
        logger.error(f"Error fetching Yahoo data for {code}: {e}")
        if retry_count < MAX_RETRIES:
            time.sleep(RETRY_DELAY * (retry_count + 1))
            return fetch_yfinance_data(code, start_date, end_date, retry_count + 1)
        return None


def fetch_tushare_data(code: str, start_date: str, end_date: str, retry_count: int = 0) -> Optional[pd.DataFrame]:
    """Fetch data from Tushare API."""
    try:
        import tushare as ts

        token = os.environ.get('TUSHARE_TOKEN')
        if not token:
            logger.error("TUSHARE_TOKEN not found in environment variables")
            return None

        pro = ts.pro_api(token)

        logger.info(f"Fetching Tushare data for {code} from {start_date} to {end_date}")

        df = pro.daily(
            ts_code=code,
            start_date=start_date.replace('-', ''),
            end_date=end_date.replace('-', '')
        )

        if df is None or df.empty:
            logger.warning(f"No data returned for {code}")
            return None

        df = df.rename(columns={'trade_date': 'date', 'close': 'close'})
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

        return df[['date', 'close']]

    except Exception as e:
        logger.error(f"Error fetching Tushare data for {code}: {e}")
        if retry_count < MAX_RETRIES:
            time.sleep(RETRY_DELAY)
            return fetch_tushare_data(code, start_date, end_date, retry_count + 1)
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


def update_log(source: str, status: str, indices_updated: int, message: str):
    """Update the log file."""
    STATUS_DIR.mkdir(parents=True, exist_ok=True)

    log_entry = {
        'source': source,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'status': status,
        'indicesUpdated': indices_updated,
        'message': message
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


def fetch_data_for_source(indices: list, source: str, start_date: str, end_date: str, init_mode: bool):
    """Fetch data for a specific source."""
    source_indices = get_indices_by_source(indices, source)

    if not source_indices:
        logger.info(f"No indices found for source: {source}")
        return 0, []

    total_updated = 0
    failed_indices = []

    fetch_func = {
        'csindex': fetch_csindex_data,
        'yfinance': fetch_yfinance_data,
        'tushare': fetch_tushare_data
    }.get(source)

    if not fetch_func:
        logger.error(f"Unknown source: {source}")
        return 0, []

    for idx in source_indices:
        code = idx.get('code')
        name = idx.get('name', code)
        region = idx.get('region', 'unknown')

        logger.info(f"Processing {name} ({code}) from {region}")

        # Add delay between requests
        time.sleep(2)

        df = fetch_func(code, start_date, end_date)

        if df is not None and not df.empty:
            processed_data = process_stock_data(df)
            saved = save_data_by_year(code, processed_data)
            total_updated += saved
            logger.info(f"Successfully processed {code}: {saved} records")
        else:
            failed_indices.append(code)
            logger.error(f"Failed to fetch data for {code}")

    return total_updated, failed_indices


def main():
    parser = argparse.ArgumentParser(description='Fetch stock data from multiple sources')
    parser.add_argument('--source', type=str, default='all',
                        choices=['all', 'csindex', 'yfinance', 'tushare'],
                        help='Data source to fetch from')
    parser.add_argument('--init', type=str, default='false',
                        help='Initial full fetch (true/false)')
    args = parser.parse_args()

    init_mode = args.init.lower() == 'true'
    source = args.source

    logger.info(f"Starting data fetch, source: {source}, init: {init_mode}")

    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Load indices
    indices = load_indices()

    if not indices:
        logger.error("No indices configured")
        return

    # Get date range
    start_date, end_date = get_date_range(init_mode)

    # Determine which sources to fetch
    if source == 'all':
        sources = ['csindex', 'yfinance', 'tushare']
    else:
        sources = [source]

    total_updated = 0
    all_failed = []

    for src in sources:
        updated, failed = fetch_data_for_source(indices, src, start_date, end_date, init_mode)
        total_updated += updated
        all_failed.extend(failed)

    # Update log
    if all_failed:
        update_log(source, 'failed', total_updated, f"Failed: {', '.join(all_failed)}")
    else:
        update_log(source, 'success', total_updated, '')

    logger.info(f"Data fetch completed. Updated {total_updated} records.")


if __name__ == '__main__':
    main()