import streamlit as st
import pandas as pd
from logic import process_target_csv

st.set_page_config(page_title="競馬CSV変換アプリ", layout="wide")

st.title("競馬CSV変換アプリ")
st.write("TARGETで出力したCSVを読み込み、独自ロジックで新CSVを生成します。")

uploaded_file = st.file_uploader("CSVを選択してください", type=["csv"])

if uploaded_file is not None:
    try:
        encodings = ["utf-8-sig", "cp932", "shift_jis", "utf-8"]
        df = None

        for enc in encodings:
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding=enc)
                st.success(f"CSV読込成功: encoding={enc}")
                break
            except Exception:
                continue

        if df is None:
            st.error("CSVの読み込みに失敗しました。文字コードを確認してください。")
        else:
            st.subheader("元データ")
            st.dataframe(df, use_container_width=True)

            result_df = process_target_csv(df)

            st.subheader("変換後データ")
            st.dataframe(result_df, use_container_width=True)

            csv_data = result_df.to_csv(index=False).encode("utf-8-sig")

            st.download_button(
                label="変換後CSVをダウンロード",
                data=csv_data,
                file_name="converted_keiba.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
