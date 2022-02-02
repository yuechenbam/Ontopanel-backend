import pandas as pd


def process_data(file, keyword):
    if keyword == "excel":
        df = pd.read_excel(file)
    elif keyword == "csv":
        df = pd.read_csv(file)

    elif keyword == "json":
        df = pd.read_json(file)

    result = df.to_json(orient="columns")

    return result


if __name__ == "__main__":
    file = r"C:\Users\ychen2\Desktop\test.xlsx"
    process_data(file, "excel")
    print('end')
