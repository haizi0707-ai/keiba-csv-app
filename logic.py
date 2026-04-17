import pandas as pd

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    column_map = {
        "日付": "date",
        "場名": "venue",
        "レース": "race_name",
        "R": "race_number",
        "馬番": "horse_number",
        "馬名": "horse_name",
        "騎手": "jockey",
        "調教師": "trainer",
    }

    existing_map = {k: v for k, v in column_map.items() if k in df.columns}
    df = df.rename(columns=existing_map)

    return df

def apply_user_logic(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["category"] = "相手候補"
    df["trust"] = "C"
    df["score"] = 70
    df["comment"] = "仮判定"
    df["finishPosition"] = ""

    if "horse_number" in df.columns:
        df["score"] = 80 - pd.to_numeric(df["horse_number"], errors="coerce").fillna(99)

    df.loc[df["score"] >= 78, "category"] = "本命候補"
    df.loc[df["score"] >= 78, "trust"] = "A"
    df.loc[(df["score"] >= 74) & (df["score"] < 78), "category"] = "相手本線"
    df.loc[(df["score"] >= 74) & (df["score"] < 78), "trust"] = "B"
    df.loc[(df["score"] < 74), "category"] = "強穴"
    df.loc[(df["score"] < 74), "trust"] = "C"

    df["comment"] = (
        "score=" + df["score"].astype(str) +
        " / 今後ここに直線ロジック・展開ロジックを実装"
    )

    output_cols = [
        "date", "venue", "race_name", "race_number",
        "horse_number", "horse_name", "jockey", "trainer",
        "category", "trust", "score", "comment", "finishPosition"
    ]

    for col in output_cols:
        if col not in df.columns:
            df[col] = ""

    df = df[output_cols]
    return df

def process_target_csv(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)
    df = apply_user_logic(df)
    return df
