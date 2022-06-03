import pandas as pd
import numpy as np
from io import StringIO

'''
function to turn iput file into JSON format.
Input file is excel or csv or json.

'''


def file_to_json(file, keyword, decimal, nrows, skip_rows, sep="none"):

    if keyword == "excel":
        df = pd.read_excel(file, decimal=decimal, nrows=nrows,
                           dtype="string", skiprows=skip_rows)
    elif keyword == "csv":
        df = pd.read_csv(file, decimal=decimal, nrows=nrows,
                         dtype="string", sep=sep, encoding_errors="replace", index_col=False, skiprows=skip_rows)
    elif keyword == "json":
        df = pd.read_json(file)

    df = df.set_index("in_"+df.index.astype(str))

    df.columns = df.columns.astype(str).str.strip()
    df = df.applymap(lambda x: x.strip(),
                     na_action="ignore")
    df = df.fillna(np.nan)
    df = df.replace("", np.nan)

    df = df.dropna(axis=0, how="all")
    df = df.dropna(axis=1, how="all")
    assert not df.empty, "The file contains no values"

    result = df.to_json(orient="columns")

    return result
