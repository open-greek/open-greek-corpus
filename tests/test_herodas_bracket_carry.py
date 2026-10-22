"""An inherited source bracket excludes words before a new nested opener."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from herodas_body_readings_c import READINGS
from repair_herodas_body import _critical_flags, _word_ranges


def test_nested_first_opener_does_not_erase_inherited_exclusion():
    text = "λόγος [λέξις]] μένει"
    ranges = _word_ranges(text)
    inherited = _critical_flags(text, ranges, initial_brackets=["]"])
    assert [word for (word, _, _), flags in zip(ranges, inherited, strict=True) if not flags] == ["μένει"]
    fresh = _critical_flags(text, ranges, initial_brackets=[])
    assert [word for (word, _, _), flags in zip(ranges, fresh, strict=True) if not flags] == ["λόγος", "μένει"]


def test_actual_viii_prefix_stays_excluded_until_both_source_brackets_close():
    review = READINGS[442]
    assert review["initial_brackets"] == ["]"] and review["initial_brackets_evidence"]
    text = review["text"]
    ranges = _word_ranges(text)
    flags = _critical_flags(text, ranges, initial_brackets=review["initial_brackets"])
    end = text.index("]]") + 2
    assert all(reasons for (_, start, _), reasons in zip(ranges, flags, strict=True) if start < end)
    assert next(reasons for (word, _, _), reasons in zip(ranges, flags, strict=True) if word == "σχιστὸν") == []


def test_next_body_page_has_no_inherited_editorial_bracket():
    review = READINGS[444]
    assert review["initial_brackets"] == [] and review["initial_brackets_evidence"]
    ranges = _word_ranges(review["text"])
    flags = _critical_flags(review["text"], ranges, initial_brackets=review["initial_brackets"])
    assert next(reasons for (word, _, _), reasons in zip(ranges, flags, strict=True) if word == "δεινὰ") == []
