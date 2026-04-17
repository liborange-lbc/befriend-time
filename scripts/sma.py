"""
SMA (Simple Moving Average) calculation utilities
"""

import pandas as pd
import numpy as np
from typing import List, Optional


def calculate_sma(prices: List[float], period: int) -> Optional[float]:
    """
    Calculate Simple Moving Average for a given period.

    Args:
        prices: List of closing prices
        period: Number of days for SMA calculation

    Returns:
        SMA value or None if not enough data points
    """
    if len(prices) < period:
        return None
    return np.mean(prices[-period:])


def calculate_sma_series(close_prices: List[float], period: int) -> List[Optional[float]]:
    """
    Calculate SMA series for entire price list.

    Args:
        close_prices: List of closing prices
        period: Number of days for SMA calculation

    Returns:
        List of SMA values (first period-1 values will be None)
    """
    if len(close_prices) < period:
        return [None] * len(close_prices)

    result = [None] * (period - 1)
    for i in range(period - 1, len(close_prices)):
        sma = np.mean(close_prices[i - period + 1:i + 1])
        result.append(sma)

    return result


def calculate_all_smas(close_prices: List[float]) -> dict:
    """
    Calculate all SMA periods (30, 60, 90, 180, 240, 360 days).

    Args:
        close_prices: List of closing prices

    Returns:
        Dictionary with SMA values for each period
    """
    periods = [30, 60, 90, 180, 240, 360]
    sma_dict = {}

    for period in periods:
        sma_dict[f'sma{period}'] = calculate_sma_series(close_prices, period)

    return sma_dict


def calculate_deviation(close_price: float, sma_value: Optional[float]) -> Optional[float]:
    """
    Calculate deviation (close price - SMA).

    Args:
        close_price: Current closing price
        sma_value: SMA value

    Returns:
        Deviation value or None if SMA is None
    """
    if sma_value is None:
        return None
    return close_price - sma_value


def calculate_deviation_percent(close_price: float, sma_value: Optional[float]) -> Optional[float]:
    """
    Calculate deviation as percentage.

    Args:
        close_price: Current closing price
        sma_value: SMA value

    Returns:
        Deviation percentage or None if SMA is None
    """
    if sma_value is None or sma_value == 0:
        return None
    return ((close_price - sma_value) / sma_value) * 100


if __name__ == '__main__':
    # Test
    prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
              110, 111, 112, 113, 114, 115, 116, 117, 118, 119,
              120, 121, 122, 123, 124, 125, 126, 127, 128, 129]

    print("Test SMA30:", calculate_sma(prices, 30))
    print("Test SMA60:", calculate_sma(prices, 60))

    sma30_series = calculate_sma_series(prices, 30)
    print("SMA30 series (first 35):", sma30_series[:35])

    # Test deviation
    close = 130
    sma = 125
    print("Deviation:", calculate_deviation(close, sma))
    print("Deviation %:", calculate_deviation_percent(close, sma))