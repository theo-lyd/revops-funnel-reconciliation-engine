# Batch 9.2: Operational Dashboards and SLO/SLI Tracking

## Objective
Implement operational dashboards with SLO/SLI metrics, cost-performance trend analysis, and automated scaling recommendations to provide production observability and inform infrastructure tuning decisions.

## Deliverables
- `src/revops_funnel/operational_dashboards.py`
- `scripts/ops/generate_operational_dashboards.py`
- `tests/test_operational_dashboards.py`
- `tests/test_generate_operational_dashboards_cli.py`
- `Makefile` (updated with dashboard variables and targets)
- `.env.example` (updated with dashboard configuration)
- `.github/workflows/ci.yml` (updated with dashboard generation step)
- `.github/workflows/release.yml` (updated with dashboard generation step and env variable)
- `docs/project-governance/commands/make-commands.md` (added MK-071, MK-072)
- `docs/project-governance/commands/python-dbt-duckdb-commands.md` (added PDD-053, PDD-054)
- `docs/project-governance/issues-log.md` (added ISS-040)

## What Changed

### 1. Operational Dashboard Module
Created `src/revops_funnel/operational_dashboards.py` with:
- **Enums**: `MetricTrend` (improving/stable/degrading/insufficient_data), `ScalingRecommendation` (scale_up/scale_down/monitor/no_action)
- **Dataclasses**:
  - `PerformanceMetric`: timestamp, value, unit, metric_type
  - `TrendAnalysis`: metric statistics with trend direction and percent change
  - `SLIMetric`: service-level indicator measurement (name, current, SLO threshold, unit, status, trend)
  - `OperationalDashboard`: complete dashboard with SLI metrics, trends, correlations, and recommendations
- **Core Functions**:
  - `calculate_trend()`: determines trend direction and percent change given recent/historical values
  - `analyze_metric_trend()`: comprehensive trend analysis over 1-week lookback window
  - `evaluate_sli_status()`: maps metric value to health status (healthy/degraded/unhealthy)
  - `calculate_cost_performance_correlation()`: Pearson correlation between cost and performance metrics
  - `generate_scaling_recommendations()`: derives scaling recommendations from latency/throughput trends
  - `determine_dashboard_status()`: aggregates SLI statuses into overall dashboard status
  - `generate_operational_dashboard()`: orchestrates dashboard creation with all metrics and recommendations

### 2. Dashboard Generation CLI
Created `scripts/ops/generate_operational_dashboards.py` with:
- **Arguments**:
  - `--health-report`: path to health report artifact (optional)
  - `--cost-report`: path to cost attribution artifact (optional)
  - `--performance-report`: path to performance metrics artifact (optional)
  - `--output`: dashboard output path (default: `artifacts/monitoring/operational_dashboard.json`)
  - `--deployment-version`: current deployment version for tracking
  - `--strict-metrics`: enforce telemetry availability (fails if missing)
- **Local-Safe Architecture**:
  - Non-strict mode: returns `skipped` status if telemetry unavailable
  - Strict mode: non-zero exit if telemetry unavailable
- **Telemetry Ingestion**:
  - `fetch_health_status()`: extracts freshness data from health report
  - `fetch_cost_metrics()`: extracts cost-per-record from cost attribution
  - `fetch_performance_metrics()`: extracts latency from performance report
- **Metric Extraction**:
  - `extract_latency_metrics()`: converts performance execution time to latency metric
  - `extract_cost_metrics()`: extracts cost-per-record metrics with timestamps
- **SLI Generation**:
  - Data freshness SLI (SLO: 24 hours)
  - Transformation latency SLI (SLO: 120 minutes)
  - Cost-per-record SLI (SLO: $0.001/record)

### 3. Comprehensive Test Suite
Created 26 tests across two files:

