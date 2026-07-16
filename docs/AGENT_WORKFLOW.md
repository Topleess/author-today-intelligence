# Agent workflow

## Goal

Turn changing platform facts into one decision, not a wall of metrics.

## Procedure

1. Ask which author, works, cohort, and period matter.
2. Fetch documented API data first.
3. Save timestamp, complete source URL, and raw normalized snapshot.
4. Require at least two observations before calculating velocity.
5. Annotate known events: chapter release, price, cover, post, ad, completion.
6. Separate output into:
   - **Observed:** directly supported by stored evidence.
   - **Hypothesis:** a plausible explanation.
   - **Missing evidence:** what prevents a stronger conclusion.
   - **Next experiment:** one measurable change.
7. Quote comments minimally and preserve source/time.
8. Require approval before any external action.

## Claims to avoid

- “We discovered the ranking algorithm.”
- “The ad caused the growth” from a before/after line alone.
- “createOrder equals a paid sale.”
- “Public views equal unique readers.”

## Reusable user outcome

A useful agent message is short:

> **Changed:** reading entry rose after chapter 8.  
> **Likely:** returning readers, not new traffic.  
> **Unknown:** no campaign-level traffic data.  
> **Try next:** hold price/cover constant and publish the next chapter at the same time.
