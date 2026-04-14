import re
from typing import Optional

def strip_all_whitespace(text: str) -> str:
    return re.sub(r"\s+", "", text)

def map_stripped_index_to_raw(raw_text: str, stripped_index: int) -> Optional[int]:
    stripped_pos = 0
    for raw_pos, ch in enumerate(raw_text):
        if stripped_pos == stripped_index:
            return raw_pos
        if not re.match(r"\s", ch):
            stripped_pos += 1
            
    if stripped_pos == stripped_index:
        return len(raw_text)
    return None

def test_mapper():
    raw_text = "MenuClose\nToday  "
    original = "Menu Close Today"
    
    norm_raw = strip_all_whitespace(raw_text)
    norm_orig = strip_all_whitespace(original)
    
    print(f"Norm Raw: '{norm_raw}'")
    print(f"Norm Orig: '{norm_orig}'")
    
    start = norm_raw.find(norm_orig)
    print(f"Found at: {start}")
    
    if start >= 0:
        raw_start = map_stripped_index_to_raw(raw_text, start)
        raw_end = map_stripped_index_to_raw(raw_text, start + len(norm_orig))
        print(f"Raw indices: {raw_start} to {raw_end}")
        print(f"Extracted from raw: '{raw_text[raw_start:raw_end]}'")

test_mapper()
