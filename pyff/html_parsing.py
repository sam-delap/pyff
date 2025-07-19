"""
Common HTML parsing functions used to parse ProFootballReference data with baked-in, documented assumptions.
"""

from bs4 import Tag
from typing import Any


def fetch_specific_sub_tag(source_doc: Tag, sub_tag_type: str, id: str) -> Tag:
    """Find a lower-level tag with a specific ID in an existing HTML doc."""
    sub_tag = source_doc.find(sub_tag_type, id=id)
    assert type(sub_tag) == Tag
    return sub_tag


def fetch_sub_tag(source_doc: Tag, sub_tag_type: str) -> Tag:
    """Find a lower-level tag in an existing HTML doc."""
    sub_tag = source_doc.find(sub_tag_type)
    assert type(sub_tag) == Tag
    return sub_tag


def fetch_data_stat(
    row: Tag,
    stat_identifier: str,
    stat_html_attribute: str,
    stat_default_value: Any = "",
    stat_dtype: type = str,
    return_html: bool = False,
):
    """Find value for specific stat based on a given attribute from a table row"""
    stat_html = row.find(attrs={"data-stat": stat_html_attribute})
    if stat_html is None:
        print(row)
        raise ValueError(
            f"Couldn't find value for {stat_identifier} using data-stat {stat_html_attribute}. Check HTML."
        )
    assert type(stat_html) == Tag
    if return_html:
        return stat_html

    stat_value = stat_html.get_text()

    if stat_default_value != "" and stat_value is None:
        # Not doing typecasting here to support default value of "NA" for all fields
        return stat_default_value

    return stat_dtype(stat_value)
