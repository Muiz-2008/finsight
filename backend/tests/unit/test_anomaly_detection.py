from app.analytics.anomaly import iqr_anomalies, zscore_anomalies

# A realistic-size baseline (20 routine transactions) plus one outlier.
# With only a handful of baseline points, a single huge value drags the
# mean/std toward itself enough to mask its own z-score — the known
# Z-score weakness IQR is meant to address (see test_iqr_flags_a_clear_
# outlier below, which demonstrates IQR catching the same case with a
# much smaller sample).
_BASELINE_SPENDING = [
    28, 29, 30, 31, 32, 29, 30, 31, 28, 32, 30, 29, 31, 30, 28, 32, 29, 31, 30, 29,
]


def test_zscore_flags_a_clear_outlier():
    values = [*_BASELINE_SPENDING, 500]

    flags = zscore_anomalies(values, threshold=2.5)

    assert len(flags) == 1
    assert flags[0].index == len(values) - 1
    assert flags[0].value == 500


def test_zscore_does_not_flag_the_outlier_with_too_small_a_baseline():
    # Documents the known weakness itself: with only 5 baseline points,
    # the outlier inflates the mean/std enough that its own z-score drops
    # below the threshold.
    values = [30, 32, 28, 31, 29, 500]

    assert zscore_anomalies(values, threshold=2.5) == []


def test_zscore_flags_nothing_for_uniform_spending():
    values = [30, 31, 29, 30, 32, 28]

    assert zscore_anomalies(values) == []


def test_zscore_handles_identical_values_without_dividing_by_zero():
    assert zscore_anomalies([50, 50, 50, 50]) == []


def test_zscore_needs_at_least_two_values():
    assert zscore_anomalies([50]) == []


def test_iqr_flags_a_clear_outlier():
    values = [30, 32, 28, 31, 29, 33, 27, 500]

    flags = iqr_anomalies(values)

    assert len(flags) == 1
    assert flags[0].value == 500


def test_iqr_flags_nothing_for_uniform_spending():
    values = [30, 31, 29, 30, 32, 28, 31, 29]

    assert iqr_anomalies(values) == []


def test_iqr_needs_at_least_four_values():
    assert iqr_anomalies([10, 20, 30]) == []


def test_reason_string_names_a_concrete_number_not_just_a_verdict():
    flags = zscore_anomalies([*_BASELINE_SPENDING, 500], threshold=2.5)

    assert "standard deviations" in flags[0].reason
    assert "500.00" in flags[0].reason
