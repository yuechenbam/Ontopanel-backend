
import re
import logging
from .shapes_notes import *
from urllib.parse import urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

''' 
help functions
'''


def clean_html_tags(text):

    html_tags = ["<u>", "</u>", "<b>", "</b>",
                 "(<span .[^>]+\>)", "(<font .[^>]+\>)", "</font>", "<span>", "</span>"]
    for tag in html_tags:
        text = re.sub(tag, "", text)

    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text("|", strip=True)
    return text


def seperate_string(text):
    assert len(text.split(
        ':', 1)) == 2, f"Shape text '{text}' formed not correctly. Use 'prefix:name' to form it."
    text_pre, text_name = text.split(':', 1)
    text_pre = text_pre.strip().lower()
    text_name = text_name.strip()
    return text_pre, text_name


def seperate_string_pattern(text):
    # match all patterns
    # (all) ns:objectProperty <<owl:someValuesFrom>>ns:objectProperty
    text = text.strip()
    pattern = '(<<|\()(.*)(>>|\))'
    groups = re.search(pattern, text)
    if groups:
        matched_text = groups.group()
        res = groups.group(2)

        rest_text = text.replace(matched_text, '').strip().strip('|')
    else:
        res = ''
        rest_text = text.strip().strip('|')

    return res, rest_text


def get_corners(geometry):
    x = geometry["x"]
    y = geometry["y"]
    width = geometry["width"]
    height = geometry["height"]

    p1 = (x, y)
    p2 = (x, y+height)
    p3 = (x+width, y)
    p4 = (x+width, y+height)

    return p1, p2, p3, p4


def compare_geo(geometry1, geometry2):

    geo1_p1, geo1_p2, geo1_p3, geo1_p4 = get_corners(geometry1)
    geo2_p1, geo2_p2, geo2_p3, geo2_p4 = get_corners(geometry2)
    # geo2 should be above geo1
    # but in graph, it is reversed, so the value should be lower.
    # but they could have some overlap or distance
    stacked = False

    if geo1_p2[1] > geo2_p2[1]:
        # geo1 bottom left x and geo2 upper left x
        dx = abs(geo1_p1[0] - geo2_p2[0])
        # geo1 bottom left y and geo2 upper left y
        dy = abs(geo1_p1[1] - geo2_p2[1])

        if dx < 1 and dy < 1:
            stacked = True

    return stacked


def onRule_checker(sub, predica, obj):
    # use the rule from shape_notes.py
    inputs = sub + '+' + predica
    try:
        output = sum_rules[inputs]

        if output == obj or obj in output:

            return True
    except:
        return False


def value_checker(datatype, value, name):
    try:
        if datatype.lower() == 'int':
            re_value = int(value)
        elif datatype.lower() == 'float':
            re_value = float(value)
        elif datatype.lower() == 'boolean':
            re_value = bool(value)
        else:
            re_value = value
    except ValueError:
        logger.warning(
            f'In datatype shape "{name}": the value and the datatype do not match.')
        return None
    else:
        return re_value


# the function used to decide the IRI
'''
1. if in the shape-daten,  no data, it means, the shape is
newly created by user, so use the text shape
2. if with data, it is draged and dropped from the imported ontology,
so use the data from shape-daten
3. the data varaiables are
EntityName, BelongsTo, RDFLabel, IRI, MappingID
4. BelongsTo is not taken, always use the shape master(for the reason of shapes like 'someop')
4. if MappingID variable is here, then this shape has more data for mapping.
5. only shapes individual, bnode, datatype can have mapping, the rest will be ignored.
'''


def uri_validator(x):
    invalid_uri_chars = '<>" {}|\\^`'
    try:
        for c in invalid_uri_chars:
            if c in x:
                return False

        result = urlparse(x)
        return all([result.scheme, result.netloc, result.path])
    except:
        return False
