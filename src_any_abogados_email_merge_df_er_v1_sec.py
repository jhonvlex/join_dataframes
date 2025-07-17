import pandas as pd
import re
from rapidfuzz.fuzz import ratio

def merge_by_email(df1, df2, df1_email_colname, df2_email_colname, df1_name, df2_name):

    df_1 = df1[df1[df1_email_colname].notna()].copy()
    df_2 = df2[df2[df2_email_colname].notna()].copy()

    df_1 = df_1.drop_duplicates(subset=df1_email_colname)
    df_2 = df_2.drop_duplicates(subset=df2_email_colname)

    df_merged = pd.merge(df_1, df_2, left_on=df1_email_colname, right_on=df2_email_colname, how="inner")   

    df_merged["score"] = df_merged.apply(lambda row: ratio(str(row[df1_name]), str(row[df2_name]))/100, axis=1)

    return df_merged