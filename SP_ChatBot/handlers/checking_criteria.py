import re
import pymorphy2

morph = pymorphy2.MorphAnalyzer()

FIRST_PERSON_PRONOUNS = {
    "мы", "нас", "нам", "нами",
    "наш", "наши", "нашего", "нашему", "нашим", "наших"
}

def contains_label0_features(sentence: str) -> bool:
    words = sentence.lower().split()
    for word in words:
        parsed = morph.parse(word)[0]
        tag = parsed.tag

        # местоимения 1-го лица множественного числа
        if word in FIRST_PERSON_PRONOUNS:
            return True

        # глаголы 1-го лица множественного числа
        if ("VERB" in tag or "INFN" in tag) and "1per" in tag and "plur" in tag:
            return True

        # глаголы совершенного вида
        if ("VERB" in tag or "INFN" in tag) and "perf" in tag:
            return True

        # страдательный залог
        if "pssv" in tag:
            return True

        # причастия и деепричастия
        if "PRTF" in tag or "GRND" in tag:
            return True

    return False

FIRST_PERSON_SING_PRONOUNS = {
    "я", "меня", "мне", "мной", "мой", "моя", "моё", "мои"
}

DEVERBAL_SUFFIXES = (
    "ние", "ция", "тельство", "ание", "ение", "ка"
)

def looks_like_deverbal(noun: str) -> bool:
    return noun.endswith(DEVERBAL_SUFFIXES)

def contains_label1_features(sentence: str) -> bool:
    words = sentence.lower().split()
    parsed_words = [(w, morph.parse(w)[0]) for w in words]

    # местоимения и глаголы 1-го лица ед. числа
    for w, p in parsed_words:
        if w in FIRST_PERSON_SING_PRONOUNS:
            return True
        tag = p.tag
        if ("VERB" in tag or "INFN" in tag) and "1per" in tag and "sing" in tag:
            return True

    #отглагольные существительные
    if any("NOUN" in p.tag and looks_like_deverbal(w) for w, p in parsed_words):
        return True

    #глаголы несовершенного вида
    if any(("VERB" in p.tag or "INFN" in p.tag) and "impf" in p.tag for w, p in parsed_words):
        return True

    # перечисление действий (>=3 глаголов подряд)
    tokens = re.split(r"[,\s]+", sentence.lower())
    run = 0
    for t in tokens:
        p = morph.parse(t)[0]
        if "VERB" in p.tag or "INFN" in p.tag:
            run += 1
            if run >= 3:
                return True
        else:
            run = 0

    return False
