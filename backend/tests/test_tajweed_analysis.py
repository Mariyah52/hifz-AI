from app.services.quran_text import TajweedWord
from app.services.tajweed_analysis import analyze_elongation
from app.services.transcription import WordTiming


def _reference():
    return [
        TajweedWord(word="الرحمن", ayah_number=1, elongation_rule=None),
        TajweedWord(word="الرحيم", ayah_number=1, elongation_rule=None),
        TajweedWord(word="الضالين", ayah_number=1, elongation_rule="madda_necessary"),
        TajweedWord(word="ولا", ayah_number=1, elongation_rule=None),
        TajweedWord(word="الضالين", ayah_number=1, elongation_rule=None),
    ]


def test_properly_elongated_word_is_not_flagged():
    timings = [
        WordTiming(word="الرحمن", start_seconds=0.0, end_seconds=0.4),
        WordTiming(word="الرحيم", start_seconds=0.4, end_seconds=0.8),
        WordTiming(word="الضالين", start_seconds=0.8, end_seconds=1.7),  # held long
        WordTiming(word="ولا", start_seconds=1.7, end_seconds=2.1),
        WordTiming(word="الضالين", start_seconds=2.1, end_seconds=2.5),
    ]
    assert analyze_elongation(_reference(), timings) == []


def test_rushed_elongated_word_is_flagged():
    timings = [
        WordTiming(word="الرحمن", start_seconds=0.0, end_seconds=0.4),
        WordTiming(word="الرحيم", start_seconds=0.4, end_seconds=0.8),
        WordTiming(word="الضالين", start_seconds=0.8, end_seconds=1.0),  # only 0.2s -- rushed
        WordTiming(word="ولا", start_seconds=1.0, end_seconds=1.4),
        WordTiming(word="الضالين", start_seconds=1.4, end_seconds=1.8),
    ]
    flags = analyze_elongation(_reference(), timings)
    assert len(flags) == 1
    assert flags[0].word == "الضالين"
    assert flags[0].rule == "madda_necessary"
    assert flags[0].actual_seconds < flags[0].expected_minimum_seconds


def test_non_elongated_words_are_never_flagged_even_if_short():
    # Every non-elongated word here is unusually short/uniform -- none
    # should ever be flagged, since flagging only ever applies to
    # elongation-tagged reference words.
    timings = [
        WordTiming(word="الرحمن", start_seconds=0.0, end_seconds=0.1),
        WordTiming(word="الرحيم", start_seconds=0.1, end_seconds=0.2),
        WordTiming(word="الضالين", start_seconds=0.2, end_seconds=0.9),  # still adequately elongated
        WordTiming(word="ولا", start_seconds=0.9, end_seconds=1.0),
        WordTiming(word="الضالين", start_seconds=1.0, end_seconds=1.1),
    ]
    flags = analyze_elongation(_reference(), timings)
    assert all(f.rule != "madda_normal" or f.word not in ("الرحمن", "الرحيم", "ولا") for f in flags)
    for f in flags:
        assert f.rule in ("madda_necessary", "madda_obligatory", "madda_normal", "madda_permissible")


def test_returns_no_flags_with_too_few_non_elongated_words_for_a_baseline():
    # Only 2 non-elongated words -- below the minimum sample size this
    # module requires before trusting a personal baseline at all.
    reference = [
        TajweedWord(word="ا", ayah_number=1, elongation_rule=None),
        TajweedWord(word="ب", ayah_number=1, elongation_rule="madda_necessary"),
        TajweedWord(word="ج", ayah_number=1, elongation_rule=None),
    ]
    timings = [
        WordTiming(word="ا", start_seconds=0.0, end_seconds=0.3),
        WordTiming(word="ب", start_seconds=0.3, end_seconds=0.4),  # would look rushed, but...
        WordTiming(word="ج", start_seconds=0.4, end_seconds=0.7),
    ]
    assert analyze_elongation(reference, timings) == []


def test_returns_empty_list_when_nothing_aligns_at_all():
    reference = [TajweedWord(word="الرحمن", ayah_number=1, elongation_rule="madda_normal")]
    timings = [WordTiming(word="completely different transcription", start_seconds=0.0, end_seconds=1.0)]
    assert analyze_elongation(reference, timings) == []
