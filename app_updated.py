import streamlit as st
import pandas as pd
from logic_updated import process_csv, detect_input_type, REQUIRED_FINAL_COLUMNS

st.set_page_config(page_title="競馬CSV変換アプリ", layout="wide")

st.title("競馬CSV変換アプリ")
st.write("TARGETの元CSVでも、完成済みFinalCSVでも読み込めます。自動判定で最終CSV形式にそろえます。")

with st.expander("対応している入力形式"):
    st.markdown(
        """
- TARGET/Excel由来の元CSV
- すでに整形済みの FinalCSV

最終出力列:
`raceDate, racecourse, raceNo, raceClass, surface, distance, horseCount, horseName, category, trust, finishPosition, comment`
        """
    )

uploaded_file = st.file_uploader("CSVを選択してください", type=["csv"])

mode = st.radio(
    "入力形式",
    ["自動判定", "TARGET元CSVとして読む", "FinalCSVとして読む"],
    horizontal=True,
)

if uploaded_file is not None:
    encodings = ["utf-8-sig", "cp932", "shift_jis", "utf-8"]
    df = None
    used_enc = None

    for enc in encodings:
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding=enc)
            used_enc = enc
            break
        except Exception:
            continue

    if df is None:
        st.error("CSVの読み込みに失敗しました。UTF-8 / CP932 / Shift_JIS のいずれでも読めませんでした。")
        st.stop()

    st.success(f"CSV読込成功: encoding={used_enc}")
    st.caption(f"行数: {len(df):,} / 列数: {len(df.columns):,}")

    if mode == "自動判定":
        input_type = detect_input_type(df)
    elif mode == "TARGET元CSVとして読む":
        input_type = "target_raw"
    else:
        input_type = "final_csv"

    st.info(f"判定結果: {input_type}")

    st.subheader("元データ")
    st.dataframe(df.head(100), use_container_width=True)

    try:
        result_df = process_csv(df, input_type=input_type)
    except Exception as e:
        st.error(f"変換エラー: {e}")
        st.stop()

    st.subheader("変換後データ")
    st.dataframe(result_df.head(200), use_container_width=True)

    missing = [c for c in REQUIRED_FINAL_COLUMNS if c not in result_df.columns]
    if missing:
        st.error(f"出力列が不足しています: {missing}")
    else:
        st.success("最終CSV形式に変換できました。")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("出力行数", f"{len(result_df):,}")
    with c2:
        st.metric("ユニークレース数", f"{result_df[['raceDate','racecourse','raceNo']].drop_duplicates().shape[0]:,}")
    with c3:
        st.metric("ユニーク馬数", f"{result_df['horseName'].nunique():,}")

    csv_data = result_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="変換後CSVをダウンロード",
        data=csv_data,
        file_name="converted_keiba.csv",
        mime="text/csv",
        use_container_width=True,
    )
