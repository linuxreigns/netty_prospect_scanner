import pandas as pd


def export_xlsx(df: pd.DataFrame, output_path: str) -> str:
    df.to_excel(output_path, index=False)
    return output_path
