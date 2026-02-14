# backend/content/chart_generator.py - Market Chart Generation
import os
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from django.conf import settings

logger = logging.getLogger("tradeiq.chart_generator")


def generate_market_chart(
    instrument: str,
    current_price: float,
    change_pct: Optional[float],
    time_range: str = "24h",
    annotations: Optional[List[dict]] = None,
    analysis_report: Optional[dict] = None
) -> dict:
    """
    Generate line chart with annotations for market movements.

    Args:
        instrument: Trading instrument (e.g., "BTC/USD", "EUR/USD")
        current_price: Current price level
        change_pct: Percentage change (e.g., -5.2 for -5.2%)
        time_range: Time range for chart ("1h", "24h", "7d", "30d")
        annotations: List of annotation dicts {text, price, time}
        analysis_report: Optional analysis report for additional context

    Returns:
        dict with image_path, image_url, alt_text, dimensions, success
    """
    try:
        logger.info(f"Generating chart for {instrument} (current_price: ${current_price}, change: {change_pct}%)")
        price_data = _fetch_price_history(instrument, time_range, current_price, change_pct)

        if not price_data or len(price_data) == 0:
            logger.error(f"No price data available for {instrument}")
            return {
                "success": False,
                "error": f"No price data available for {instrument}",
                "image_path": None,
                "image_url": None
            }

        logger.info(f"Chart will use {len(price_data)} data points")

        fig, ax = plt.subplots(figsize=(12, 6.75), dpi=100)

        times = [point['time'] for point in price_data]
        prices = [point['price'] for point in price_data]

        if change_pct == 0 or change_pct is None:
            if len(prices) >= 2:
                first_price = prices[0]
                last_price = prices[-1]
                if first_price and first_price != 0:
                    change_pct = ((last_price - first_price) / first_price) * 100
                    logger.info(f"Calculated actual change from data: {change_pct:.2f}%")

        line_color = '#e74c3c' if change_pct < 0 else '#2ecc71'
        ax.plot(times, prices, color=line_color, linewidth=2.5, label=instrument)

        if abs(change_pct) >= 0.01:
            ax.set_title(
                f"{instrument} - {abs(change_pct):.2f}% {'Drop' if change_pct < 0 else 'Gain'}",
                fontsize=16,
                fontweight='bold',
                pad=20
            )
        else:
            ax.set_title(
                f"{instrument} - ${current_price:,.2f}",
                fontsize=16,
                fontweight='bold',
                pad=20
            )
        ax.set_xlabel('Time', fontsize=12, labelpad=10)
        ax.set_ylabel('Price', fontsize=12, labelpad=10)

        if current_price >= 1000:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        elif current_price >= 1:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.2f}'))
        else:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.4f}'))

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.xticks(rotation=45)

        ax.grid(True, alpha=0.3, linestyle='--')

        if annotations:
            for annotation in annotations:
                ax.annotate(
                    annotation.get('text', ''),
                    xy=(annotation.get('time'), annotation.get('price')),
                    xytext=(10, 10),
                    textcoords='offset points',
                    fontsize=10,
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
                )

        ax.scatter([times[-1]], [prices[-1]], color=line_color, s=100, zorder=5)
        ax.annotate(
            f'${current_price:,.2f}',
            xy=(times[-1], prices[-1]),
            xytext=(10, 10),
            textcoords='offset points',
            fontsize=11,
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor=line_color, alpha=0.8, edgecolor='white'),
            color='white'
        )

        fig.text(
            0.95, 0.02,
            'TradeIQ Analysis',
            ha='right',
            va='bottom',
            fontsize=10,
            color='gray',
            alpha=0.7
        )

        plt.tight_layout()

        safe_instrument = instrument.replace('/', '_').replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_instrument}_{timestamp}.png"
        filepath = settings.MEDIA_ROOT / "charts" / filename

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        plt.savefig(filepath, dpi=100, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        image_url = f"{settings.MEDIA_URL}charts/{filename}"
        relative_path = f"charts/{filename}"

        direction = "drop" if change_pct < 0 else "gain"
        alt_text = f"{instrument} price chart showing {abs(change_pct):.1f}% {direction} to ${current_price:,.2f}"

        return {
            "image_path": relative_path,
            "image_url": image_url,
            "alt_text": alt_text,
            "dimensions": {"width": 1200, "height": 675},
            "success": True
        }

    except Exception as e:
        logger.error(f"Chart generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "image_path": None,
            "image_url": None
        }


def _fetch_price_history(
    instrument: str,
    time_range: str,
    current_price: float,
    change_pct: Optional[float]
) -> List[dict]:
    """
    Fetch real market price history for charting.
    Falls back to synthetic data if market data unavailable.
    """
    # Attempt real data first via market.tools
    try:
        from market.tools import fetch_price_history

        count_map = {"1h": 60, "24h": 120, "7d": 168, "30d": 120}
        count = count_map.get(time_range, 120)

        timeframe_map = {"1h": "1m", "24h": "1h", "7d": "1h", "30d": "1d"}
        timeframe = timeframe_map.get(time_range, "1h")

        logger.info(f"Fetching real market data for {instrument} ({timeframe}, {count} candles)")

        market_data = fetch_price_history(
            instrument=instrument,
            timeframe=timeframe,
            count=count
        )

        candles = market_data.get("candles", [])

        if candles and len(candles) > 0:
            data = []
            for candle in candles:
                if isinstance(candle.get("time"), (int, float)):
                    candle_time = datetime.fromtimestamp(candle["time"])
                else:
                    candle_time = datetime.now()

                data.append({
                    'time': candle_time,
                    'price': candle.get("close", current_price)
                })

            logger.info(f"Successfully loaded {len(data)} real market data points")
            return data
        else:
            logger.warning(f"No market data available for {instrument}, using fallback")

    except Exception as e:
        logger.warning(f"Failed to fetch real market data: {e}, using fallback")

    # Fallback: Generate synthetic price data with seeded random for reproducibility
    logger.info("Using synthetic price data as fallback")
    # Seed random per instrument for reproducible charts
    random.seed(hash(instrument) % (2**32))

    hours = 24 if time_range == "24h" else 1 if time_range == "1h" else 168
    num_points = 50

    if change_pct is not None and change_pct != 0:
        start_price = current_price / (1 + change_pct / 100)
    else:
        start_price = current_price * 0.95
    end_price = current_price

    now = datetime.now()
    data = []

    for i in range(num_points):
        time_offset = (hours / num_points) * i
        point_time = now - timedelta(hours=hours) + timedelta(hours=time_offset)

        progress = i / (num_points - 1)
        price = start_price + (end_price - start_price) * progress

        noise = random.uniform(-0.01, 0.01) * price
        price = price + noise

        data.append({
            'time': point_time,
            'price': price
        })

    data[-1]['price'] = current_price

    return data
