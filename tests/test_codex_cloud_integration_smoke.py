import unittest


def normalize_label(label: str) -> str:
    return label.strip()


class CodexCloudIntegrationSmokeTest(unittest.TestCase):
    def test_trims_surrounding_whitespace(self):
        self.assertEqual(normalize_label('  codex  '), 'codex')


if __name__ == '__main__':
    unittest.main()
