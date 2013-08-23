from tests import TestSimpatico

class TestIndents(TestSimpatico):

    def test_indents(self):
        expected_error_lines = [4, 9, 12, 14, 32, 33, 36, 47]

        f = 'tests/files/indents.c'
        s = self.run_simpatico(f)
        indent_errors = len(s.errors.indent_d.keys())
        found_error_lines = set(s.errors.indent_d.keys())

        self.assertEqual(indent_errors, len(expected_error_lines))
        self.assertSetEqual(found_error_lines, set(expected_error_lines))

if __name__ == "__main__":
    unittest.main()
