# Decimal reference for offline practice

Construct monetary values from strings, for example `Decimal("10.005")`.
Constructing from a binary float carries its approximation into the Decimal.

Use `value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)` to round to cents.
With this mode, a tie rounds away from zero: EUR 10.005 becomes EUR 10.01.
The default Decimal rounding mode is half-even, so specify the business rule
explicitly instead of relying on the process's current Decimal context.

Rounding changes a value. Rounding each line and then adding can differ from
adding unrounded lines and rounding once. Apply rounding at the boundaries
specified by the customer; tests should distinguish those two calculations.

Use Decimal constants throughout arithmetic and comparisons. Python's `sum`
accepts a starting value, which lets an accumulated subtotal stay a Decimal.

Reference: [Python Decimal documentation](https://docs.python.org/3/library/decimal.html).
