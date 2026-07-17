# Reader observations, not psychological profiles

The project may connect a public commenter to other user-selected public comments only to summarize observable activity. It must not infer sensitive or clinical traits.

## Permitted observations

- public profile URL and display name;
- works/chapters on which the person commented in the imported evidence set;
- timestamps and repeat activity;
- evidence-linked topic tags;
- feedback stance such as praise, question, correction, objection, or continuation request;
- whether a tag was produced by a human, deterministic rule, or model;
- confidence and human confirmation state.

## Prohibited inferences

- health, disability, diagnosis or mental state;
- political or religious beliefs;
- sexual orientation or intimate life;
- ethnicity, income, exact age or other sensitive attributes;
- manipulative targeting or vulnerability scoring;
- a definitive personality type from comments;
- claims about the silent readership based only on active commenters.

## Evidence chain

```text
aggregate tag
  -> taxonomy path + stance
  -> exact evidence excerpt
  -> full imported comment
  -> work/chapter + timestamp
  -> original public URL and profile URL
```

Any aggregate must remain drillable to its supporting records. A model-generated tag is a review candidate, not a fact. Only `confirmed=1` may be shown as human-confirmed.

## Data minimization

A local installation should support export and deletion by profile URL. Public comments remain personal data when they identify a person; public visibility is not unlimited consent for republishing a dossier. The default UI therefore shows evidence for the owner's analysis and does not publish profile reports.
