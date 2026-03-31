select
    lead_id,
    match_confidence,
    match_confidence_band
from {{ ref('int_lead_account_resolved') }}
where (match_confidence_band = 'high' and match_confidence < 0.95)
   or (match_confidence_band = 'medium' and (match_confidence < 0.85 or match_confidence >= 0.95))
   or (match_confidence_band = 'low' and match_confidence >= 0.85)
