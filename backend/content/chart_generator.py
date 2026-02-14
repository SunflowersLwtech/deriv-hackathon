# backend/content/chart_generator.py - Market Chart Generation
import os
import logging
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
    change_pct: float,
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
        {
            "image_path": "/path/to/chart.png",
            "image_url": "/media/charts/BTC_USD_20260214_123456.png",
            "alt_text": "BTC/USD price chart showing -5.2% drop to $95,000",
            "dimensions": {"width": 1200, "height": 675}
        }
    """
    try:
        # Fetch historical price data
        price_data = _fetch_price_history(instrument, time_range, current_price, change_pct)

        # Create figure with proper dimensions (16:9 ratio for social media)
        fig, ax = plt.subplots(figsize=(12, 6.75), dpi=100)

        # Extract times and prices
        times = [point['time'] for point in price_data]
        prices = [point['price'] for point in price_data]

        # Plot line chart
        line_color = '#e74c3c' if change_pct < 0 else '#2ecc71'  # Red for down, green for up
        ax.plot(times, prices, color=line_color, linewidth=2.5, label=instrument)

        # Format chart
        ax.set_title(
            f"{instrument} - {abs(change_pct):.1f}% {'Drop' if change_pct < 0 else 'Gain'}",
            fontsize=16,
            fontweight='bold',
            pad=20
        )
        ax.set_xlabel('Time', fontsize=12, labelpad=10)
        ax.set_ylabel('Price', fontsize=12, labelpad=10)

        # Format y-axis with proper price formatting
        if current_price >= 1000:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        elif current_price >= 1:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.2f}'))
        else:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.4f}'))

        # Format x-axis with time formatting
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.xticks(rotation=45)

        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--')

        # Add annotations
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

        # Add current price marker
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

        # Add watermark
        fig.text(
            0.95, 0.02,
            '📊 TradeIQ Analysis',
            ha='right',
            va='bottom',
            fontsize=10,
            color='gray',
            alpha=0.7
        )

        # Tight layout
        plt.tight_layout()

        # Save chart
        safe_instrument = instrument.replace('/', '_').replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_instrument}_{timestamp}.png"
        filepath = settings.MEDIA_ROOT / "charts" / filename

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        plt.savefig(filepath, dpi=100, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        # Generate URL
        image_url = f"{settings.MEDIA_URL}charts/{filename}"

        # Generate relative path for backend use (e.g., "charts/BTC_USD_20260214.png")
        relative_path = f"charts/{filename}"

        # Generate alt text
        direction = "drop" if change_pct < 0 else "gain"
        alt_text = f"{instrument} price chart showing {abs(change_pct):.1f}% {direction} to ${current_price:,.2f}"

        return {
            "image_path": relative_path,  # Relative path for backend to reconstruct full path
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
    change_pct: float
) -> List[dict]:
    """
    Fetch or generate price history for charting.

    In production, this would call the market/tools.py fetch_price_data() function.
    For now, we'll generate synthetic data based on current price and change.
    """
    # TODO: Replace with actual market data fetch
    # from market.tools import fetch_price_data
    # return fetch_price_data(instrument, time_range)

    # Generate synthetic price data for demo
    hours = 24 if time_range == "24h" else 1 if time_range == "1h" else 168
    num_points = 50

    start_price = current_price / (1 + change_pct / 100)  # Calculate starting price
    end_price = current_price

    now = datetime.now()
    data = []

    for i in range(num_points):
        time_offset = (hours / num_points) * i
        point_time = now - timedelta(hours=hours) + timedelta(hours=time_offset)

        # Linear interpolation with some noise
        progress = i / (num_points - 1)
        price = start_price + (end_price - start_price) * progress

        # Add some realistic volatility (±1% random walk)
        import random
        noise = random.uniform(-0.01, 0.01) * price
        price = price + noise

        data.append({
            'time': point_time,
            'price': price
        })

    # Ensure last point is exact current price
    data[-1]['price'] = current_price

    return data


def generate_comparison_chart(
    instruments: List[str],
    time_range: str = "24h"
) -> dict:
    """
    Generate multi-instrument comparison chart.

    Future enhancement for comparing multiple assets.
    """
    # TODO: Implement multi-instrument comparison
    raise NotImplementedError("Comparison charts coming soon")
