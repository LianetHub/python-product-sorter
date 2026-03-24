import re

import numpy as np
import pandas as pd

from config import FILTER_KEYS, YES_VALUES


def get_brand_from_filename(filename):
    fname = filename.lower()
    if "breez" in fname:
        return "Breez"
    if "hiconix" in fname:
        return "Hiconix"
    if "haier" in fname:
        return "Haier"
    if "mdv" in fname:
        return "MDV"
    if "vesna" in fname:
        return "Vesna"
    return "Unknown"


def normalize_power(value):
    if pd.isna(value):
        return np.nan
    s_val = str(value).lower().replace(",", ".").strip()
    match = re.search(r"(\d+\.?\d*)", s_val)
    if not match:
        return np.nan
    num = float(match.group(1))
    if "вт" in s_val or (num > 100 and "квт" not in s_val):
        num = num / 1000
    return round(num, 3)


def normalize_refrigerant(value):
    if pd.isna(value):
        return np.nan
    s_val = str(value).lower().replace(",", ".").strip()
    match = re.search(r"(\d+\.?\d*)", s_val)
    if not match:
        return np.nan
    num = float(match.group(1))
    if "г" in s_val or num > 50:
        num = num / 1000
    return round(num, 3)


def extract_filters(row, source_columns):
    active_filters = []

    for key in FILTER_KEYS:
        if key in row.index and pd.notna(row[key]):
            val = str(row[key]).strip()
            if val.lower() not in ["нет", "0", "-", "nan", "none"]:
                active_filters.append(val)

    check_markers = [
        "Дополнительный фильтр",
        "Противопылевой фильтр",
        "Фильтры для воды",
    ]

    boolean_cols = [
        c
        for c in source_columns
        if any(marker in str(c) for marker in check_markers) and c not in FILTER_KEYS
    ]

    for col in boolean_cols:
        val = str(row[col]).lower().strip()
        if val in YES_VALUES:
            name = str(col).replace("Дополнительный фильтр тонкой очистки ", "")
            name = name.replace(" в комплекте", "")
            active_filters.append(name.strip())

    unique_filters = []
    for f in active_filters:
        if f not in unique_filters:
            unique_filters.append(f)

    return ", ".join(unique_filters) if unique_filters else np.nan
