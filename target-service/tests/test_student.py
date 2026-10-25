"""Student regression: a line is rounded after multiplying by quantity."""
import unittest
from decimal import Decimal as D
from orders.pricing import quote


class StudentRegression(unittest.TestCase):
    def test_multi_quantity_line_rounded_after_multiplication(self):
        # 0.335 * 3 = 1.005 -> 1.01 (ROUND_HALF_UP); goods < 100 so shipping 5.00.
        # Rounding the unit price first would give 0.34 * 3 = 1.02.
        result = quote([{"unit_price": D("0.335"), "quantity": 3}])
        self.assertEqual(result["subtotal"], D("1.01"))
        self.assertEqual(result["shipping"], D("5.00"))
        self.assertEqual(result["total"], D("6.01"))


if __name__ == "__main__":
    unittest.main()
