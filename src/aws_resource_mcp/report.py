"""Read-only AWS utilization analysis and HTML business-impact report."""
from __future__ import annotations

import html
import json
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

HOURS_PER_YEAR = 8760
WINDOWS = (30, 15, 7)
UNDER_PEAK_PCT = 40.0  # peak below this => candidate for downsizing
TARGET_PEAK_PCT = 80.0  # peak allowed on the downsized resource
OVER_AVG_PCT = 70.0
OVER_P95_PCT = 85.0
GP2_TO_GP3_SAVING = 0.20

SIZE_LADDER = [
    "nano", "micro", "small", "medium", "large", "xlarge", "2xlarge", "4xlarge",
    "8xlarge", "12xlarge", "16xlarge", "24xlarge", "32xlarge",
]
# Capacity doubles per step from "large" upwards; smaller sizes are not halved exactly.
EBS_GB_MONTH_USD = {"gp2": 0.10, "gp3": 0.08, "io1": 0.125, "io2": 0.125, "st1": 0.045, "sc1": 0.015, "standard": 0.05}
RDS_ENGINES = {
    "mysql": "MySQL", "postgres": "PostgreSQL", "mariadb": "MariaDB",
    "aurora-mysql": "Aurora MySQL", "aurora-postgresql": "Aurora PostgreSQL",
}

STATUS_ORDER = {"Overutilized": 0, "Idle": 1, "Underutilized": 2, "Insufficient data": 3, "Right-sized": 4}


@dataclass
class Usage:
    avg: float | None = None
    p95: float | None = None
    peak: float | None = None


@dataclass
class Finding:
    service: str
    region: str
    resource_id: str
    name: str
    configured: str  # what limit is configured
    required: str  # what limit is required
    status: str
    usage: dict[int, Usage] = field(default_factory=dict)
    metric: str = "CPUUtilization"
    annual_cost: float | None = None
    annual_cost_after: float | None = None
    recommendation: str = ""
    limitations: str = ""

    @property
    def savings(self) -> float | None:
        if self.annual_cost is None or self.annual_cost_after is None:
            return None
        return max(self.annual_cost - self.annual_cost_after, 0.0)


# ---------------------------------------------------------------- analysis

def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(math.ceil(pct / 100 * len(ordered)) - 1, 0)
    return ordered[index]


def summarize_usage(points: list[dict], now: datetime) -> dict[int, Usage]:
    """Average, p95 (of hourly averages) and peak (of hourly maximums) per window."""
    result: dict[int, Usage] = {}
    for days in WINDOWS:
        cutoff = now - timedelta(days=days)
        window = [p for p in points if p["Timestamp"] >= cutoff]
        averages = [p["Average"] for p in window]
        maxima = [p["Maximum"] for p in window]
        if averages:
            result[days] = Usage(sum(averages) / len(averages), percentile(averages, 95), max(maxima))
        else:
            result[days] = Usage()
    return result


def split_type(type_name: str) -> tuple[str, str] | None:
    """'m5.2xlarge' -> ('m5.', '2xlarge'); 'db.r5.large' -> ('db.r5.', 'large')."""
    match = re.match(r"^(.+\.)([a-z0-9]+)$", type_name)
    if match and match.group(2) in SIZE_LADDER:
        return match.group(1), match.group(2)
    return None


def smaller_type(type_name: str, steps: int) -> str | None:
    parts = split_type(type_name)
    if not parts or steps < 1:
        return None
    prefix, size = parts
    index = SIZE_LADDER.index(size) - steps
    return prefix + SIZE_LADDER[index] if index >= 0 else None


def downsize_steps(peak: float) -> int:
    """Halvings that keep the observed peak under TARGET_PEAK_PCT (capped at 2)."""
    steps = 0
    while steps < 2 and peak * 2 ** (steps + 1) <= TARGET_PEAK_PCT:
        steps += 1
    return steps


def classify(usage: dict[int, Usage]) -> str:
    u30 = usage.get(30) or Usage()
    if u30.avg is None or u30.peak is None:
        return "Insufficient data"
    if (u30.avg >= OVER_AVG_PCT) or (u30.p95 or 0) >= OVER_P95_PCT:
        return "Overutilized"
    if u30.peak < UNDER_PEAK_PCT:
        return "Underutilized"
    return "Right-sized"


