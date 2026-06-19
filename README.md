# Daily Breakout Swing Trading Backtester

A Python backtesting engine for a **daily breakout swing trading strategy** — tested across up to 2 years of historical data — with dynamic position sizing, a 1:2 Risk-Reward ratio, and a full trade-by-trade performance tearsheet.

---

## What This Does

Unlike intraday strategies that open and close within a single day, swing trades can stay open for multiple days — you enter when a breakout happens, and hold until your stop-loss or target is hit, even if that takes a week.

This engine simulates exactly that: for each day, it checks whether today's price has broken the previous day's high or low. If it has, it enters a trade and tracks it across subsequent days until it resolves.

This means the backtest accounts for **multi-day holding periods**, which makes it significantly more realistic than a same-day exit model.

---

## Strategy Logic

```
1. Define Range = Previous day's High and Low
2. If today's High breaks ABOVE previous day's High → Enter LONG
   - Entry = Previous day's High
   - Stop Loss = Previous day's Low
   - Target = Entry + (2 × Range)
3. If today's Low breaks BELOW previous day's Low → Enter SHORT
   - Entry = Previous day's Low
   - Stop Loss = Previous day's High
   - Target = Entry - (2 × Range)
4. Position size = floor((2% of capital) / Range)
5. Hold across days until SL or Target is hit
6. Only one open trade at a time
```

---

## How to Run

**1. Install dependencies**
```bash
pip install yfinance pandas numpy
```

**2. Run the script**
```bash
python main.py
```

**3. Follow the prompt**
```
Enter stock ticker (e.g., RELIANCE, TCS, or ^NSEI for NIFTY 50): TCS
```
The script automatically appends `.NS` for Indian stocks.

---

## Example Output

```
--- Running Daily Breakout Backtest for: TCS.NS ---
--- Period: 2y ---

--- Performance Summary (Daily Breakout) ---
Starting Balance: Rs 100,000.00
Final Balance:    Rs 118,750.00
Total PnL (Rs):   Rs 18,750.00
---------------------------
Total Days Tested: 502
Total Trades Closed: 87
---------------------------
Wins (Target Hit): 47
Losses (Stop Hit): 36
Held to EOD: 4
Win Rate: 54.02%
---------------------------
Profit Factor (Rs): 1.61
Average Win (Rs):   Rs 1,820.00
Average Loss (Rs):  Rs -910.00
```

---

## How This Differs From the ORB Backtester

| Feature | ORB (ORB.py) | Daily Breakout (main.py) |
|---------|-------------|--------------------------|
| Timeframe | Intraday (5-minute) | Daily (swing trade) |
| Data period | Max 60 days | Up to 2 years |
| Trade duration | Same day | Multiple days |
| Range definition | First 5-min candle | Previous day's H/L |
| Best for | Active intraday traders | Swing / positional traders |

---

## Configuration

```python
PERIOD_TO_TEST   = '2y'     # Test period (1y, 2y, 5y — daily data has no limit)
RR_RATIO         = 2.0      # Risk-Reward ratio
STARTING_BALANCE = 100000.0 # Starting capital in ₹
RISK_PER_TRADE   = 0.02     # 2% of current capital risked per trade
```

---

## Performance Metrics Explained

| Metric | What It Tells You |
|--------|------------------|
| **Win Rate** | % of closed trades that hit target. With a 1:2 RR, you only need >33% to be profitable |
| **Profit Factor** | Total gross profit ÷ total gross loss. >1.0 is profitable; >1.5 is considered strong |
| **Avg Win / Avg Loss** | Should be ~2:1 due to the fixed RR ratio |
| **Held to EOD** | Trades still open at the end of the backtest period |

---

## Tech Stack

| Library | Purpose |
|---------|---------|
| `yfinance` | Daily OHLCV data (up to years of history) |
| `pandas` | Trade log, results DataFrame, analysis |
| `numpy` | Fast array-based price access |
| `math` | Integer position sizing via `floor()` |

---

## Key Design Decisions

**Why use the previous day's range, not same-day?** Same-day entry and range definition creates lookahead bias — you'd be using information (the day's high/low) that wasn't available at the time of entry. Previous day's range is fully known before the market opens.

**Why only one trade at a time?** This prevents over-leveraging and keeps the risk model clean. A more advanced version could allow pyramiding into positions, but that requires additional risk controls.

**Instant win/loss handling:** If a breakout day also hits the target or stop on the same candle, the trade is settled immediately with no multi-day carry. This prevents false carry-over logic.

---

## Limitations

- Slippage, brokerage, and STT/taxes are not modelled
- Assumes execution at the exact breakout price — in live trading, there can be gaps
- Past performance does not predict future results

---

*This is not financial advice. Built for educational and research purposes.*
