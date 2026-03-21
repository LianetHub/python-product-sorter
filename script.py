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
    "URL": [
        "URL",
        "Ссылка",
        "Сайт"
    ],

    "Изображение": [
        "Изображения", 
        "Файлы"
    ],

    "Название": [   
        "Название", 
    ],
    
    "Наличие": [
        "Наличие",
        "В наличии",
        "Доступность"
    ],

    "Производитель": [
        "Производитель",
        "Бренд"
    ],
    
    "Цена": [
        "Цена", 
        "Розничная цена", 
        "Цена со скидкой", 
        "Стоимость", 
        "Розничная цена",
        "Price", 
        "РРЦ"
    ],
    
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
        "Мощность охлаждения (кВт)"
    ],

    "Мощность в режиме обогрева": [
        "Мощность в режиме обогрева",
        "Потребляемая мощность (обогрев) , кВт"
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
        "Основные режимы",
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
        "Максимальная длина коммуникаций",
        "Максимальная длина трассы", 
        "Max.длина магистрали , м", 
        "Длина трассы, м", 
        "Максимальная длина труб, м"
    ],

    "Тип внутреннего блока": [
        "Тип внутреннего блока",
        "Тип блока",    
        "Тип прибора"
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
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            df = df.replace(r'^\s*$', np.nan, regex=True)
            logging.info(f"Loaded: {file} ({len(df)} rows)")
            dataframes.append(df)
        except Exception as e:
            logging.error(f"Error loading {file}: {e}")
            
    return pd.concat(dataframes, axis=0, ignore_index=True, sort=False) if dataframes else None

def extract_filters(row, source_columns):
    active_filters = []
    
    for key in FILTER_KEYS:
        if key in row.index and pd.notna(row[key]):
            active_filters.append(str(row[key]))
            
    boolean_cols = [c for c in source_columns if "фильтр тонкой очистки" in str(c).lower() and c not in FILTER_KEYS]
    
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

    logging.info("Building unified catalog...")
    temp_df = pd.DataFrame(index=raw_df.index)
    current_cols = raw_df.columns.tolist()

    if "Артикул" in current_cols:
        temp_df["Артикул"] = raw_df["Артикул"]
    
    for target, sources in MAPPING.items():
        temp_df[target] = np.nan
        for s in sources:
            if s in current_cols:
                temp_df[target] = temp_df[target].fillna(raw_df[s])
        
    logging.info("Filtering by availability...")
    if "Наличие" in temp_df.columns:
        valid_rows = temp_df["Наличие"].astype(str).str.lower().isin(YES_VALUES)
        temp_df = temp_df[valid_rows].copy()
        raw_df_filtered = raw_df.loc[temp_df.index]
        logging.info(f"Rows after filtering: {len(temp_df)}")
    else:
        logging.warning("Column 'Наличие' not found in mapping, skipping filter.")
        raw_df_filtered = raw_df

    logging.info("Processing air filters...")
    temp_df["Фильтры тонкой очистки воздуха"] = raw_df_filtered.apply(
        extract_filters, axis=1, source_columns=current_cols
    )

    final_df = temp_df.copy()
    
    cols = list(final_df.columns)
    if "URL" in cols:
        cols.insert(0, cols.pop(cols.index("URL")))
        final_df = final_df[cols]

    logging.info("Sorting by Manufacturer...")
    if "Производитель" in final_df.columns:
        final_df.sort_values(by="Производитель", inplace=True, na_position='last')

    try:
        final_df.to_excel(OUTPUT_FILE, index=False)
        logging.info(f"Success! Saved to {OUTPUT_FILE} | Total items: {len(final_df)}")
    except PermissionError:
        logging.error(f"Could not save! Close '{OUTPUT_FILE}' and try again.")
    except Exception as e:
        logging.error(f"Error during save: {e}")

if __name__ == "__main__":
    process_catalog()