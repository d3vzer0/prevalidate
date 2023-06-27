from enum import Enum
from pydantic import BaseModel


class Functions(Enum):
    """Different functions allowed in a DCR
    which only supports a subset of KQL

    Args:
        Enum (_type_): _description_
    """
    BITWISE = [
        "binary_and",
        "binary_or",
        "binary_not",
        "binary_shift_left",
        "binary_shift_right",
        "binary_xor",
    ]
    CONDITIONAL = [
        "case",
        "iif",
        "max_of",
        "min_of"
    ]
    CONVERSION = [
        "tobool",
        "todatetime",
        "todouble/toreal",
        "toguid",
        "toint",
        "tolong",
        "tostring",
        "totimespan",
    ]
    DATETIME = [
        "ago",
        "datetime_add",
        "datetime_diff",
        "datetime_part",
        "dayofmonth",
        "dayofweek",
        "dayofyear",
        "endofday",
        "endofmonth",
        "endofweek",
        "endofyear",
        "getmonth",
        "getyear",
        "hourofday",
        "make_datetime",
        "make_timespan",
        "now",
        "startofday",
        "startofmonth",
        "startofweek",
        "startofyear",
        "todatetime",
        "totimespan",
        "weekofyear",
    ]
    DYNAMIC = [
        "array_concat",
        "array_length",
        "pack_array",
        "pack",
        "parse_json",
        "parse_xml",
        "zip"
    ]
    STRING = [
        "base64_encodestring",
        "base64_decodestring",
        "countof",
        "extract",
        "extract_all",
        "indexof",
        "isempty",
        "isnotempty",
        "parse_json",
        "replace",
        "split",
        "strcat",
        "strcat_delim",
        "strlen",
        "substring",
        "tolower",
        "toupper",
        "hash_sha256",
    ]
    TYPE = [
        "gettype"
        "isnotnull"
        "isnull"
    ]


class TabularOperators(Enum):
    """Different types of allowed operators for DCR
    which only supports a subset of KQL

    Args:
        Enum (_type_): _description_
    """
    TABULAR = [
        'extend',
        'project',
        'print',
        'where',
        'parse',
        'project-away',
        'project-rename',
        'datatable',
        'columnifexists'
    ]


class ScalarOperators(Enum):
    MATH = [
        # "abs",
        "bin/floor",
        "ceiling",
        "exp",
        "exp10",
        "exp2",
        "isfinite",
        "isinf",
        "isnan",
        "log",
        "log10",
        "log2",
        "pow",
        "round",
        "sign"
    ]

    NUMERIC = [
        "+",
        "-",
        "*",
        "/",
        "%",
        "<",
        ">",
        "==",
        "!=",
        "<=",
        ">=",
        "in",
        "!in",
    ]
    STRING = [
        "==",
        "!=",
        "=~",
        "!~",
        "contains",
        "!contains",
        "contains_cs",
        "!contains_cs",
        "has",
        "!has",
        "has_cs",
        "!has_cs",
        "startswith",
        "!startswith",
        "startswith_cs",
        "!startswith_cs",
        "endswith",
        "!endswith",
        "endswith_cs",
        "!endswith_cs",
        "matchesregex",
        "in",
        "!in"
    ]
    BITWISE = [
        "binary_and()",
        "binary_or()",
        "binary_xor()",
        "binary_not()",
        "binary_shift_left()",
        "binary_shift_right()"
    ]


class DCR(BaseModel):
    query: str
