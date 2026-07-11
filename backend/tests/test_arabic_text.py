from app.services.arabic_text import ReferenceWord, align, normalize_arabic, tokenize


def test_normalize_strips_diacritics():
    diacritized = "بِسْمِ"
    assert normalize_arabic(diacritized) == normalize_arabic("بسم")


def test_normalize_unifies_alef_variants():
    assert normalize_arabic("أحمد") == normalize_arabic("احمد")
    assert normalize_arabic("إحسان") == normalize_arabic("احسان")
    assert normalize_arabic("آدم") == normalize_arabic("ادم")


def test_normalize_unifies_taa_marbuta_and_alef_maksura():
    assert normalize_arabic("رحمة") == normalize_arabic("رحمه")
    assert normalize_arabic("موسى") == normalize_arabic("موسي")


def test_tokenize_splits_on_whitespace_after_normalizing():
    assert tokenize("بِسْمِ اللَّهِ الرَّحْمَٰنِ") == tokenize("بسم الله الرحمن")


def test_align_all_words_match():
    reference = [ReferenceWord(word=w, ayah_number=1) for w in ["بسم", "الله", "الرحمن"]]
    matched, mistakes = align(reference, "بسم الله الرحمن")
    assert matched == 3
    assert mistakes == []


def test_align_detects_missing_word():
    reference = [ReferenceWord(word=w, ayah_number=1) for w in ["بسم", "الله", "الرحمن", "الرحيم"]]
    matched, mistakes = align(reference, "بسم الرحمن الرحيم")
    assert matched == 3
    assert len(mistakes) == 1
    assert mistakes[0].mistake_type == "missing"
    assert mistakes[0].reference_word == "الله"
    assert mistakes[0].ayah_number == 1


def test_align_detects_extra_word():
    reference = [ReferenceWord(word=w, ayah_number=1) for w in ["بسم", "الله"]]
    matched, mistakes = align(reference, "بسم الله الرحمن")
    assert matched == 2
    assert len(mistakes) == 1
    assert mistakes[0].mistake_type == "extra"
    assert mistakes[0].transcribed_word == "الرحمن"
    assert mistakes[0].ayah_number is None


def test_align_detects_substituted_word():
    reference = [ReferenceWord(word=w, ayah_number=2) for w in ["الحمد", "لله", "رب", "العالمين"]]
    matched, mistakes = align(reference, "الحمد لله رب العلمين")
    assert len(mistakes) == 1
    assert mistakes[0].mistake_type == "substituted"
    assert mistakes[0].reference_word == "العالمين"
    assert mistakes[0].transcribed_word == "العلمين"
    assert mistakes[0].ayah_number == 2


def test_align_spans_multiple_ayahs():
    reference = [
        ReferenceWord(word="الحمد", ayah_number=1),
        ReferenceWord(word="لله", ayah_number=1),
        ReferenceWord(word="الرحمن", ayah_number=2),
        ReferenceWord(word="الرحيم", ayah_number=2),
    ]
    matched, mistakes = align(reference, "الحمد لله")
    assert matched == 2
    assert {m.ayah_number for m in mistakes} == {2}
