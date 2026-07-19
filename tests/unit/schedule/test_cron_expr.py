"""UT-S03/S04 — validate_cron_expression."""

from __future__ import annotations

import unittest

from github_rag.schedule.cron_expr import validate_cron_expression
from github_rag.schedule.errors import InvalidCronExpressionError


class TestValidateCronExpression(unittest.TestCase):
    def test_accepts_common_expressions(self) -> None:
        for expr in ("0 2 * * *", "0 */6 * * *", "0 0,12 * * *", " 0 2 * * * "):
            with self.subTest(expr=expr):
                self.assertEqual(
                    validate_cron_expression(expr), expr.strip()
                )

    def test_rejects_invalid(self) -> None:
        for expr in ("not-a-cron", "60 * * * *", "0 2 * *", "", "   ", "* *"):
            with self.subTest(expr=expr):
                with self.assertRaises(InvalidCronExpressionError) as ctx:
                    validate_cron_expression(expr)
                message = str(ctx.exception)
                self.assertTrue(message)
                if expr.strip():
                    # mensagem cita algo da expressão (ou truncamento)
                    self.assertIn(expr.strip()[:20], message)

    def test_long_expression_message_truncated(self) -> None:
        huge = "x" * 300
        with self.assertRaises(InvalidCronExpressionError) as ctx:
            validate_cron_expression(huge)
        self.assertLessEqual(len(str(ctx.exception)), 280)


if __name__ == "__main__":
    unittest.main()