def evaluate_compute(service: str, region: str, rid: str, name: str, type_name: str,
                     usage: dict[int, Usage], price_of) -> Finding:
    """Shared EC2/RDS rule. price_of(type_name) -> hourly USD or None."""
    status = classify(usage)
    finding = Finding(service, region, rid, name, configured=type_name, required=type_name,
                      status=status, usage=usage)
    hourly = price_of(type_name)
    finding.annual_cost = hourly * HOURS_PER_YEAR if hourly is not None else None
    finding.annual_cost_after = finding.annual_cost
    peak = (usage.get(30) or Usage()).peak
    if status == "Underutilized" and peak is not None:
        steps = downsize_steps(peak)
        target = smaller_type(type_name, steps)
        if target:
            finding.required = target
            target_hourly = price_of(target)
            if target_hourly is None and hourly is not None:
                target_hourly = hourly / 2 ** steps
            finding.annual_cost_after = target_hourly * HOURS_PER_YEAR if target_hourly is not None else None
            finding.recommendation = (
                f"30-day peak CPU is {peak:.1f}%. Review moving {type_name} to {target}; "
                f"projected peak would be about {min(peak * 2 ** steps, 100):.0f}%."
            )
        else:
            finding.status = "Right-sized"
            finding.recommendation = "Lowest practical size in this family; no downsizing available."
    elif status == "Overutilized":
        finding.recommendation = (
            f"Sustained high CPU. Evaluate a larger size than {type_name} or scaling out to avoid performance risk."
        )
        finding.required = "Larger than " + type_name
    elif status == "Insufficient data":
        finding.recommendation = "Fewer than expected CloudWatch datapoints; enable monitoring or wait for data."
    else:
        finding.recommendation = "Utilization is within a healthy range."
    finding.limitations = "CPU only; memory and disk are not available from default CloudWatch metrics."
    return finding


def evaluate_volume(region: str, vol: dict) -> Finding:
    vtype, size = vol.get("VolumeType", "gp2"), vol.get("Size", 0)
    rate = EBS_GB_MONTH_USD.get(vtype)
    cost = rate * size * 12 if rate is not None else None
    configured = f"{size} GiB {vtype}" + (f", {vol['Iops']} IOPS" if vol.get("Iops") else "")
    name = next((t["Value"] for t in vol.get("Tags", []) if t["Key"] == "Name"), "")
    attached = bool(vol.get("Attachments"))
    finding = Finding("EBS", region, vol["VolumeId"], name, configured, configured, "Right-sized",
                      metric="Attachment", annual_cost=cost, annual_cost_after=cost)
    finding.limitations = "Prices are approximate us-east-1 list rates; IOPS/throughput charges not included."
    if not attached:
        finding.status, finding.required = "Idle", "None (unattached)"
        finding.annual_cost_after = 0.0 if cost is not None else None
        finding.recommendation = "Volume is not attached to any instance. Snapshot if needed, then delete."
    elif vtype == "gp2":
        finding.required = f"{size} GiB gp3"
        finding.status = "Underutilized"
        finding.annual_cost_after = cost * (1 - GP2_TO_GP3_SAVING) if cost is not None else None
        finding.recommendation = "Migrate gp2 to gp3 for about 20% lower storage cost at equal or better baseline performance."
    else:
        finding.recommendation = "Attached and using a current-generation volume type."
    return finding


# ---------------------------------------------------------------- AWS access

