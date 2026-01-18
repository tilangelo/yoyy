import pandas as pd
import re
from rapidfuzz import fuzz
def normalize_text(text):

    if pd.isna(text):
        return ""
    return re.sub(r"\s+", " ", str(text).lower().strip())

df_chudodey = pd.read_csv("C:\dev\DataBases\CourseWork1\parsers\chudodey.csv")
df_profi = pd.read_csv("C:\dev\DataBases\CourseWork1\parsers\proficosmetics.csv")

df = pd.concat([df_chudodey, df_profi], ignore_index=True)

print(f"Загружено строк: {len(df)}")

df["brand_norm"] = df["brand"].apply(normalize_text)
df["name_norm"] = df["name"].apply(normalize_text)

result_rows = []

for brand, brand_group in df.groupby("brand_norm"):
    unique_rows = []

    for _, row in brand_group.iterrows():
        is_duplicate = False

        for saved_row in unique_rows:
            score = fuzz.token_sort_ratio(
                row["name_norm"],
                saved_row["name_norm"]
            )

            if score >= 85:
                is_duplicate = True
                break

        if not is_duplicate:
            unique_rows.append(row)

    result_rows.extend(unique_rows)

result_df = pd.DataFrame(result_rows)

result_df = result_df.drop(columns=["brand_norm", "name_norm"])

print(f"После дедупликации строк: {len(result_df)}")

output_file = "merged_deduplicated.csv"
result_df.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"Файл сохранён: {output_file}")