**`tests/test_operational_dashboards.py` (22 tests)**:
- **TrendCalculation** (5 tests): improving/degrading/stable trends, edge cases (insufficient data, zero historical)
- **TrendAnalysis** (2 tests): with data, without data
- **SLIEvaluation** (3 tests): healthy/degraded/unhealthy status mapping
- **CostPerformanceCorrelation** (4 tests): positive correlation, no correlation (insufficient data, mismatched lengths)
- **ScalingRecommendations** (2 tests): scale-up when latency degrading, monitor when stable
- **DashboardStatus** (3 tests): all healthy, with degraded (30% threshold), with unhealthy (critical)
- **DashboardGeneration** (2 tests): end-to-end generation, serialization to dict with enum handling

**`tests/test_generate_operational_dashboards_cli.py` (4 tests)**:
- `test_cli_skipped_no_telemetry`: returns success (status=skipped) when no telemetry available
- `test_cli_strict_fails_no_telemetry`: returns error when --strict-metrics and no telemetry
- `test_cli_custom_output_path`: respects custom output path argument
- `test_cli_with_deployment_version`: preserves deployment version in output

### 4. Makefile Integration
Added to `Makefile`:
- **Variables** (4 new):
  - `DASHBOARD_OUTPUT_PATH` (default: `artifacts/monitoring/operational_dashboard.json`)
  - `DASHBOARD_HEALTH_REPORT` (default: `artifacts/monitoring/health_report.json`)
  - `DASHBOARD_COST_REPORT` (default: `artifacts/monitoring/query_cost_attribution.json`)
  - `DASHBOARD_PERFORMANCE_REPORT` (default: `artifacts/performance/dbt_build_prod_report.json`)
- **Targets** (2 new):
  - `make dashboards`: safe-skip mode dashboard generation
  - `make dashboards-strict`: strict telemetry enforcement mode
- **PHONY targets**: added `dashboards` and `dashboards-strict` to .PHONY declaration

### 5. Environment Configuration
Updated `.env.example` with:
- Section: "Phase 9: Operational Dashboards and SLO/SLI Tracking"
- All four dashboard variables with production defaults

### 6. Workflow Integration

**CI Workflow (`.github/workflows/ci.yml`)**:
- Added step "Generate operational dashboards (safe skip mode)" after health checks
- Configured to use default paths for all telemetry inputs
- Added `artifacts/monitoring/operational_dashboard.json` to deployment integration artifact upload

**Release Workflow (`.github/workflows/release.yml`)**:
- Added `DASHBOARD_OUTPUT_PATH` environment variable
- Added step "Generate operational dashboards" after health checks
- Uses cost attribution report path from release workflow
- Configured to use health, cost, and performance report paths
- Added `artifacts/monitoring/operational_dashboard.json` to release gate artifact upload

### 7. Governance Documentation
Updated three governance files:
- **`docs/project-governance/commands/make-commands.md`**: Added MK-071 (dashboards) and MK-072 (dashboards-strict)
- **`docs/project-governance/commands/python-dbt-duckdb-commands.md`**: Added PDD-053 (dashboard generation) and PDD-054 (strict dashboard generation)
- **`docs/project-governance/issues-log.md`**: Added ISS-040 (no blocking defects for Batch 9.2)

## Design Rationale

### SLO/SLI Framework
- **Service-Level Objectives (SLOs)**: quantified performance targets
  - Data freshness: 24 hours (healthy when < 24h, degraded 24-36h, unhealthy > 36h)
  - Transformation latency: 120 minutes (healthy < 120m, degraded < 180m, unhealthy > 180m)
  - Cost per record: $0.001 (healthy when < 0.001, degraded < 0.0015, unhealthy > 0.0015)
- **Service-Level Indicators (SLIs)**: measurable metrics tracking SLO compliance
  - Each SLI includes: current value, SLO threshold, unit, status (healthy/degraded/unhealthy), trend

### Trend Analysis
- **Lookback window**: 1 week (168 hours) by default
- **Trend detection**: percentage change between recent (last 7 days) and historical average
  - Stable: <2% change
  - Degrading: >2% increase in latency/cost
  - Improving: >2% decrease in latency/cost
