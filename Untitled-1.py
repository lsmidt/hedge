from textblob import TextBlob
import re
from fuzzywuzzy import fuzz


def string_word_ratio(a_string, b_list):
    """
    RETURN max ratio of word match in substring of b_string
    """
    a_string = a_string.lower()
    max_ratio = 0
    for b_word in b_list:
        b_word = b_word.lower()
        if b_word in a_string:
            max_ratio = 100
            break
        ratio = fuzz.token_sort_ratio(b_word, a_string)
        max_ratio = max(ratio, max_ratio)
    return max_ratio

print (string_word_ratio("iPhone", ["phone"])) 