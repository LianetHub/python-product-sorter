import logging

import numpy as np
import pandas as pd

from config import CATEGORY_NORMALIZATION, DATA_FOLDER, MAPPING, OUTPUT_FILE, YES_VALUES
from loader import load_data
from utils import extract_filters, normalize_power, normalize_refrigerant


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)


def process_catalog():
    raw_df = load_data(DATA_FOLDER)
    if raw_df is None:
        return

    raw_df = raw_df.copy()

    temp_df = pd.DataFrame(index=raw_df.index)
    current_cols = raw_df.columns.tolist()

    if "Артикул" in current_cols:
        temp_df["Артикул"] = raw_df["Артикул"]

    for target, sources in MAPPING.items():
        temp_df[target] = np.nan
        for s in sources:
            if s in current_cols:
                values = raw_df[s]

                is_numeric_target = any(
                    word in target.lower()
                    for word in ["мощность", "охлаждение", "хладагента"]
                )
                is_class_target = "класс" in target.lower()

                if is_numeric_target and not is_class_target:
                    values = values.apply(normalize_power)
                elif "хладагента (кг)" in target.lower():
                    values = values.apply(normalize_refrigerant)

                temp_df[target] = temp_df[target].fillna(values)

    temp_df["Производитель"] = np.nan
    for s in ["Производитель", "Бренд"]:
        if s in current_cols:
            temp_df["Производитель"] = temp_df["Производитель"].fillna(raw_df[s])

    mask_override = raw_df["_source_brand"].isin(["Haier", "MDV"])
    temp_df.loc[mask_override, "Производитель"] = raw_df.loc[
        mask_override, "_source_brand"
    ]
    temp_df["Производитель"] = temp_df["Производитель"].fillna(raw_df["_source_brand"])

    temp_df["Категория"] = ""
    temp_df["Категория"] = temp_df["Категория"].astype(object)

    for idx, row in raw_df.iterrows():
        brand = row["_source_brand"]
        cat_val = str(row.get("Категория", "")).strip()
        cat_low = cat_val.lower()
        subcat_val = str(row.get("Подкатегория", "")).strip()

        final_category = ""
        if brand in ["Hiconix", "Haier", "MDV"]:
            final_category = cat_val
        elif brand == "Breez":
            if cat_low == "кондиционирование":
                final_category = subcat_val
            elif cat_low == "микроклимат/ plug&play":
                final_category = "Аксессуары"
            else:
                final_category = subcat_val
        elif brand == "Vesna":
            final_category = "Сплит-системы"

        temp_df.at[idx, "Категория"] = final_category

    temp_df["Категория"] = temp_df["Категория"].astype(str).str.strip().str.lower()
    temp_df["Категория"] = temp_df["Категория"].replace(CATEGORY_NORMALIZATION)
    temp_df.loc[temp_df["Категория"].isin(["nan", ""]), "Категория"] = np.nan

    if "Наличие" in temp_df.columns:
        valid_rows = temp_df["Наличие"].astype(str).str.lower().isin(YES_VALUES)
        temp_df = temp_df[valid_rows].copy()
        raw_df_filtered = raw_df.loc[temp_df.index]
    else:
        raw_df_filtered = raw_df

    if "Название" in temp_df.columns:
        stop_words = ["пульт", "фильтр", "панель", "wi-fi", "адаптер"]
        pattern = "|".join(stop_words)
        is_stop_word = (
            temp_df["Название"].astype(str).str.contains(pattern, case=False, na=False)
        )
        is_accessory_cat = temp_df["Категория"] == "Аксессуары"
        mask_to_remove = is_stop_word & (~is_accessory_cat)
        temp_df = temp_df[~mask_to_remove].copy()
        raw_df_filtered = raw_df_filtered.loc[temp_df.index]

    temp_df["Наличие фильтров"] = raw_df_filtered.apply(
        extract_filters, axis=1, source_columns=current_cols
    )

    final_df = temp_df.copy()
    cols = list(final_df.columns)
    if "URL" in cols:
        cols.insert(0, cols.pop(cols.index("URL")))
        final_df = final_df[cols]

    if "Производитель" in final_df.columns:
        final_df.sort_values(
            by=["Производитель", "Категория"], inplace=True, na_position="last"
        )

    try:
        final_df.to_excel(OUTPUT_FILE, index=False)
        logging.info(f"Success! Saved to {OUTPUT_FILE} | Items: {len(final_df)}")
    except Exception as e:
        logging.error(f"Error: {e}")


if __name__ == "__main__":
    process_catalog()