- **Edge case handling**: returns INSUFFICIENT_DATA when <2 data points or zero stdev

### Cost-Performance Correlation
- **Pearson correlation coefficient**: -1.0 (perfect negative) to +1.0 (perfect positive)
- **Interpretation**:
  - Positive correlation: cost and latency moving together (both increasing or both decreasing)
  - Negative correlation: cost and latency moving opposite (cost down, latency up = efficiency loss)
  - Ideal: positive correlation with improving trend (both cost and latency decreasing)
- **Edge case handling**: returns None when <2 data points, missing data, or zero stdev

### Scaling Recommendations
- **Scale Up**: recommended when latency degrading >5% over past week
  - Confidence: 0.8
  - Estimated impact: 30-40% latency reduction
  - Priority: high
- **Monitor**: recommended when performance stable (latency not degrading)
  - Confidence: 0.7
  - Estimated impact: baseline for future decisions
  - Priority: medium
- **No Action**: default when all metrics within SLO
  - Confidence: 0.9
  - Priority: low

### Local-Safe vs Strict Modes
- **Local-safe mode** (default):
  - Telemetry absence doesn't block dashboard generation
  - Emits `skipped` status for missing telemetry
  - Enable in CI/local for non-blocking observability
  - Allows development workflow without production metrics
- **Strict mode** (--strict-metrics):
  - Telemetry must be available or exit non-zero
  - Used in production release workflows
  - Fails fast if observability data missing
  - Ensures complete visibility at release boundary

## Validation

### Code Quality
- ✅ Lint: All Ruff checks passed (import sorting, type hints, line length)
- ✅ Type checking: mypy passed all checks (explicit type annotations for dict/list returns)
- ✅ Imports: No unused imports, all dependencies properly declared

### Test Coverage
- ✅ 22 unit tests: trend calculation, SLI evaluation, correlation math, dashboard generation
- ✅ 4 CLI integration tests: safe-skip behavior, strict failure, custom paths, deployment versioning
- ✅ Total: 26 tests passing, 0 failures
- ✅ Edge cases covered: zero historical values, insufficient data, mismatched data lengths, correlation edge conditions

### Integration
- ✅ Makefile targets: dashboards and dashboards-strict callable and configured
- ✅ CI workflow: dashboard generation integrated after health checks with safe-skip mode
- ✅ Release workflow: dashboard generation with configurable telemetry paths in strict context
- ✅ Artifact uploads: operational_dashboard.json included in both CI and release workflows

## Operational Impact

### New Capabilities
1. **SLO/SLI Tracking**: quantified performance visibility with health status aggregation
2. **Trend Analysis**: 7-day trend detection to identify improvement/degradation patterns
3. **Cost-Performance Correlation**: identifies efficiency tradeoffs and scaling opportunities
4. **Scaling Recommendations**: automated scaling suggestions based on latency trends
5. **Machine-Readable Dashboards**: JSON artifacts for integration with external monitoring systems

### Observability Improvements
- Track transformation latency trends over time
- Correlate cost metrics against performance changes
- Identify when scaling recommendations emerge (latency degrading >5%)
- Historical baseline for cost optimization decisions

### Operational Workflows
- CI validates dashboard generation with safe-skip mode (non-blocking)
- Release workflow generates dashboards with full telemetry enforcement
- Dashboards published as release artifacts for post-deployment analysis
- Enable cost vs performance tradeoff analysis for infrastructure tuning

## Notes
- Dashboard accuracy depends on availability of health, cost, and performance artifacts
- Local development without production telemetry can still generate dashboards in safe-skip mode
- Correlation calculations handle edge cases (insufficient data, zero variance) gracefully
- SLO thresholds (24h freshness, 120m latency, $0.001 cost) are configurable via command-line arguments
- Batch 9.2 provides the foundation for Batch 9.3 (on-call runbooks) and future alerting systems
