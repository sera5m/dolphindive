from dolphindive.engine.fuzzy import fuzzy_score
from dolphindive.engine.query import parse_query
from dolphindive.engine.rank import Hit, RankMode, next_mode, score_hit


def test_fuzzy_abbreviation():
    assert fuzzy_score("vs", "VisualStudio") is not None
    assert fuzzy_score("vs", "VisualStudio") > fuzzy_score("vs", "xxxvsxxx")


def test_fuzzy_prefix_wins():
    a = fuzzy_score("rep", "report.pdf")
    b = fuzzy_score("rep", "older-report-final.pdf")
    assert a is not None and b is not None
    assert a >= b


def test_fuzzy_reject():
    assert fuzzy_score("zzz", "readme.md") is None


def test_parse_filters():
    q = parse_query("invoice doc: ext:pdf;odt projects/")
    assert q.text == "invoice"
    assert q.kind == "doc"
    assert q.extensions == {".pdf", ".odt"}
    assert q.path_hint == "projects"


def test_parse_star_ext():
    q = parse_query("shader *.glsl")
    assert q.text == "shader"
    assert ".glsl" in q.extensions


def test_rank_modes_cycle():
    assert next_mode(RankMode.SMART) is RankMode.FUZZY_ONLY
    assert next_mode(RankMode.INVERT) is RankMode.SMART


def test_usage_boosts_smart_rank():
    cold = Hit(path="/tmp/a.pdf", name="budget.pdf", is_dir=False, opens=0)
    hot = Hit(path="/tmp/b.pdf", name="budget.pdf", is_dir=False, opens=20, last_open=1e12)
    c = score_hit(cold, "budget", RankMode.SMART)
    h = score_hit(hot, "budget", RankMode.SMART)
    assert h.final > c.final
