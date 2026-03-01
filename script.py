import pandas as pd
import glob
import numpy as np
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

DATA_FOLDER = "data/"
OUTPUT_FILE = "merged_catalog.xlsx"

MAPPING = {
    "Производитель": [
        "Бренд", 
        "Производитель", 
        "Заводская маркировка"
    ],
    
    "Цена": [
        "Цена", 
        "Розничная цена", 
        "Цена со скидкой", 
        "Стоимость", 
        "Price", 
        "РРЦ"
    ],
    
    "Мощность в режиме охлаждения": [
        "Холодопроизводительность (кВт)", 
        "Номинальная холодопроизводительность, кВт", 
        "Номинальная холодопроизводительность", 
        "Охлаждение (кВт)", 
        "Произв. холод, кВт", 
        "Производительность холод , кВт", 
        "Холодопроизводительность", 
        "Охлаждение (Вт)"
    ],
    
    "Тип хладагента": [
        "Тип хладагента", 
        "Марка фреона"
    ],
    
    "Цвет": [
        "Цвет внутреннего блока", 
        "Цвет прибора", 
        "Цвет"
    ],
    
    "Класс энергопотребления": [
        "Класс энергопотребления", 
        "Класс энергоэффективности (охлаждение)", 
        "Класс энергоэффективности EER (охлаждение)", 
        "Класс энергетической эффективности"
    ],
    
    "Инвертор/Тип компрессора": [
        "Инверторная технология", 
        "Тип компрессора", 
        "Инвертор", 
        "Инверторный компрессор", 
        "Тип управления компрессором"
    ],
    
    "Основные режимы (режим работы)": [
        "Режим работы", 
        "Основные режимы (режим работы)", 
        "Режимы работы"
    ],
    
    "Уровень шума": [
        "Уровень шума внутреннего блока, дБ(А)", 
        "Уровень шума внутреннего блока", 
        "Уровень звукового давления дБ(А)", 
        "Мин. уровень шума , дБ(А)"
    ],
    
    "Максимальная длина коммуникаций": [
        "Максимальная длина трассы", 
        "Max.длина магистрали , м", 
        "Длина трассы, м", 
        "Максимальная длина труб, м"
    ],
    
    "Модель": [
        "Название", 
        "Модель", 
        "Модель внутреннего блока"
    ],
    
    "Изображение": [
        "Изображения", 
        "Файлы"
    ],
    
    "URL": [
        "URL",
        "Ссылка",
        "Сайт"
    ]
}

FILTER_KEYS = [
    "Дополнительные фильтры тонкой очистки в комплекте", 
    "Фильтра", 
    "Воздушный фильтр"
]

YES_VALUES = {'да', '+', 'yes', 'true', '1', 'есть'}

def load_data(folder):
    files = glob.glob(os.path.join(folder, "*.xlsx"))
    if not files:
        logging.error(f"Excel files not found in: {folder}")
        return None
    
    logging.info(f"Files found: {len(files)}")
    dataframes = []
    
    for file in files:
        try:
            df = pd.read_excel(file)
            df.columns = df.columns.astype(str).str.strip()
            logging.info(f"Loaded: {file} ({len(df)} rows)")
            dataframes.append(df)
        except Exception as e:
            logging.error(f"Error loading {file}: {e}")
            
    return pd.concat(dataframes, axis=0, ignore_index=True) if dataframes else None

def extract_filters(row, source_columns):
    active_filters = []
    
    for key in FILTER_KEYS:
        if key in row.index and pd.notna(row[key]) and str(row[key]).strip():
            active_filters.append(str(row[key]))
            
    boolean_cols = [c for c in source_columns if "фильтр тонкой очистки" in c.lower() and c not in FILTER_KEYS]
    
    for col in boolean_cols:
        val = str(row[col]).strip().lower()
        if val in YES_VALUES:
            name = col.replace("Дополнительный фильтр тонкой очистки ", "")
            active_filters.append(name)
            
    return ", ".join(active_filters) if active_filters else np.nan

def process_catalog():
    raw_df = load_data(DATA_FOLDER)
    if raw_df is None:
        return

    logging.info("Building unified catalog...")
    temp_df = pd.DataFrame()
    current_cols = raw_df.columns.tolist()

    if "Артикул" in current_cols:
        temp_df["Артикул"] = raw_df["Артикул"]
    else:
        logging.error("Column 'Артикул' not found! Duplicates cannot be merged correctly.")
        return

    for target, sources in MAPPING.items():
        match = next((s for s in sources if s in current_cols), None)
        if match:
            temp_df[target] = raw_df[match]
            logging.info(f"Mapped: {target} <- {match}")
        else:
            temp_df[target] = np.nan
            logging.warning(f"Field not found: {target}")

    logging.info("Processing air filters...")
    temp_df["Фильтры тонкой очистки воздуха"] = raw_df.apply(extract_filters, axis=1, source_columns=current_cols)

    logging.info("Merging duplicates and filling gaps...")
    final_df = temp_df.groupby("Артикул", as_index=False).agg(
        lambda x: x.dropna().iloc[0] if not x.dropna().empty else np.nan
    )
    
    cols = list(final_df.columns)
    if "URL" in cols:
        cols.insert(0, cols.pop(cols.index("URL")))
        final_df = final_df[cols]

    logging.info("Sorting by Manufacturer...")
    if "Производитель" in final_df.columns:
        final_df.sort_values(by="Производитель", inplace=True, na_position='last')

    try:
        final_df.to_excel(OUTPUT_FILE, index=False)
        logging.info(f"Success! Saved to {OUTPUT_FILE} | Total unique items: {len(final_df)}")
    except PermissionError:
        logging.error(f"Could not save! Close '{OUTPUT_FILE}' and try again.")
    except Exception as e:
        logging.error(f"Error during save: {e}")

if __name__ == "__main__":
    process_catalog()