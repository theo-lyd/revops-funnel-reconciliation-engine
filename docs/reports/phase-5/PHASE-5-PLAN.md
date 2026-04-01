# Phase 5 Plan: AI-Driven Analytics and Visualization

**Status**: Planning (awaiting approval to proceed)

---

## Phase Objective

Deliver AI-powered analytical interfaces and interactive visualizations that enable self-service revenue insights for RevOps stakeholders, bridging the semantic Gold layer with LLM-orchestrated query generation and BI dashboarding.

---

## Scope and Batches

This phase is proposed as a **4-batch sequence** with incremental deliverables and validation:

### Batch 5.1: Dashboard Foundation and BI Layer Integration
**Focus**: Metabase dashboard setup and semantic layer connection
- Set up Metabase configuration and DuckDB/Snowflake data source connections
- Build foundational dashboards from `bi_executive_funnel_overview` and `fct_revenue_funnel`
- Create reusable dashboard templates (funnel, cohort, cohort-based analysis)
- Document BI consumption patterns and dashboard access control
- **Deliverables**: Metabase template dashboards, connection guides, access runbook
- **Validation**: Dashboard queries execute correctly, parity with Gold layer metrics confirmed

### Batch 5.2: Streamlit Application and Query Templates
**Focus**: Interactive self-service analytics interface
- Build Streamlit application with session state and data caching
- Implement query templates for approved metric calculations (CAC, LTV, velocity, conversion rates)
- Add query library interface for stakeholders to explore metrics
- Integrate Streamlit with DuckDB and Snowflake connection pooling
- **Deliverables**: Streamlit application code, query template library, deployment guide
- **Validation**: App runs locally and connects to warehouse; query templates execute without exceptions

### Batch 5.3: LLM Integration and AI-Driven Query Generation
**Focus**: Semantic understanding and natural language query translation
- Integrate LLM (e.g., OpenAI API) with Streamlit for natural language interpretation
- Implement semantic schema mapper translating user intent to approved queries
- Add safety and audit controls (query logging, rate limiting, approved metric guard rails)
- Build query validation and cost estimation layer
- **Deliverables**: LLM integration code, query validation framework, audit logging
- **Validation**: Natural language inputs translate correctly to approved queries; safety rails prevent invalid metric transformations

### Batch 5.4: Analytics Insights and Anomaly Detection
**Focus**: Automated insights and monitoring dashboard
- Implement anomaly detection on key metrics (funnel conversion rate, CAC, velocity)
- Build insight generation (period-over-period deltas, cohort trends)
- Create monitoring dashboard for stakeholder alerts and exceptions
- Integrate monitoring into Streamlit and email notification workflow
- **Deliverables**: Anomaly detection module, monitoring dashboard, alert templates
- **Validation**: Anomaly detection identifies known test cases; alerts fire correctly; monitoring dashboard reflects real-time metric state

---

## Key Constraints and Dependencies

1. **Gold Layer Dependency**: Phase 5 depends on Phase 4 Gold layer completion including `fct_revenue_funnel`, `dim_sales_teams`, `bi_executive_funnel_overview`.
2. **Snowflake Alignment**: BI tools must connect to both DuckDB (dev) and Snowflake (prod) for parity verification.
3. **LLM Costs**: OpenAI API usage will incur costs; recommend environment-based rate limiting.
4. **Semantic Drift Prevention**: All LLM-generated queries must be validated against approved metric contract from Phase 4.
5. **Security**: Access controls must integrate with existing RBAC framework from Phase 4 hardening Block 1.

---

## Technical Dependencies and Setup

### New Dependencies to Add
- `streamlit` (interactive Python app framework)
- `streamlit-caching` (performance optimization)
- `openai` (LLM API integration)
- `sqlalchemy` (query abstraction layer)
- `plotly` (charting and visualization)
- Metabase (separate deployment, Docker or cloud)

