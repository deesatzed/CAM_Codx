# Monid Whisky Shopping Proof

## Receipt boundary

- Revalidated: `2026-09-03` (`America/New_York`)
- Monid CLI: `0.1.7`
- Paid endpoint: Apify `/burbn/google-shopping-scraper`
- Paid runs completed: `2`
- Results returned and billed: `18`
- Total Monid cost: `$0.151 USD`
- Purchases placed: `0`
- Credentials, account data, payment data, and private street addresses sent: `0`

The two runs used public product queries and a small result limit. Monid supplied
shopping leads. CAM_Codx then checked product identity, current merchant pages,
stock signals, shipping policies, delivered-price evidence, and seller risk.
Indexed shopping data was never treated as a verified purchase offer by itself.

## Case 1: Springbank 10 under $120 delivered to 19002

- Run ID: `01M1JAY91KXVGXK88YP4VQ0JRT`
- Status: `COMPLETED`, provider HTTP `200`
- Results/billed units: `8`
- Actual cost: `$0.068 USD`
- Verdict: **no seller met the full acceptance test**

The result set included wrong expressions, stale or unresolvable listings,
location-specific delivery language, a sold-out listing, a seller with material
trust concerns, and sellers whose public shipping rules did not establish a
legal delivered offer to Pennsylvania below the requested ceiling. The useful
answer was a defensible negative, not the lowest indexed number.

An earlier attempt against Strale `/x402/product-search` completed with provider
HTTP `404`, zero results, and `$0.00` cost. Run ID:
`01M1J858VMQ9HAVG2PZKDF76QV`.

## Case 2: Best delivered price for Port Charlotte 18 to 19002

- Run ID: `01M1KJMYSHW61X1563RWJP4BKW`
- Status: `COMPLETED`, provider HTTP `200`
- Results/billed units: `10`
- Actual cost: `$0.083 USD`
- Best verified shopping result: Liquor Cave, exact available `700 mL` variant
  at `$186.99`
- Anonymous checkout rate to ZIP `19002`: UPS Ground at `$43.44`
- Bottle plus shipping: `$230.43` before tax

No order was placed. The merchant's public policy shifts responsibility for
state-law compliance to the buyer and does not publish a definitive supported-
state list. The checkout response therefore proves that the site offered a
rate to the ZIP, not that delivery is legally guaranteed or that the merchant
will ultimately fulfill the order.

Lower indexed results were rejected when they referred to Bruichladdich 18
rather than Port Charlotte 18, omitted the age statement, were sold out or
backordered, or could not produce a destination-specific delivered total.

## What this proves

The product-intelligence workflow can use a low-cost metered discovery tool to
broaden the candidate set, then apply an application-specific acceptance test.
It can return both a qualified positive and an honest negative while retaining
run identity, cost, source boundaries, and rejected-candidate reasons.

It does not prove continuous inventory accuracy, retailer reliability, legal
shipping eligibility, checkout completion, or a production WhiskeySages
integration. Prices and availability are observations from the validation
dates and will change.

## Public validation sources

- <https://www.hiproof.com/products/port-charlotte-18-year-aged-islay-single-malt-scotch-2026-release>
- <https://www.hiproof.com/pages/shipping-policy>
- <https://www.remedyliquor.com/products/bruichladdich-scotch-port-charlotte-single-malt-islay-heavy-peated-18yr-700ml>
- <https://www.saratogawine.com/product/bruichladdich-port-charlotte-scotch-single-malt-18-year-700ml/>
- <https://www.saratogawine.com/more-info/shipping-info/>
- <https://www.liquorcave.com/products/bruichladdich-port-charlotte-18-year-old>
- <https://www.liquorcave.com/policies/shipping-policy>
- <https://tipxy.com/collections/campbeltown-scotch>
- <https://concierge.totalwine.com/shipping>
- <https://www.oldtowntequila.com/springbank-10-year-old-single-malt-whisky-700ml/>
- <https://liquorama.com/customer-service/>
