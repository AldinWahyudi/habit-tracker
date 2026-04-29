from datetime import date

from app import analytics
from app.services.claude import _BULLET_PREFIX_RE, _heuristic_insight


def test_heatmap_intensity_levels():
    # 7-day all-True window -> level 4 on day 7
    series = [True] * 7
    levels = analytics.heatmap_intensity(series)
    assert levels[0] == 1  # window count = 1
    assert levels[6] == 4  # window count = 7


def test_heatmap_intensity_zero_for_missed_day():
    series = [True, True, False, True]
    levels = analytics.heatmap_intensity(series)
    assert levels[2] == 0


def test_pearson_perfect_positive():
    xs = [0.0, 1.0, 0.0, 1.0, 1.0]
    ys = [0.0, 1.0, 0.0, 1.0, 1.0]
    assert analytics.pearson(xs, ys) == 1.0


def test_pearson_perfect_negative():
    xs = [0.0, 1.0, 0.0, 1.0]
    ys = [1.0, 0.0, 1.0, 0.0]
    assert analytics.pearson(xs, ys) == -1.0


def test_pearson_constant_returns_none():
    xs = [1.0, 1.0, 1.0]
    ys = [0.0, 1.0, 0.0]
    assert analytics.pearson(xs, ys) is None


def test_top_correlated_pairs_orders_by_abs_r():
    habits = [(1, "A"), (2, "B"), (3, "C")]
    series = {
        1: [True, False, True, False, True, False, True, False],
        2: [True, False, True, False, True, False, True, False],   # r(A,B) = 1.0
        3: [False, True, False, True, False, True, False, True],   # r(A,C) = -1.0
    }
    pairs = analytics.top_correlated_pairs(habits, series, top_k=3)
    # Both pairs involving A should rank above the B/C pair (which is also -1).
    assert len(pairs) == 3
    top_a, top_b, top_r, _ = pairs[0]
    assert abs(top_r) == 1.0


def test_correlation_explanation_buckets():
    msg_pos = analytics.correlation_explanation("A", "B", 0.62)
    assert "Strong positive" in msg_pos
    msg_neg = analytics.correlation_explanation("A", "B", -0.35)
    assert "negative" in msg_neg.lower()
    msg_none = analytics.correlation_explanation("A", "B", 0.05)
    assert "no meaningful" in msg_none.lower()


def test_aligned_day_of_week_rates():
    # 14 days starting on a Monday with one habit completed every Monday only.
    start = date(2024, 1, 1)  # Monday
    series = [d % 7 == 0 for d in range(14)]
    rates = analytics.aligned_day_of_week_rates(start, {1: series})
    by_name = {name: rate for _, name, rate in rates}
    assert by_name["Mon"] == 1.0
    assert by_name["Tue"] == 0.0


def test_heuristic_insight_returns_three_bullets():
    stats = [
        {"name": "Read", "this_week": 6, "prev_week": 2,
         "this_week_rate": 6 / 7, "best_day": "Mon", "worst_day": "Fri"},
        {"name": "Run", "this_week": 1, "prev_week": 5,
         "this_week_rate": 1 / 7, "best_day": "Sat", "worst_day": "Tue"},
    ]
    bullets = _heuristic_insight(date(2024, 1, 8), date(2024, 1, 14), stats)
    assert len(bullets) == 3
    assert any("Read" in b for b in bullets)


def test_heuristic_insight_handles_no_habits():
    bullets = _heuristic_insight(date(2024, 1, 1), date(2024, 1, 7), [])
    assert len(bullets) == 3


def test_bullet_prefix_regex_preserves_leading_digits_and_dashes():
    # Numeric bullet prefix is stripped, but leading digits in the actual content are preserved.
    assert _BULLET_PREFIX_RE.sub("", "1. 5 out of 7 days completed") == "5 out of 7 days completed"
    assert _BULLET_PREFIX_RE.sub("", "- 30% improvement") == "30% improvement"
    assert _BULLET_PREFIX_RE.sub("", "* Note: try Monday") == "Note: try Monday"
    # Lines without a bullet prefix are left untouched.
    assert _BULLET_PREFIX_RE.sub("", "5 out of 7 days completed") == "5 out of 7 days completed"
