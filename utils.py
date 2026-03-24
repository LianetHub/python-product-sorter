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
            active_filters.append(str(row[key]))
    boolean_cols = [
        c
        for c in source_columns
        if "фильтр тонкой очистки" in str(c).lower() and c not in FILTER_KEYS
    ]
    for col in boolean_cols:
        val = str(row[col]).lower()
        if val in YES_VALUES:
            name = str(col).replace("Дополнительный фильтр тонкой очистки ", "")
            active_filters.append(name)
    return ", ".join(active_filters) if active_filters else np.nan
