import os
import re
import unittest


class TestTeachingCorpus(unittest.TestCase):
    def test_teaching_corpus_accuracy(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        corpus_path = os.path.join(root_dir, "TEACHING_CORPUS.md")
        examples_dir = os.path.join(root_dir, "examples")

        self.assertTrue(os.path.exists(corpus_path), "TEACHING_CORPUS.md is missing")

        with open(corpus_path, "r", encoding="utf-8") as file:
            corpus_content = file.read()

        referenced_files = set(re.findall(r"([a-zA-Z0-9_]+\.nq)", corpus_content))
        actual_files = {name for name in os.listdir(examples_dir) if name.endswith(".nq")}

        for referenced in referenced_files:
            self.assertIn(
                referenced,
                actual_files,
                f"Referenced file {referenced} in TEACHING_CORPUS.md does not exist in examples/",
            )

        for actual in actual_files:
            self.assertIn(actual, referenced_files, f"Example {actual} is not documented in TEACHING_CORPUS.md")


if __name__ == "__main__":
    unittest.main()
