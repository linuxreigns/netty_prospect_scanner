import pandas as pd


def export_csv(df: pd.DataFrame, output_path: str) -> str:
    df.to_csv(output_path, index=False)
    return output_path
