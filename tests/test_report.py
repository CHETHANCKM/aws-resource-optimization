from datetime import datetime, timedelta, timezone

from aws_resource_mcp import report

NOW = datetime(2026, 1, 31, tzinfo=timezone.utc)


def points(avg, peak, days=30):
    return [{"Timestamp": NOW - timedelta(hours=h), "Average": avg, "Maximum": peak} for h in range(days * 24)]


def test_smaller_type_and_steps():
    assert report.smaller_type("m5.2xlarge", 1) == "m5.xlarge"
    assert report.smaller_type("db.r5.large", 2) == "db.r5.small" or report.smaller_type("db.r5.large", 2) == "db.r5.medium"
    assert report.smaller_type("t3.nano", 1) is None
    assert report.downsize_steps(10) == 2
    assert report.downsize_steps(35) == 1
    assert report.downsize_steps(39) == 1


def test_underutilized_compute_reports_savings():
    usage = report.summarize_usage(points(8, 20), NOW)
    f = report.evaluate_compute("EC2", "us-east-1", "i-1", "", "m5.2xlarge", usage, lambda t: {"m5.2xlarge": 0.4, "m5.large": 0.1}.get(t))
    assert f.status == "Underutilized"
    assert f.required == "m5.xlarge" or f.required == "m5.large"
    assert f.savings and f.savings > 0


def test_overutilized_and_insufficient():
    usage = report.summarize_usage(points(80, 99), NOW)
    assert report.evaluate_compute("EC2", "r", "i", "", "m5.large", usage, lambda t: 0.1).status == "Overutilized"
    empty = report.summarize_usage([], NOW)
    assert report.evaluate_compute("EC2", "r", "i", "", "m5.large", empty, lambda t: 0.1).status == "Insufficient data"


def test_volume_rules():
    idle = report.evaluate_volume("r", {"VolumeId": "v-1", "Size": 100, "VolumeType": "gp3", "Attachments": []})
    assert idle.status == "Idle" and idle.savings == 96
    gp2 = report.evaluate_volume("r", {"VolumeId": "v-2", "Size": 100, "VolumeType": "gp2", "Attachments": [{}]})
    assert round(gp2.savings, 2) == 24.0


def test_html_contains_required_columns_and_escapes():
    usage = report.summarize_usage(points(8, 20), NOW)
    f = report.evaluate_compute("EC2", "r", "i-<b>", "", "m5.2xlarge", usage, lambda t: 0.4)
    doc = report.render_html([f], "123", ["r"], NOW, [])
    for text in ("Last 30 days", "Last 15 days", "Last 7 days", "Required limit", "Configured limit", "Saved per year if fixed"):
        assert text in doc
    assert "i-<b>" not in doc
