import ipytest
from hypothesis import given
from hypothesis.strategies import text


def encode(input_string):
    count = 1
    prev = ""
    lst = []
    if not input_string:
        return []
    for character in input_string:
        if character != prev:
            if prev:
                entry = (prev, count)
                lst.append(entry)
            count = 1
            prev = character
        else:
            count += 1
    entry = (character, count)
    lst.append(entry)
    return lst


def decode(lst):
    q = ""
    for character, count in lst:
        q += character * count
    return q


@given(text())
def test_decode_inverts_encode(s):
    print(s)
    assert decode(encode(s)) == s  # inverse property test


ipytest.run("-s")
