from pathlib import Path

from voi_bw_commander.eval import evaluate_corpus


def test_parser_corpus_passes() -> None:
    report = evaluate_corpus(Path("fixtures/parser_corpus.json"))

    assert report.passed
    assert report.score == 1.0