### Environment Variables
```bash
# Streamlit configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_LOGGER_LEVEL=info

# LLM configuration
OPENAI_API_KEY=<your-key>
OPENAI_MODEL=gpt-4
LLM_MAX_TOKENS=1000
LLM_RATE_LIMIT_PER_MINUTE=10

# Analytics configuration
ANOMALY_DETECTION_SENSITIVITY=2.0  # Standard deviations
ANOMALY_CHECK_CADENCE_HOURS=24

# Monitoring
ALERT_EMAIL_RECIPIENTS=stakeholder@example.com
MONITORING_DASHBOARD_REFRESH_INTERVAL=300  # seconds
```

### Updated Makefile Targets
- `streamlit-dev`: Run Streamlit app locally
- `metabase-init`: Initialize Metabase with DuckDB/Snowflake datasources
- `anomaly-check`: Run anomaly detection runner
- `insights-generate`: Generate and publish insights

---

## Validation Strategy

### Batch 5.1 Stop-Gate Validation
- ✅ Metabase dashboards load without errors
- ✅ Dashboard queries return metrics matching Gold layer (to 5 decimal places)
- ✅ Dashboard templates document key metric definitions
- ✅ Access control matrix aligns with Phase 4 hardening RBAC

### Batch 5.2 Stop-Gate Validation
- ✅ Streamlit app starts and loads without errors
- ✅ Query templates execute and return non-null results
- ✅ Session state persists across reruns; no data loss
- ✅ Performance profiling shows <2s query execution for common patterns

### Batch 5.3 Stop-Gate Validation
- ✅ LLM integration responds to 10 test queries
- ✅ LLM-generated queries map correctly to approved metric templates
- ✅ Safety validation catches 5/5 invalid query attempts (unauthorized metrics, data exfiltration patterns)
- ✅ Query logging captures all LLM interactions for audit

### Batch 5.4 Stop-Gate Validation
- ✅ Anomaly detection identifies 80%+ of injected anomalies in test data
- ✅ Insights generation produces human-readable period-over-period deltas
- ✅ Monitoring dashboard reflects current metric state with <5min staleness
- ✅ Alert email template is correct and recipients receive test alerts

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| LLM hallucinations producing invalid SQL | High | Query validation layer, approved template guardrails, audit logging |
| Metric parity drift between BI and Gold layer | High | Automated parity checks in each dashboard refresh; monitoring dashboard alerts |
| Performance degradation with high concurrent users | Medium | Query result caching, connection pooling, rate limiting on LLM queries |
| Snowflake cost overruns | Medium | Cost estimation in query validation; recommend read-only roles and query warming |
| LLM API key exposure in environment | High | Use GitHub Actions secrets; enforce `.env` in `.gitignore`; rotate keys regularly |

---

## Readiness Assessment

### Prerequisites Met (from Phase 4)
- ✅ Gold layer models complete and tested
- ✅ Semantic metric contract established
- ✅ BI consumption templates documented
- ✅ Governance framework in place
- ✅ CI/CD pipeline with conditional parity job
- ✅ Production deployment checklist

### Prerequisites to Address (Phase 5 setup)
- Metabase deployment infrastructure
- LLM API account (OpenAI or equivalent)
- Additional Python dependencies
- Updated environment configuration examples

---

## Success Criteria

**Phase 5 is successful when**:
1. All 4 batches complete with passing validation
2. Dashboard and Streamlit interfaces are accessible to stakeholders
3. LLM-generated queries are auditable and safe
4. Anomaly detection monitoring is operational
5. Parity with Gold layer is maintained across all interfaces
6. All governance logs and documentation are current
7. CI/CD integration is verified (if applicable)

---

## Next Steps (Approval Gates)

| Step | Owner | Gate |
|------|-------|------|
| 1) Review Phase 5 plan (this document) | Capstone lead | Approve scope and batch breakdown |
| 2) Implement Batch 5.1 (Dashboard foundation) | Engineering | Validation and stop-gate |
| 3) Implement Batch 5.2 (Streamlit app) | Engineering | Validation and stop-gate |
| 4) Implement Batch 5.3 (LLM integration) | Engineering | Validation and stop-gate |
| 5) Implement Batch 5.4 (Anomaly detection) | Engineering | Validation and stop-gate |
| 6) Create Phase 5 end report | Engineering | Readiness for defense/deployment |

---

**Awaiting approval to proceed to Batch 5.1.**
