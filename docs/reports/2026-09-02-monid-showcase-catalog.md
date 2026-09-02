# Monid Showcase Catalog Receipt

## Receipt boundary

- Observed: `2026-09-02T11:21:32-04:00` (`America/New_York`)
- Monid CLI: `0.1.7`
- Monid skill: `0.1.7`
- Operation: five `monid discover` catalog searches, limit 3 each
- Paid endpoint execution: **none**
- Amount spent by this catalog check: **$0.00**

Discovery returned catalog metadata only. No `monid run` or `monid runs`
command was issued. No product, company, or incident subject was sent. Prices
and health below are the published values observed at the timestamp and may
change as the catalog changes.

## Observed catalog evidence

| Discovery phrase | Representative relevant provider and endpoint | Published price | Health |
| --- | --- | --- | --- |
| `brand mentions public web` | Strale, `/x402/brand-mention-search` | `$0.3564` per call | `stable` |
| `SEO organic competitors keywords` | Ahrefs, `/site-explorer/organic-competitors` | `$0.042` per result | `stable` |
| `company enrichment public data` | Akta, `/v1/company/enrichment` | `$0.125` per result | `stable` |
| `product prices reviews inventory` | Capterra, `/get_product_reviews` | `$0.01` per call | `stable` |
| `company news incidents outages` | Context.dev, `/news/search` | `$0.00009` per result | `stable` |

These rows are candidate evidence, not endorsements and not proof that a paid
run would satisfy an application. The shared planner must inspect the current
schema, calculate the bounded cost, and retain `paid_endpoint_executed: false`
before a developer considers a separately authorized live fixture.

## Why the receipt matters

The catalog confirms that the five showcase families map to real metered tool
surfaces: public brand signals, organic-search competitors, company enrichment,
product reviews, and company news. CAM_Codx adds the missing product discipline:
an existing-tool check, an acceptance test, a normalized adapter boundary, a
cost ceiling, and evidence labels that prevent discovery from becoming a false
completion claim.
