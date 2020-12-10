import regex
import mojimoji


def cleaning(raw_doc):
    """
    特許文書を正規化する．

    Parameters
    ----------
    raw_doc : str
        特許の生テキストデータ

    Returns
    -------
    cleaned_doc : str
        正規化された特許のテキストデータ
    """
    cleaned = regex.sub(r'<[\/A-Za-z\d=\s]+?>', '', raw_doc)
    cleaned = regex.sub(r'【.+?】', '', cleaned)
    cleaned = regex.sub(r'\n', '', cleaned)

    cleaned = _normalize(cleaned)

    return cleaned

def _normalize(s):
    """
    mecab-ipadic-neologd の正規化処理（一部修正）を適用する
    ref: https://github.com/neologd/mecab-ipadic-neologd/wiki/Regexp.ja
    
    Parameters
    ----------
    s : str
        raw text

    Returns
    -------
    str
        normalized text
    """

    s = s.strip()

    s = regex.sub('[˗֊‐‑‒–⁃⁻₋−]+', '-', s)  # normalize hyphens
    s = regex.sub('[﹣－ｰ—―─━ー]+', 'ー', s)  # normalize choonpus
    s = regex.sub('[~∼∾〜〰～]', '〜', s)  # normalize tildes

    s = _remove_extra_spaces(s)
    s = regex.sub('[’]', '\'', s)
    s = regex.sub('[”]', '"', s)

    s = mojimoji.han_to_zen(s, digit=False, ascii=False)
    s = mojimoji.zen_to_han(s, kana=False)
    s = s.lower()

    return s

def _remove_extra_spaces(s):
    s = regex.sub('[ 　]+', ' ', s)
    blocks = ''.join(('\u4E00-\u9FFF',  # CJK UNIFIED IDEOGRAPHS
                      '\u3040-\u309F',  # HIRAGANA
                      '\u30A0-\u30FF',  # KATAKANA
                      '\u3000-\u303F',  # CJK SYMBOLS AND PUNCTUATION
                      '\uFF00-\uFFEF'   # HALFWIDTH AND FULLWIDTH FORMS
                      ))
    basic_latin = '\u0000-\u007F'

    def remove_space_between(cls1, cls2, s):
        p = regex.compile('([{}]) ([{}])'.format(cls1, cls2))
        while p.search(s):
            s = p.sub(r'\1\2', s)
        return s

    s = remove_space_between(blocks, blocks, s)
    s = remove_space_between(blocks, basic_latin, s)
    s = remove_space_between(basic_latin, blocks, s)
    return s


def extract_content_from_NTCIR(doc, field):
    """
    NTCIRフォーマットの特許文書から指定したフィールドの内容を抽出する
    
    Parameters
    ----------
    raw_doc : str
        特許のテキストデータ

    field: {'ab', 'cl', 'de', 'es'}
        取得したいフィールドを指定する．
        'ab' -> 要約
        'cl' -> 特許請求の範囲
        'de' -> 発明の詳細な説明
        'es' -> 符号の説明

    Returns
    -------
    content : str
        指定したフィールドのテキストデータ
    """
    
    if field in ['ab', 'cl', 'de']:
        patt = fr'<SDO {field.upper()}J>([\S\s]+?)</SDO>'
    elif field == 'es':
        patt = fr'【符号の説明】([^(?:【.+?】)]+)'
    else:
        raise AttributeError("正しいフィールド名ではありません．")
        
    m = regex.search(patt, doc)
    if m:
        return m.group(1)
    else:
        return ""

    
def split_claims(raw_claim):
    """
    請求項ごとに分割してリストにする

    Parameters
    ----------
    raw_claim: str
        「特許請求の範囲」のテキスト

    Returns
    -------
    claims : list of str
        請求項のリスト
    """
    return regex.findall(r'【請求項\d+】([\S\s]+?)(?=【請求項\d+】|$)', raw_claim)
    
    
def extract_effect_section_paragraphs(text):
    m = regex.search(r'【発明の効果】([\s\S]+)', text)
    if not m:
        return []

    sec_text = m.group(1)
    paragraphs = split_paragraph(sec_text)
    for i, p in enumerate(paragraphs[1:], 1):
        if not is_paragraph_tag(p):
            return paragraphs[:i]
        
    return paragraphs


def split_paragraph(text):
    paragraphs = regex.findall(r'([\s\S]*?。\n)', text)
    paragraphs = [p.strip() for p in paragraphs]
    return paragraphs


def split_sentence(text):
    return [s.strip() for s in regex.findall(r'([\S\s]+?。)', text)]


def is_paragraph_tag(text):
    return regex.search(r'^【\d{4}】', text)