import yfinance as yf
import pandas as pd
import math
import numpy as np


def run_daily_breakout_backtest(ticker_symbol,
                                starting_balance,
                                risk_per_trade_percent=0.02,
                                period='2y',  # We can now test over years
                                risk_reward_ratio=2.0):
    """
    Runs a backtest of a Daily Breakout (Swing Trading) strategy.

    Strategy:
    1. Define range as the High/Low of the *previous day*.
    2. Enter a trade if the current day's High/Low breaks that range.
    3. Hold the trade (swing trade) until Stop Loss or Target Profit is hit.
    """

    # --- 1. Fetch Historical Data ---
    # We now fetch '1d' (daily) data for a longer period
    try:
        data = yf.download(ticker_symbol,
                           period=period,
                           interval='1d',
                           auto_adjust=False,
                           progress=False)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    if data.empty:
        print(f"No data fetched for {ticker_symbol}.")
        return

    print(f"--- Running Daily Breakout Backtest for: {ticker_symbol} ---")
    print(f"--- Period: {period} ---")

    # --- 2. Initialize Backtest State ---
    results_list = []
    current_balance = starting_balance

    # Extract data into NumPy arrays for safe access
    try:
        high_values = data['High'].values
        low_values = data['Low'].values
        close_values = data['Close'].values
    except KeyError:
        print("Error: DataFrame missing 'High', 'Low', or 'Close' columns.")
        return

    # These are now "global" for the whole backtest, not reset daily
    trade_taken = False
    trade_type = None
    entry_price = 0.0
    stop_loss = 0.0
    target_profit = 0.0
    number_of_shares = 0
    trade_range = 0.0
    target_points = 0.0
    entry_date = None

    # --- 3. Loop Through Each Day (Swing Trading Logic) ---
    # We start from index 1 to have a "previous day" (index 0)
    for i in range(1, len(data)):
        # Get today's and previous day's data from NumPy arrays
        today_high = high_values[i]
        today_low = low_values[i]

        prev_high = high_values[i - 1]
        prev_low = low_values[i - 1]

        # --- A. Check for Trade Exit (if we are in a trade) ---
        if trade_taken:
            trade_closed = False

            if trade_type == 'LONG':
                # Check for Stop Loss first
                if today_low <= stop_loss:
                    exit_price = stop_loss
                    pnl_points = exit_price - entry_price
                    outcome = 'SL_HIT'
                    trade_closed = True
                # Check for Target Profit
                elif today_high >= target_profit:
                    exit_price = target_profit
                    pnl_points = exit_price - entry_price
                    outcome = 'TARGET_HIT'
                    trade_closed = True

            elif trade_type == 'SHORT':
                # Check for Stop Loss first
                if today_high >= stop_loss:
                    exit_price = stop_loss
                    pnl_points = entry_price - exit_price
                    outcome = 'SL_HIT'
                    trade_closed = True
                # Check for Target Profit
                elif today_low <= target_profit:
                    exit_price = target_profit
                    pnl_points = entry_price - exit_price
                    outcome = 'TARGET_HIT'
                    trade_closed = True

            if trade_closed:
                pnl_rs = pnl_points * number_of_shares
                current_balance += pnl_rs
                results_list.append({
                    'entry_date': entry_date,
                    'exit_date': data.index[i].date(),  # Use index to get date
                    'outcome': outcome,
                    'pnl_points': pnl_points,
                    'pnl_rs': pnl_rs
                })
                # Reset all trade parameters
                trade_taken = False
                number_of_shares = 0
                trade_type = None

        # --- B. Check for Trade Entry (if we are NOT in a trade) ---
        if not trade_taken:
            # Define the "range" as the previous day's High/Low
            opening_range_high = prev_high
            opening_range_low = prev_low

            trade_range = opening_range_high - opening_range_low
            if trade_range <= 0:  # This comparison is now safe
                continue

            target_points = trade_range * risk_reward_ratio

            # Calculate Position Size *before* entry
            risk_per_trade_rs = current_balance * risk_per_trade_percent
            number_of_shares = math.floor(risk_per_trade_rs / trade_range)

            if number_of_shares == 0:
                continue  # Insufficient capital for this trade's risk

            # Check for breakouts on the *current* day's candle
            # (We already got today_high and today_low at the start of the loop)

            # Check for LONG entry
            if today_high > opening_range_high:
                entry_price = opening_range_high
                stop_loss = opening_range_low
                target_profit = entry_price + target_points

                # Check if it was an "instant loss" (hit SL on same day)
                if today_low <= stop_loss:
                    pnl_points = stop_loss - entry_price
                    pnl_rs = pnl_points * number_of_shares
                    current_balance += pnl_rs
                    results_list.append({
                        'entry_date': data.index[i].date(),
                        'exit_date': data.index[i].date(),
                        'outcome': 'SL_HIT', 'pnl_points': pnl_points, 'pnl_rs': pnl_rs
                    })
                    continue  # Don't take trade

                # Check if it was an "instant win" (hit TP on same day)
                elif today_high >= target_profit:
                    pnl_points = target_profit - entry_price
                    pnl_rs = pnl_points * number_of_shares
                    current_balance += pnl_rs
                    results_list.append({
                        'entry_date': data.index[i].date(),
                        'exit_date': data.index[i].date(),
                        'outcome': 'TARGET_HIT', 'pnl_points': pnl_points, 'pnl_rs': pnl_rs
                    })
                    continue  # Don't take trade

                # Otherwise, the trade is open and carried over
                else:
                    trade_taken = True
                    trade_type = 'LONG'
                    entry_date = data.index[i].date()

            # Check for SHORT entry (only if no LONG was taken)
            elif not trade_taken and today_low < opening_range_low:
                entry_price = opening_range_low
                stop_loss = opening_range_high
                target_profit = entry_price - target_points

                # Check for "instant loss" (hit SL on same day)
                if today_high >= stop_loss:
                    pnl_points = entry_price - stop_loss
                    pnl_rs = pnl_points * number_of_shares
                    current_balance += pnl_rs
                    results_list.append({
                        'entry_date': data.index[i].date(),
                        'exit_date': data.index[i].date(),
                        'outcome': 'SL_HIT', 'pnl_points': -trade_range, 'pnl_rs': pnl_rs
                    })
                    continue  # Don't take trade

                # Check for "instant win" (hit TP on same day)
                elif today_low <= target_profit:
                    pnl_points = entry_price - target_profit
                    pnl_rs = pnl_points * number_of_shares
                    current_balance += pnl_rs
                    results_list.append({
                        'entry_date': data.index[i].date(),
                        'exit_date': data.index[i].date(),
                        'outcome': 'TARGET_HIT', 'pnl_points': target_points, 'pnl_rs': pnl_rs
                    })
                    continue  # Don't take trade

                # Otherwise, the trade is open and carried over
                else:
                    trade_taken = True
                    trade_type = 'SHORT'
                    entry_date = data.index[i].date()

    # --- 4. End of Backtest - Close any open trade ---
    if trade_taken:
        last_price = close_values[-1]  # Use NumPy array
        if trade_type == 'LONG':
            pnl_points = last_price - entry_price
        else:  # SHORT
            pnl_points = entry_price - last_price

        pnl_rs = pnl_points * number_of_shares
        current_balance += pnl_rs
        results_list.append({
            'entry_date': entry_date,
            'exit_date': data.index[-1].date(),
            'outcome': 'EOD_OPEN', 'pnl_points': pnl_points, 'pnl_rs': pnl_rs
        })

    # --- 5. Analyze and Print Results ---
    if not results_list:
        print("No trades were executed.")
        return

    results_df = pd.DataFrame(results_list)

    total_days = len(data)
    total_trades = len(results_df)

    wins = results_df[results_df['outcome'] == 'TARGET_HIT']
    losses = results_df[results_df['outcome'] == 'SL_HIT']
    eod_open = results_df[results_df['outcome'] == 'EOD_OPEN']

    win_rate = (len(wins) / total_trades) * 100 if total_trades > 0 else 0
    total_pnl_points = float(results_df['pnl_points'].sum())
    total_pnl_rs = float(results_df['pnl_rs'].sum())

    avg_win_rs = float(wins['pnl_rs'].mean()) if len(wins) > 0 else 0.0
    avg_loss_rs = float(losses['pnl_rs'].mean()) if len(losses) > 0 else 0.0

    # Calculate profit factor
    total_profit_rs = float(wins['pnl_rs'].sum())
    total_loss_rs = float(abs(losses['pnl_rs'].sum()))
    profit_factor_rs = total_profit_rs / total_loss_rs if total_loss_rs > 0 else float('inf')

    print("--- Performance Summary (Daily Breakout) ---")
    print(f"Starting Balance: Rs {starting_balance:,.2f}")
    print(f"Final Balance:    Rs {float(current_balance):,.2f}")
    print(f"Total PnL (Rs):   Rs {total_pnl_rs:,.2f}")
    print(f"Total PnL (Points): {total_pnl_points:.2f}")
    print("-" * 27)
    print(f"Total Days Tested: {total_days}")
    print(f"Total Trades Closed: {total_trades}")
    print("-" * 27)
    print(f"Wins (Target Hit): {len(wins)}")
    print(f"Losses (Stop Hit): {len(losses)}")
    print(f"Held to EOD: {len(eod_open)}")
    print(f"Win Rate: {win_rate:.2f}%")
    print("-" * 27)
    print(f"Profit Factor (Rs): {profit_factor_rs:.2f}")
    print(f"Average Win (Rs):   Rs {avg_win_rs:,.2f}")
    print(f"Average Loss (Rs):  Rs {avg_loss_rs:,.2f}")


# --- Main execution ---
if __name__ == "__main__":
    # Get ticker input from user
    ticker_input = input("Enter stock ticker (e.g., RELIANCE, TCS, or ^NSEI for NIFTY 50): ").strip().upper()
    if not ticker_input.startswith('^') and not ticker_input.endswith('.NS'):
        TICKER = ticker_input + '.NS'
        print(f"Assuming Indian stock, using: {TICKER}")
    else:
        TICKER = ticker_input
        print(f"Using ticker: {TICKER}")

    PERIOD_TO_TEST = '2y'  # We can now test for 2 years!
    RR_RATIO = 2.0  # 1:2 Risk/Reward Ratio
    STARTING_BALANCE = 100000.0
    RISK_PER_TRADE = 0.02  # 2% risk per trade

    run_daily_breakout_backtest(TICKER,
                                starting_balance=STARTING_BALANCE,
                                risk_per_trade_percent=RISK_PER_TRADE,
                                period=PERIOD_TO_TEST,
                                risk_reward_ratio=RR_RATIO)

