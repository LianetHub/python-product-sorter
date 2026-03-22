import glob
import logging
import os

import numpy as np
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

DATA_FOLDER = "data/"
OUTPUT_FILE = "merged_catalog.xlsx"

MAPPING = {
    "Изображение": ["Изображения"],
    "Название": ["Название"],
    "Артикул": ["Артикул"],
    "Цена": ["Цена", "РРЦ"],
    "Валюта": ["Валюта"],
    "Наличие": ["Наличие"],
    "Файлы": ["Файлы"],
    "URL": ["URL"],
    "Описание": ["Описание", "Краткое описание"],
    "Инвертор": ["Инвертор", "Инверторная технология", "Инверторный компрессор"],
    "Мощность в режиме охлаждения": [
        "Мощность в режиме охлаждения",
        "Холодопроизводительность (кВт)",
        "Номинальная холодопроизводительность, кВт",
        "Номинальная холодопроизводительность",
        "Охлаждение (кВт)",
        "Произв. холод, кВт",
        "Производительность холод , кВт",
        "Холодопроизводительность",
        "Охлаждение (Вт)",
        "Потребляемая мощность (охлаждение) , кВт",
        "Мощность охлаждения (кВт)",
    ],
    "Мощность в режиме обогрева": [
        "Мощность в режиме обогрева",
        "Потребляемая мощность (обогрев) , кВт",
    ],
    "Тип хладагента": ["Тип хладагента", "Марка фреона"],
    "Цвет": ["Цвет внутреннего блока", "Цвет прибора", "Цвет"],
    "Класс энергопотребления": [
        "Класс энергопотребления",
        "Класс энергоэффективности (охлаждение)",
        "Класс энергоэффективности EER (охлаждение)",
        "Класс энергетической эффективности",
    ],
    "Основные режимы (режим работы)": [
        "Режим работы",
        "Основные режимы",
        "Основные режимы (режим работы)",
        "Режимы работы",
    ],
    "Уровень шума": [
        "Уровень шума внутреннего блока, дБ(А)",
        "Уровень шума внутреннего блока",
        "Уровень звукового давления дБ(А)",
        "Мин. уровень шума , дБ(А)",
    ],
    "Максимальная длина коммуникаций": [
        "Максимальная длина коммуникаций",
        "Максимальная длина трассы",
        "Max.длина магистрали , м",
        "Длина трассы, м",
        "Максимальная длина труб, м",
    ],
    "Тип внутреннего блока": ["Тип внутреннего блока", "Тип блока", "Тип прибора"],
}

CATEGORY_NORMALIZATION = {
    "сплит системы": "Сплит-системы",
    "сплит-системы": "Сплит-системы",
    "бытовые сплит-системы": "Сплит-системы",
    "бытовые сплит-системы mdv для дома и офиса": "Сплит-системы",
    "мульти-сплиты": "Мульти-сплит-системы",
    "мульти-сплит-системы": "Мульти-сплит-системы",
    "мульти сплит-системы": "Мульти-сплит-системы",
    "мультисплит-системы mdv": "Мульти-сплит-системы",
    "полупромышленные": "Полупромышленные системы",
    "полупромышленные сплит-системы": "Полупромышленные системы",
    "полупромышленные сплит-системы mdv": "Полупромышленные системы",
    "мультизональные": "VRF-системы",
    "мультизональные системы": "VRF-системы",
    "vrf-системы mdv (мультизональные)": "VRF-системы",
    "mini vrf-системы mdv серия atom": "VRF-системы",
    "вентиляция": "Вентиляция",
    "мобильные кондиционеры": "Мобильные кондиционеры",
    "аксессуары для сплит-систем": "Аксессуары",
    "аксессуары": "Аксессуары",
}

FILTER_KEYS = [
    "Дополнительные фильтры тонкой очистки в комплекте",
    "Фильтра",
    "Воздушный фильтр",
]

YES_VALUES = {"да", "+", "yes", "true", "1", "есть"}


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


def load_data(folder):
    all_files = glob.glob(os.path.join(folder, "*.xlsx"))
    files = [f for f in all_files if not os.path.basename(f).startswith("~$")]
    if not files:
        logging.error(f"Excel files not found in: {folder}")
        return None
    logging.info(f"Files found: {len(files)}")
    dataframes = []
    for file in files:
        try:
            df = pd.read_excel(file)
            df.columns = df.columns.astype(str).str.strip()
            brand = get_brand_from_filename(file)
            df["_source_brand"] = brand
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            df = df.replace(r"^\s*$", np.nan, regex=True)
            logging.info(f"Loaded: {file} | Brand: {brand}")
            dataframes.append(df)
        except Exception as e:
            logging.error(f"Error loading {file}: {e}")
    return (
        pd.concat(dataframes, axis=0, ignore_index=True, sort=False)
        if dataframes
        else None
    )


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


def process_catalog():
    raw_df = load_data(DATA_FOLDER)
    if raw_df is None:
        return

    temp_df = pd.DataFrame(index=raw_df.index)
    current_cols = raw_df.columns.tolist()

    if "Артикул" in current_cols:
        temp_df["Артикул"] = raw_df["Артикул"]

    for target, sources in MAPPING.items():
        temp_df[target] = np.nan
        for s in sources:
            if s in current_cols:
                temp_df[target] = temp_df[target].fillna(raw_df[s])

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

    temp_df["Фильтры тонкой очистки воздуха"] = raw_df_filtered.apply(
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
