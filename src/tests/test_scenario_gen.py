# src/tests/test_scenario_gen.py

import os
import unittest
import tempfile
import datetime
from PyQt5.QtWidgets import QMessageBox

# Import your scenario code from src/modules/scenario_generator.py
from modules.scenario_generator import (
    SDSMContext,
    modify_data,
    parse_value,
    increase_date,
    check_settings,
)


def no_op_message(*args, **kwargs):
    """
    A no-op function to override QMessageBox calls during tests,
    so your test run isn't interrupted by GUI popups.
    """
    pass


class TestScenarioGenerator(unittest.TestCase):
    def setUp(self):
        """
        Called before each test method. We override QMessageBox methods
        so that no dialogs appear during tests.
        """
        QMessageBox.critical = no_op_message
        QMessageBox.information = no_op_message

    def test_increase_date(self):
        """
        Test that increase_date properly advances a date, including leap years.
        """
        dt = datetime.date(2020, 2, 28)
        next_day = increase_date(dt)
        self.assertEqual(
            next_day,
            datetime.date(2020, 2, 29),
            "Should advance to Feb 29 in a leap year.",
        )
        next_day = increase_date(next_day)
        self.assertEqual(
            next_day, datetime.date(2020, 3, 1), "Should advance to Mar 1 after Feb 29."
        )

    def test_check_settings(self):
        """
        Test that check_settings enforces file/treatment requirements.
        """
        ctx = SDSMContext()

        # No input, no output, no treatments => fail
        self.assertFalse(check_settings(ctx))

        ctx.in_file = "dummy_in.txt"
        ctx.in_root = "/some/path/dummy_in.txt"
        # Still no output => fail
        self.assertFalse(check_settings(ctx))

        ctx.out_file = "dummy_out.txt"
        ctx.out_root = "/some/path/dummy_out.txt"
        # No treatments => fail
        self.assertFalse(check_settings(ctx))

        # Now enable at least one treatment => pass
        ctx.amount_check = True
        self.assertTrue(check_settings(ctx))

    def test_parse_value_line_by_line(self):
        """
        Demonstrates subTest for line-by-line checks of parse_value.
        In verbose mode, you'll see a separate pass/fail line per subTest.
        """
        ctx = SDSMContext()
        test_cases = [
            (" 12.34 ", 12.34),
            ("-999", ctx.global_missing_code),
            ("not_a_number", ctx.global_missing_code),
            (" 42.1 ", 42.1),
        ]
        for raw_str, expected in test_cases:
            with self.subTest(raw_str=raw_str):
                result = parse_value(raw_str, ctx)
                self.assertEqual(
                    result, expected, f"parse_value('{raw_str}') should be {expected}."
                )

    def test_modify_data_with_sample_input(self):
        """
        Integration test: read from src/test_data/sample_input.txt,
        run modify_data, and check the output.
        """
        # Locate your sample_input.txt file
        test_data_dir = os.path.join(
            os.path.dirname(__file__),  # .../src/tests
            "..",  # .../src
            "test_data",  # .../src/test_data
        )
        sample_input_path = os.path.join(test_data_dir, "sample_input.txt")

        # Create a temporary file path for output
        tmp_out_fd, tmp_out_path = tempfile.mkstemp()
        os.close(tmp_out_fd)  # We'll open it ourselves

        # Set up the scenario context
        ctx = SDSMContext()
        ctx.in_file = "sample_input.txt"
        ctx.in_root = sample_input_path
        ctx.out_file = "sample_output.txt"
        ctx.out_root = tmp_out_path
        ctx.ensemble_size = 1

        # Must enable at least one treatment for check_settings() to pass
        ctx.amount_check = True
        # We'll choose a factor-based approach with 0% => no real change
        ctx.amount_option = 0
        ctx.amount_factor = 0
        ctx.amount_factor_percent = 1.0

        # Run the scenario generator
        modify_data(ctx)

        # Verify the output file was created and read it
        with open(tmp_out_path, "r") as f:
            lines = f.readlines()

        with open(sample_input_path, "r") as f:
            input_lines = f.readlines()

        # If sample_input.txt has 10 lines, we expect 10 lines of output
        # Adjust as needed if your file has a different number of lines.
        self.assertEqual(
            len(lines),
            len(input_lines),
            "Output file should have the same number of lines as input.",
        )

        # The first line might contain "0.000" (depending on your data).
        # Adjust this assertion as needed if your sample_input starts with a different value.
        self.assertIn(
            "0.000",
            lines[0],
            "First line should contain 0.000 if factor=1 => no change to day 1 data.",
        )

        # Cleanup
        os.remove(tmp_out_path)


if __name__ == "__main__":
    # Run tests with higher verbosity to see line-by-line subTest results
    unittest.main(verbosity=2)
