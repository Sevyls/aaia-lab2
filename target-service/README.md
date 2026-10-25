# Order service repair

Work from this directory. Read docs/business-rules.md before changing pricing.
Run `python -m unittest discover -s tests -v`. The supplied baseline has nine
tests: five fail and four pass. Do not weaken acceptance tests.
The agent should repair orders/pricing.py. Add tests/test_student.py yourself:
the Week 2 agent's write tool can change only pricing. Choose a regression that
fails against the baseline and passes after the repair.

Keep your agent outside this target directory. This separates its implementation
and permissions from files it is allowed to change. Initialize a local Git
repository here before the first run so you can inspect the repair with git diff.
