from __future__ import annotations

import pandas as pd

REQUIRED_FINAL_COLUMNS = [
    "raceDate",
    "racecourse",
    "raceNo",
    "raceClass",
    "surface",
    "distance",
    "horseCount",
    "horseName",
    "category",
    "trust",
    "finishPosition",
    "comment",
]


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().replace("\u3000", " ") for c in out.columns]
    return out


def detect_input_type(df: pd.DataFrame) -> str:
    cols = set(_clean_columns(df).columns)

    if {"raceDate", "racecourse", "raceNo", "horseName"}.issubset(cols):
        return "final_csv"

    target_like = {"日付", "場名", "レース", "R", "馬番", "馬名"}
    completed_like = {"年", "月", "日", "場所", "レース番号", "略レース名", "芝ダ", "距離", "頭数", "馬名"}

    if len(target_like & cols) >= 4 or len(completed_like & cols) >= 6:
        return "target_raw"

    return "unknown"


def _to_text(v) -> str:
    if pd.isna(v):
        return ""
    s = str(v).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s


def _pick_series(df: pd.DataFrame, names: list[str], default="") -> pd.Series:
    for n in names:
        if n in df.columns:
            return df[n]
    return pd.Series([default] * len(df), index=df.index)


def _normalize_final_csv(df: pd.DataFrame) -> pd.DataFrame:
    df = _clean_columns(df).copy()
    alias_map = {
        "date": "raceDate",
        "venue": "racecourse",
        "race_number": "raceNo",
        "race_name": "raceClass",
        "horse_name": "horseName",
        "finishPosition": "finishPosition",
        "categoryCandidate": "category",
        "trustCandidate": "trust",
        "comment": "comment",
    }
    for old, new in alias_map.items():
        if old in df.columns and new not in df.columns:
            df[new] = df[old]

    for c in REQUIRED_FINAL_COLUMNS:
        if c not in df.columns:
            df[c] = ""

    out = df[REQUIRED_FINAL_COLUMNS].copy()
    out = out.fillna("")
    return out


def _category_and_trust(score: pd.Series) -> tuple[pd.Series, pd.Series]:
    category = pd.Series("穴候補", index=score.index)
    trust = pd.Series("D", index=score.index)

    category = category.mask(score >= 78, "本命候補")
    trust = trust.mask(score >= 78, "A")

    category = category.mask((score >= 74) & (score < 78), "相手本線")
    trust = trust.mask((score >= 74) & (score < 78), "B")

    category = category.mask((score >= 68) & (score < 74), "強穴")
    trust = trust.mask((score >= 68) & (score < 74), "C")

    return category, trust


def _normalize_target_raw(df: pd.DataFrame) -> pd.DataFrame:
    df = _clean_columns(df).copy()

    # 2 patterns supported:
    # 1) TARGET raw export: 日付/場名/レース/R/馬番/馬名...
    # 2) Completed race result export: 年/月/日/場所/レース番号/略レース名/芝ダ/距離/頭数/馬名...

    if "raceDate" not in df.columns:
        if {"年", "月", "日"}.issubset(df.columns):
            yy = pd.to_numeric(df["年"], errors="coerce").fillna(0).astype(int)
            mm = pd.to_numeric(df["月"], errors="coerce").fillna(0).astype(int)
            dd = pd.to_numeric(df["日"], errors="coerce").fillna(0).astype(int)
            df["raceDate"] = [f"20{y:02d}-{m:02d}-{d:02d}" for y, m, d in zip(yy, mm, dd)]
        elif "日付" in df.columns:
            s = df["日付"].astype(str).str.replace(".", "-", regex=False).str.replace("/", "-", regex=False)
            df["raceDate"] = s
        else:
            df["raceDate"] = ""

    df["racecourse"] = _pick_series(df, ["場所", "場名", "venue"], "").map(_to_text)
    df["raceNo"] = _pick_series(df, ["レース番号", "R", "raceNo"], "").map(_to_text)
    df["raceClass"] = _pick_series(df, ["略レース名", "レース", "race_name"], "").map(_to_text)
    df["surface"] = _pick_series(df, ["芝ダ", "芝・ダート", "surface"], "").map(_to_text)
    df["distance"] = _pick_series(df, ["距離", "distance"], "").map(_to_text)
    df["horseCount"] = _pick_series(df, ["頭数", "horseCount"], "").map(_to_text)
    df["horseName"] = _pick_series(df, ["馬名", "horse_name", "horseName"], "").map(_to_text)
    df["jockey"] = _pick_series(df, ["騎手", "jockey"], "").map(_to_text)
    df["finishPosition"] = _pick_series(df, ["確定着順", "着順", "finishPosition"], "").map(_to_text)
    df["horseNumber"] = _pick_series(df, ["馬番", "horse_number"], "").map(_to_text)

    score = 80 - pd.to_numeric(df["horseNumber"], errors="coerce").fillna(99)
    category, trust = _category_and_trust(score)

    df["category"] = category
    df["trust"] = trust
    df["comment"] = (
        "score="
        + score.astype(int).astype(str)
        + " / 今後ここに直線ロジック・展開ロジックを実装"
    )

    out = df[
        [
            "raceDate",
            "racecourse",
            "raceNo",
            "raceClass",
            "surface",
            "distance",
            "horseCount",
            "horseName",
            "category",
            "trust",
            "finishPosition",
            "comment",
        ]
    ].copy()
    out = out.fillna("")
    return out


def process_csv(df: pd.DataFrame, input_type: str = "auto") -> pd.DataFrame:
    df = _clean_columns(df)
    if input_type == "auto":
        input_type = detect_input_type(df)

    if input_type == "final_csv":
        return _normalize_final_csv(df)
    if input_type == "target_raw":
        return _normalize_target_raw(df)

    raise ValueError(
        "入力形式を判定できませんでした。TARGET元CSVかFinalCSVをアップしてください。"
    )
