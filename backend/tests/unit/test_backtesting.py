import pytest

from app.analytics.backtesting import moving_average_crossover_signals, run_backtest


def test_signal_requires_full_long_window_of_history():
    prices = [100.0] * 10
    signals = moving_average_crossover_signals(prices, short_window=3, long_window=5)

    assert signals[:4] == [0, 0, 0, 0]  # not enough history yet


def test_signal_rejects_short_window_not_shorter_than_long():
    with pytest.raises(ValueError):
        moving_average_crossover_signals([1.0] * 10, short_window=5, long_window=5)


def test_signal_goes_long_when_short_ma_crosses_above_long_ma():
    # Rising prices: the short MA will pull above the long MA once enough
    # history accumulates.
    prices = [100.0 + i for i in range(20)]
    signals = moving_average_crossover_signals(prices, short_window=3, long_window=10)

    assert signals[-1] == 1


def test_backtest_requires_matching_lengths():
    with pytest.raises(ValueError):
        run_backtest([100.0, 101.0], [1, 1, 1])


def test_backtest_with_no_trades_stays_flat_at_zero_signal():
    prices = [100.0, 105.0, 95.0, 110.0]
    signals = [0, 0, 0, 0]

    result = run_backtest(prices, signals, initial_capital=10_000.0)

    assert result.final_value == pytest.approx(10_000.0)
    assert result.num_trades == 0


def test_backtest_fully_invested_the_whole_time_tracks_the_asset():
    prices = [100.0, 110.0, 121.0]
    signals = [1, 1, 1]

    result = run_backtest(prices, signals, initial_capital=10_000.0, transaction_cost_bps=0.0)

    # +10% then +10% compounds to +21% on the asset; being long the whole
    # time (minus the entry trade, cost=0 here) should track it exactly.
    assert result.total_return == pytest.approx(0.21, abs=1e-9)


def test_transaction_cost_is_charged_only_when_position_changes():
    prices = [100.0, 100.0, 100.0]
    flat = run_backtest(prices, [0, 0, 0], transaction_cost_bps=50.0)
    # Enters at t=0 (0 -> 1) then exits at t=1 (1 -> 0): two trades, two
    # costs charged, even though the underlying price never moves.
    enter_then_exit = run_backtest(prices, [1, 0, 0], transaction_cost_bps=50.0)

    assert flat.num_trades == 0
    assert enter_then_exit.num_trades == 2
    assert enter_then_exit.final_value < flat.final_value


# --- The core correctness property: no look-ahead bias ---


def test_signal_decided_before_a_price_jump_captures_the_jump():
    # Position goes long at index 2, decided using data through index 2
    # (prices[2] = 100, no knowledge of the jump to 200 yet). Per the
    # engine's one-period lag, signals[2] governs the return realized
    # from index 2 -> index 3 (100 -> 200) — so it SHOULD capture this,
    # because the decision was made before the jump occurred, using only
    # information available at that time.
    prices = [100.0, 100.0, 100.0, 200.0]
    signals = [0, 0, 1, 1]

    result = run_backtest(prices, signals, initial_capital=10_000.0, transaction_cost_bps=0.0)

    assert result.final_value == pytest.approx(20_000.0)


def test_signal_decided_after_a_price_jump_cannot_retroactively_capture_it():
    # Position only goes long at index 3 — the LAST index, decided using
    # data through index 3, i.e. *after* the jump to 200 has already
    # happened. There is no future return left in the series for
    # signals[3] to govern. A buggy look-ahead implementation might let
    # this position "capture" the jump that already happened; a correct
    # implementation captures nothing, because you can't trade on
    # information from the past to change a return that already occurred.
    prices = [100.0, 100.0, 100.0, 200.0]
    signals = [0, 0, 0, 1]

    result = run_backtest(prices, signals, initial_capital=10_000.0, transaction_cost_bps=0.0)

    assert result.final_value == pytest.approx(10_000.0)
