import glob
import logging
import os

import numpy as np
import pandas as pd

from utils import get_brand_from_filename


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
            df = df.copy()
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