class Collector:
    def __init__(self, session, now: datetime | None = None):
        self.session = session
        self.now = now or datetime.now(timezone.utc)
        self._prices: dict[tuple, float | None] = {}
        self.warnings: list[str] = []

    def _pricing(self):
        return self.session.client("pricing", region_name="us-east-1")

    def _price(self, key: tuple, service_code: str, filters: dict) -> float | None:
        if key in self._prices:
            return self._prices[key]
        price = None
        try:
            response = self._pricing().get_products(
                ServiceCode=service_code,
                Filters=[{"Type": "TERM_MATCH", "Field": f, "Value": v} for f, v in filters.items()],
                MaxResults=1,
            )
            if response["PriceList"]:
                terms = json.loads(response["PriceList"][0])["terms"]["OnDemand"]
                dim = next(iter(next(iter(terms.values()))["priceDimensions"].values()))
                price = float(dim["pricePerUnit"]["USD"])
        except Exception as error:  # pricing is best-effort
            note = f"Pricing lookup failed ({type(error).__name__}); costs shown as n/a."
            if note not in self.warnings:
                self.warnings.append(note)
        self._prices[key] = price
        return price

    def ec2_price(self, region: str, instance_type: str, platform: str) -> float | None:
        os_name = "Windows" if platform == "windows" else "Linux"
        return self._price(("ec2", region, instance_type, os_name), "AmazonEC2", {
            "regionCode": region, "instanceType": instance_type, "operatingSystem": os_name,
            "tenancy": "Shared", "preInstalledSw": "NA", "capacitystatus": "Used",
        })

    def rds_price(self, region: str, instance_class: str, engine: str, multi_az: bool) -> float | None:
        db_engine = RDS_ENGINES.get(engine)
        if not db_engine:
            return None
        return self._price(("rds", region, instance_class, db_engine, multi_az), "AmazonRDS", {
            "regionCode": region, "instanceType": instance_class, "databaseEngine": db_engine,
            "deploymentOption": "Multi-AZ" if multi_az else "Single-AZ",
        })

    def cpu_usage(self, region: str, namespace: str, dimension: str, value: str) -> dict[int, Usage]:
        cloudwatch = self.session.client("cloudwatch", region_name=region)
        points = cloudwatch.get_metric_statistics(
            Namespace=namespace, MetricName="CPUUtilization",
            Dimensions=[{"Name": dimension, "Value": value}],
            StartTime=self.now - timedelta(days=max(WINDOWS)), EndTime=self.now,
            Period=3600, Statistics=["Average", "Maximum"],
        )["Datapoints"]
        return summarize_usage(points, self.now)

    def collect(self, regions: list[str]) -> list[Finding]:
        findings: list[Finding] = []
        for region in regions:
            for step in (self._ec2, self._ebs, self._rds):
                try:
                    findings.extend(step(region))
                except Exception as error:
                    self.warnings.append(f"{step.__name__.strip('_').upper()} in {region} skipped: {type(error).__name__}: {error}")
        return findings

    def _ec2(self, region: str) -> list[Finding]:
        ec2 = self.session.client("ec2", region_name=region)
        out = []
        for page in ec2.get_paginator("describe_instances").paginate(
                Filters=[{"Name": "instance-state-name", "Values": ["running", "stopped"]}]):
            for reservation in page["Reservations"]:
                for inst in reservation["Instances"]:
                    rid, itype = inst["InstanceId"], inst["InstanceType"]
                    name = next((t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"), "")
                    platform = inst.get("PlatformDetails", "Linux/UNIX")
                    price_of = lambda t, p=("windows" if "Windows" in platform else "linux"): self.ec2_price(region, t, p)
                    if inst["State"]["Name"] == "stopped":
                        f = Finding("EC2", region, rid, name, itype, "None (stopped)", "Idle",
                                    annual_cost=0.0, annual_cost_after=0.0,
                                    recommendation="Instance is stopped; attached EBS volumes still incur cost. Terminate if no longer needed.")
                        out.append(f)
                        continue
                    usage = self.cpu_usage(region, "AWS/EC2", "InstanceId", rid)
                    out.append(evaluate_compute("EC2", region, rid, name, itype, usage, price_of))
        return out

    def _ebs(self, region: str) -> list[Finding]:
        ec2 = self.session.client("ec2", region_name=region)
        return [evaluate_volume(region, v)
                for page in ec2.get_paginator("describe_volumes").paginate() for v in page["Volumes"]]

    def _rds(self, region: str) -> list[Finding]:
        rds = self.session.client("rds", region_name=region)
        out = []
        for page in rds.get_paginator("describe_db_instances").paginate():
            for db in page["DBInstances"]:
                rid, cls = db["DBInstanceIdentifier"], db["DBInstanceClass"]
                price_of = lambda t, d=db: self.rds_price(region, t, d["Engine"], d.get("MultiAZ", False))
                usage = self.cpu_usage(region, "AWS/RDS", "DBInstanceIdentifier", rid)
                out.append(evaluate_compute("RDS", region, rid, db["Engine"], cls, usage, price_of))
        return out


# ---------------------------------------------------------------- rendering

def _money(value: float | None) -> str:
    return "n/a" if value is None else f"${value:,.0f}"


def _pct(value: float | None) -> str:
    return "–" if value is None else f"{value:.1f}%"


def _usage_cell(usage: dict[int, Usage], days: int, metric: str) -> str:
    if metric == "Attachment":
        return "–"
    u = usage.get(days) or Usage()
    if u.avg is None:
        return '<span class="muted">no data</span>'
    return f'<span title="avg / p95 / peak">{_pct(u.avg)} <small>/ {_pct(u.p95)} / {_pct(u.peak)}</small></span>'


def render_html(findings: list[Finding], account: str, regions: list[str], generated: datetime,
                warnings: list[str]) -> str:
    esc = html.escape
    findings = sorted(findings, key=lambda f: (STATUS_ORDER.get(f.status, 9), -(f.savings or 0)))
    total_cost = sum(f.annual_cost or 0 for f in findings)
    total_savings = sum(f.savings or 0 for f in findings)
    impacted_cost = sum(f.annual_cost or 0 for f in findings if (f.savings or 0) > 0)
    counts = {s: sum(1 for f in findings if f.status == s) for s in STATUS_ORDER}

    by_service: dict[str, list[float]] = {}
    for f in findings:
        row = by_service.setdefault(f.service, [0, 0.0, 0.0])
        row[0] += 1
        row[1] += f.annual_cost or 0
        row[2] += f.savings or 0
    service_rows = "".join(
        f"<tr><td>{esc(s)}</td><td>{n}</td><td>{_money(c)}</td><td class='save'>{_money(v)}</td></tr>"
        for s, (n, c, v) in sorted(by_service.items()))

    kpis = [
        ("Resources analyzed", str(len(findings)), ""),
        ("Annual spend analyzed", _money(total_cost), ""),
        ("Impacted annual cost", _money(impacted_cost), "warn"),
        ("Savings if fixed (per year)", _money(total_savings), "good"),
        ("Overutilized (risk)", str(counts["Overutilized"]), "bad"),
        ("Underutilized / idle", str(counts["Underutilized"] + counts["Idle"]), "warn"),
    ]
    kpi_html = "".join(f'<div class="kpi {c}"><div class="v">{v}</div><div class="l">{esc(l)}</div></div>' for l, v, c in kpis)

    rows = []
    for f in findings:
        cls = f.status.lower().replace(" ", "-")
        label = f"{esc(f.resource_id)}" + (f"<br><small>{esc(f.name)}</small>" if f.name else "")
        rows.append(
            f"<tr data-status='{esc(f.status)}' data-service='{esc(f.service)}'>"
            f"<td>{esc(f.service)}<br><small>{esc(f.region)}</small></td><td>{label}</td>"
            f"<td>{_usage_cell(f.usage, 30, f.metric)}</td><td>{_usage_cell(f.usage, 15, f.metric)}</td>"
            f"<td>{_usage_cell(f.usage, 7, f.metric)}</td>"
            f"<td>{esc(f.required)}</td><td>{esc(f.configured)}</td>"
            f"<td><span class='pill {cls}'>{esc(f.status)}</span></td>"
            f"<td class='num'>{_money(f.annual_cost)}</td>"
            f"<td class='num save'>{_money(f.savings)}</td>"
            f"<td class='rec'>{esc(f.recommendation)}</td></tr>")

    warn_html = "".join(f"<li>{esc(w)}</li>" for w in warnings)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AWS Resource Optimization Report</title>
<style>
body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f4f6f9;color:#1f2933}}
header{{background:#232f3e;color:#fff;padding:28px 40px}} header h1{{margin:0 0 6px;font-size:26px}}
header p{{margin:0;color:#ff9900}} main{{padding:24px 40px;max-width:1600px;margin:auto}}
h2{{margin:32px 0 12px;font-size:19px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px}}
.kpi{{background:#fff;border-radius:8px;padding:16px;border-left:5px solid #94a3b8;box-shadow:0 1px 3px #0001}}
.kpi .v{{font-size:26px;font-weight:700}} .kpi .l{{color:#52606d;font-size:13px;margin-top:4px}}
.kpi.good{{border-color:#16a34a}} .kpi.warn{{border-color:#f59e0b}} .kpi.bad{{border-color:#dc2626}}
table{{border-collapse:collapse;width:100%;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px #0001;font-size:13px}}
th{{background:#e4e9f0;text-align:left;padding:10px;position:sticky;top:0}} td{{padding:9px 10px;border-top:1px solid #e4e9f0;vertical-align:top}}
.num{{text-align:right;white-space:nowrap}} .save{{color:#15803d;font-weight:600}} small,.muted{{color:#7b8794}}
.pill{{padding:3px 9px;border-radius:12px;font-size:12px;font-weight:600;white-space:nowrap}}
.pill.overutilized{{background:#fee2e2;color:#b91c1c}} .pill.underutilized{{background:#fef3c7;color:#b45309}}
.pill.idle{{background:#ede9fe;color:#6d28d9}} .pill.right-sized{{background:#dcfce7;color:#15803d}}
.pill.insufficient-data{{background:#e5e7eb;color:#4b5563}} .rec{{max-width:340px}}
.filters{{margin-bottom:10px}} .filters select{{padding:6px;margin-right:8px}}
.group{{background:#d9e2ec;text-align:center;font-weight:600}}
.note{{background:#fff8e1;border-left:5px solid #f59e0b;padding:10px 16px;border-radius:6px}}
.wrap{{overflow-x:auto}} footer{{color:#7b8794;font-size:12px;padding:20px 40px}}
</style></head><body>
<header><h1>AWS Resource Optimization Report</h1>
<p>Account {esc(account)} · Regions: {esc(', '.join(regions))} · Generated {generated:%Y-%m-%d %H:%M UTC} · Read-only analysis</p></header>
<main>
<h2>Business impact</h2><div class="kpis">{kpi_html}</div>
<h2>Impact by service</h2>
<table style="max-width:700px"><tr><th>Service</th><th>Resources</th><th>Annual cost</th><th>Savings if fixed</th></tr>{service_rows}</table>
<h2>Resource details</h2>
<div class="filters">Status <select id="fs"><option value="">All</option>{''.join(f'<option>{esc(s)}</option>' for s in STATUS_ORDER)}</select>
Service <select id="fv"><option value="">All</option>{''.join(f'<option>{esc(s)}</option>' for s in sorted(by_service))}</select></div>
<div class="wrap"><table id="t"><thead>
<tr><th rowspan="2">Service</th><th rowspan="2">Resource</th><th class="group" colspan="3">Usage: avg / p95 / peak</th>
<th rowspan="2">Required limit</th><th rowspan="2">Configured limit</th><th rowspan="2">Status</th>
<th rowspan="2">Annual cost (current)</th><th rowspan="2">Saved per year if fixed</th><th rowspan="2">Recommendation</th></tr>
<tr><th>Last 30 days</th><th>Last 15 days</th><th>Last 7 days</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<h2>Method &amp; limitations</h2>
<div class="note"><ul>
<li>Usage is CloudWatch CPUUtilization (hourly): average, p95 of hourly averages, and peak of hourly maximums. Memory and disk are not included.</li>
<li>Underutilized: 30-day peak below {UNDER_PEAK_PCT:.0f}%. Required limit is the smallest size (up to two steps) keeping that peak under {TARGET_PEAK_PCT:.0f}%. Overutilized: 30-day average ≥ {OVER_AVG_PCT:.0f}% or p95 ≥ {OVER_P95_PCT:.0f}%.</li>
<li>Costs are on-demand list prices from the AWS Pricing API (EBS uses approximate us-east-1 rates), annualized over {HOURS_PER_YEAR} hours. Savings plans, reservations and discounts are not reflected. Figures are estimates for review, not guarantees.</li>
<li>No AWS resources were changed.</li>{warn_html}</ul></div>
</main><footer>Generated by aws-resource-optimization-mcp</footer>
<script>
const fs=document.getElementById('fs'),fv=document.getElementById('fv');
function f(){{document.querySelectorAll('#t tbody tr').forEach(r=>{{
r.style.display=(!fs.value||r.dataset.status===fs.value)&&(!fv.value||r.dataset.service===fv.value)?'':'none'}})}}
fs.onchange=fv.onchange=f;
</script></body></html>"""


def default_regions(session) -> list[str]:
    region = session.region_name
    return [region] if region else ["us-east-1"]
