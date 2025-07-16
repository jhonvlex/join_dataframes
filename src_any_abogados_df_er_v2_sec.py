# Importacion de librerias
import pandas as pd
import re
from rapidfuzz.fuzz import ratio

# Función que normaliza el número de contacto. Elimina simbolos especiales y elimina extensiones.
def normalized_phone(phone):
    if not isinstance(phone, str):
        return None
    phone = re.split(r'\bext\b\.?', phone, flags=re.IGNORECASE)[0]
    phone = re.sub(r'\D', '', phone)
    return phone

# Función que toma dos dataframes df1 y df2 para realizar un inner merge mediante las llaves df1_colname y df2_colname respectivamente
# Adicionalmente, se calcula el score de los nombres de los contactos según las coincidencias exactas de los números de contacto df1_name y df2_name.
# Retorna un dataframe de coincidencias exactas por número y agrega un columna de score para comparar la calidad de la similitud de nombres
def merge_by_contact_number(df1, df2, df1_colname, df2_colname, df1_name, df2_name):

    df_ca_o_unique = df1.copy()
    df_naics_o_unique = df2.copy()

    df_merged = pd.merge(df_ca_o_unique, df_naics_o_unique, left_on=df1_colname, right_on=df2_colname, how="inner")   

    df_merged["score"] = df_merged.apply(lambda row: ratio(str(row[df1_name]), str(row[df2_name]))/100, axis=1)

    return df_merged

# Combina múltiples columnas en un DataFrame según orden de prioridad, dejando el primer valor no nulo.
# Se recibe el dataframe orignal df y una lista de los nombres de las columnas a combinar, en orden de prioridad.
# Se recibe el nombre de la nueva columna que agrupa las columnas de la lista.
# Retorna un df con la nueva columna que agrupa las demas.
def combinar_columnas_prioridad(df, columnas, nueva_columna):

    df[nueva_columna] = None
    for col in columnas:
        df[nueva_columna] = df[nueva_columna].combine_first(df[col])
    return df



