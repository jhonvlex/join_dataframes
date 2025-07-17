import pandas as pd
from rapidfuzz.fuzz import ratio

# Función que toma dos dataframes df1 y df2 para realizar un inner merge mediante las llaves df1_colname y df2_colname respectivamente
# Adicionalmente, se calcula el score de los nombres de los contactos según las coincidencias exactas de los números de contacto df1_name y df2_name.
# Retorna un dataframe de coincidencias exactas por número y agrega un columna de score para comparar la calidad de la similitud de nombres
def merge_by_email(df1, df2, df1_colname, df2_colname, df1_name, df2_name):

    df1 = df1.copy()
    df2 = df2.copy()

    df1_colname = df1_colname.strip()
    df2_colname = df2_colname.strip()

    df1_name = df1_name.strip()
    df2_name = df2_name.strip()

    df1 = df1[df1[df1_colname].notnull()]
    df2 = df2[df2[df2_colname].notnull()]

    df_merged = pd.merge(df1, df2, left_on=df1_colname, right_on=df2_colname, how="inner")

    df_merged["score"] = df_merged.apply(
        lambda row: 1 if str(row[df1_name]) == str(row[df2_name]) else 0,
        axis=1
    )

    return df_merged