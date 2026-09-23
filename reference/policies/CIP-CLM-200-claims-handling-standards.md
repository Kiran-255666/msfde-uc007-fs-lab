# CIP-CLM-200 Claims Handling Standards

> **FICTIONAL TRAINING DOCUMENT.** Contoso Insurance Group is not a real insurer. This
> content was written for the Microsoft FDE capstone lab.

| Field | Value |
|---|---|
| Document ID | CIP-CLM-200 |
| Version | 6.3 |
| Effective date | 2026-06-01 |
| Owner | Claims Operations |
| Applies to | All claims handlers, and to any automated system that prepares claims for review |

## 1. Required evidence by claim type

A claim is **not complete** until every document listed for its type is on file.

| Claim type | Required evidence |
|---|---|
| Collision (any) | Claim form, policy schedule, repair estimate, customer statement, photographs of the damage |
| Collision with a third party | The above, plus third-party details and a police reference where the police attended |
| Theft or attempted theft | Claim form, policy schedule, repair estimate, customer statement, **police crime reference obtained within 5 days**, photographs |
| Malicious damage or vandalism | As for theft, including the **crime reference** |
| Weather, hail, flood or falling object | Claim form, policy schedule, repair estimate, customer statement, photographs. A police reference is **not** required |
| Glass only | Claim form, policy schedule, glass supplier invoice, photographs |

1.1 Photographs must show the damaged area and at least one wider view that identifies the
vehicle.

1.2 Where a required document is missing, the claim is placed in **Awaiting information** and
the policyholder is contacted within **2 business days** with a single, consolidated list of
what is outstanding.

## 2. Data quality checks

Every claim is checked for the following before it goes to an adjuster:

2.1 **Date of loss** must be the same on the claim form, the customer statement and any police
report. Any difference is a discrepancy and must be resolved before settlement.

2.2 **Vehicle identifiers** (VIN and registration plate) must match across the claim form, the
policy schedule, the repair estimate and any police report.

2.3 **The described damage location** must be consistent across the customer statement, the
claim form, the repair estimate and the photographs.

2.4 **Cover must have been in force** on the date of loss, per CIP-POL-100 section 1.1.

2.5 The **named driver** at the time of the loss must appear on the policy schedule.

## 3. Authority limits

| Role | May approve up to |
|---|---|
| Claims handler | $5,000 |
| Senior adjuster | $25,000 |
| Claims manager | $100,000 |
| Head of Claims | Above $100,000 |

3.1 A claim whose estimated cost exceeds the handler limit is **referred upward**; it is not
declined for that reason.

3.2 Coverage decisions - including any decision that cover was not in force - are made by a
**senior adjuster or above**, never by a handler and never by an automated system.

## 4. Service standards

| Step | Standard |
|---|---|
| Acknowledge a new claim | 1 business day |
| Request outstanding information | 2 business days |
| Complete the claim review | 5 business days from receipt of complete evidence |
| Decision communicated to the policyholder | 2 business days after the decision |
| Refer to the Special Investigations Unit | Same day the indicator is identified |

## 5. Automated claim preparation

5.1 Automated tools may classify documents, extract data, check completeness, compare
evidence and draft a summary with recommendations.

5.2 An automated system must **never approve a claim, decline a claim, authorise a payment or
tell a policyholder the outcome**. Those actions are reserved for authorised staff.

5.3 Every automated finding must cite the document and field it came from, so a handler can
verify it without re-reading the whole file.

5.4 Where evidence is missing, ambiguous or contradictory, the system must say so plainly
rather than resolve it by assumption.

5.5 Every claim prepared automatically is reviewed by a named handler, who records
**accept**, **amend** or **reject** against the recommendation, with a note.

## 6. Related documents

- CIP-POL-100 Contoso Motor Policy Wording
- CIP-CLM-210 Fraud Indicators and SIU Referral Guidance
- CIP-CLM-220 Repair Network and Estimate Validation Standards
