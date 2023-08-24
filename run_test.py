import unittest


class TestLoader(unittest.TestLoader):
    def discover(self, start_dir: str, pattern: str = ..., top_level_dir: str | None = ...) -> unittest.suite.TestSuite:
        pattern = '*_test.py'
        return super().discover(start_dir, pattern, top_level_dir)


if __name__ == '__main__':
    unittest.main(module=None, testLoader=TestLoader())
