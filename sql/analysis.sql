-- analysis.sql
-- Advanced SQL analytics for insurance policy parsing results
-- Supports PostgreSQL, BigQuery, Snowflake (with minor adjustments)

-- ────────────────────────────────────────────────────────────────
-- 1. Coverage vs Premium Analysis
-- ────────────────────────────────────────────────────────────────

-- Segment policies by claim limit and analyze premium distribution
SELECT
    CASE
        WHEN claim_limit_gbp IS NULL THEN 'Unlimited'
        WHEN claim_limit_gbp < 1000 THEN 'Low (< £1k)'
        WHEN claim_limit_gbp < 5000 THEN 'Medium (£1k-£5k)'
        WHEN claim_limit_gbp < 10000 THEN 'High (£5k-£10k)'
        ELSE 'Very High (> £10k)'
    END AS coverage_tier,
    COUNT(*) AS policy_count,
    ROUND(AVG(gross_premium), 2) AS avg_premium,
    ROUND(MIN(gross_premium), 2) AS min_premium,
    ROUND(MAX(gross_premium), 2) AS max_premium,
    ROUND(SUM(gross_premium), 2) AS total_premium
FROM policies
WHERE parse_status != 'failed'
GROUP BY coverage_tier
ORDER BY
    CASE
        WHEN claim_limit_gbp IS NULL THEN 1
        WHEN claim_limit_gbp < 1000 THEN 2
        WHEN claim_limit_gbp < 5000 THEN 3
        WHEN claim_limit_gbp < 10000 THEN 4
        ELSE 5
    END;


-- ────────────────────────────────────────────────────────────────
-- 2. Parse Quality Segmentation
-- ────────────────────────────────────────────────────────────────

-- Distribution of parsing results with business metrics
SELECT
    parse_status,
    COUNT(*) AS count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_total,
    ROUND(AVG(gross_premium), 2) AS avg_premium,
    ROUND(AVG(claim_limit_confidence), 3) AS avg_limit_confidence,
    ROUND(AVG(excess_confidence), 3) AS avg_excess_confidence,
    COUNT(DISTINCT policy_number) AS unique_policies
FROM policies
GROUP BY parse_status
ORDER BY count DESC;


-- ────────────────────────────────────────────────────────────────
-- 3. Excess Distribution (Window Function)
-- ────────────────────────────────────────────────────────────────

-- Rank policies by excess within coverage tiers
SELECT
    policy_number,
    claim_limit_gbp,
    vetfees_excess_amount,
    gross_premium,
    RANK() OVER (
        PARTITION BY
            CASE
                WHEN claim_limit_gbp IS NULL THEN 'Unlimited'
                WHEN claim_limit_gbp < 5000 THEN 'Low'
                ELSE 'High'
            END
        ORDER BY vetfees_excess_amount DESC
    ) AS excess_rank_in_tier,
    ROUND(
        100.0 * CUME_DIST() OVER (ORDER BY vetfees_excess_amount),
        2
    ) AS excess_percentile
FROM policies
WHERE parse_status IN ('parsed', 'partial')
ORDER BY
    CASE
        WHEN claim_limit_gbp < 5000 THEN 'Low'
        ELSE 'High'
    END,
    excess_rank_in_tier;


-- ────────────────────────────────────────────────────────────────
-- 4. Risk Segmentation with NTILE (Quartiles)
-- ────────────────────────────────────────────────────────────────

-- Classify policies into risk quartiles based on premium + coverage
SELECT
    NTILE(4) OVER (ORDER BY gross_premium * COALESCE(claim_limit_gbp, 50000) DESC)
        AS risk_quartile,
    COUNT(*) AS policy_count,
    ROUND(AVG(gross_premium), 2) AS avg_premium,
    ROUND(AVG(claim_limit_gbp), 0) AS avg_claim_limit,
    ROUND(AVG(vetfees_excess_amount), 2) AS avg_excess,
    MIN(gross_premium) AS min_premium,
    MAX(gross_premium) AS max_premium
FROM policies
WHERE parse_status != 'failed'
GROUP BY risk_quartile
ORDER BY risk_quartile;


-- ────────────────────────────────────────────────────────────────
-- 5. Confidence Quality Check
-- ────────────────────────────────────────────────────────────────

-- Identify low-confidence extractions that may need LLM review
SELECT
    COUNT(*) AS record_count,
    ROUND(AVG(claim_limit_confidence), 3) AS avg_limit_confidence,
    ROUND(AVG(excess_confidence), 3) AS avg_excess_confidence,
    SUM(CASE WHEN claim_limit_confidence < 0.7 THEN 1 ELSE 0 END)
        AS low_confidence_limits,
    SUM(CASE WHEN excess_confidence < 0.7 AND excess_confidence > 0 THEN 1 ELSE 0 END)
        AS low_confidence_excess
FROM policies;


-- ────────────────────────────────────────────────────────────────
-- 6. Premium Efficiency by Coverage Level
-- ────────────────────────────────────────────────────────────────

-- Cost per unit of coverage (premium per £1000 of limit)
SELECT
    CASE
        WHEN claim_limit_gbp IS NULL THEN 'Unlimited'
        ELSE CONCAT('£', ROUND(claim_limit_gbp, -3)::TEXT)
    END AS coverage_bracket,
    COUNT(*) AS policy_count,
    ROUND(AVG(gross_premium), 2) AS avg_premium,
    ROUND(AVG(gross_premium) / NULLIF(claim_limit_gbp / 1000, 0), 2)
        AS premium_per_1k_coverage,
    ROUND(STDDEV(gross_premium), 2) AS premium_stddev
FROM policies
WHERE claim_limit_gbp IS NOT NULL
    AND claim_limit_gbp > 0
    AND parse_status IN ('parsed', 'partial')
GROUP BY claim_limit_gbp
HAVING COUNT(*) >= 5
ORDER BY claim_limit_gbp;
