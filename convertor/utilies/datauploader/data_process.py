import pandas as pd


def file_to_json(file, keyword, decimal, nrows):

    if keyword == "excel":
        df = pd.read_excel(file, decimal=decimal, nrows=nrows, dtype=str)
    elif keyword == "csv":
        df = pd.read_csv(file)

    elif keyword == "json":
        df = pd.read_json(file)

    df = df.set_index("in_"+df.index.astype(str))

    df.columns = df.columns.str.strip()

    result = df.to_json(orient="columns")

    return result


if __name__ == "__main__":
    file = r"C:\Users\ychen2\Desktop\test.xlsx"
    file_to_json(file, "excel")
    print('end')
