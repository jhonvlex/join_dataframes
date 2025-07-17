# Importacion de librerias
import pandas as pd
import numpy as np
from collections import Counter
import re
import unicodedata
from thefuzz import fuzz
from rapidfuzz.fuzz import token_sort_ratio
from rapidfuzz.fuzz import ratio
from itertools import product

#Lista de palabras para identificar las firmas
firm_words = [
    
        "law","&","offices","bufete","llc","asociados","puerto","psc","estudio","firm",
        "despacho","legales","servicios","services","offices","p.s.c.","group","notarial","notarios",
        "attornays","csp","associates","and","social","inmigracion","llp","asociados,",
        "archivo","solutions","incapacidad","mediacion","immigration","accidentes","business",
        "abogados","urb","corp","leading","consulting","immigrants","insource","advisors",
        "capitulaciones","busca"
]

#Lista de palabras para remover de los nombres de los registros
remove_words = [

    "dr","mr","ms","mrs","lic","abogado","abogada","esq","j.d","attorney","lawyer","at","law",
    "partner","especialista","asociado","of","the","sr","sra","lcdo","lcda","licenciado",
    "licenciada","aboga","cpa","licda","licdo","oficina", "notario","a","b","c","d","e","f","g","h","i",
    "j","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"                                                                              # ver coherencia y no eliminar del todo
]

#Patrones
pattern_firma = r'\b(?:' + '|'.join(firm_words) + r')\b'
pattern_remover = r'\b(?:' + '|'.join(remove_words ) + r')\b'

def name_normalized(name):

    if not isinstance(name, str):
        return ""

    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8') #Elimina acentos
    name = name.lower()                                                                  #Convierte el nombre en minusculas
    name = re.sub(pattern_remover, '', name)                                             #Remueve las palabras contenidas en pattern_remover
    name = re.sub(r'[^\w\s]', '', name)                                                  #Remueve caracteres especiales                     
    name = re.sub(r'\s+', ' ', name).strip()                                             #Elimina espacios
    return name

# Penalización por número de palabras diferentes
def penalizaition_diff_words_name(name1, name2):

    name1_split = name1.split()
    name2_split = name2.split()
    
    total_words = len(name1_split) + len(name1_split)
    colect = Counter(name1_split + name2_split)
    diff = sum([value for value in colect.values() if value == 1])
    score = (total_words - diff)/total_words
    return score

# Penalización diferencia en las iniciales de todo el nombre
def name_initials(name):
    return ''.join([token[0] for token in name.split() if token]) 

def penalizaition_diff_initials_name(name1, name2):       # Hacer la comparacion con fuzzy

    initials1 = name_initials(name1)
    initials2 = name_initials(name2)

    return ratio(initials1, initials2)/100

def custom_match_score(name1, name2, w1=1/3, w2=1/3, w3=1/3):
    token_sort_score = token_sort_ratio(name1, name2) / 100
    penalization_diff_name = penalizaition_diff_words_name(name1, name2)
    penalization_diff_initials = penalizaition_diff_initials_name(name1, name2)

    final_score = (w1 * token_sort_score + w2 * penalization_diff_name + w3 * penalization_diff_initials)
    return final_score

def find_best_matches(df1, df2, col1, col2, threshold, w1=1/3, w2=1/3, w3=1/3):
    matches = []

    for idx1, name1 in df1[col1].items():
        best_score = 0
        best_idx2 = None

        for idx2, name2 in df2[col2].items():
            score = custom_match_score(name1, name2, w1, w2, w3)
            if score > best_score:
                best_score = score
                best_idx2 = idx2

        if best_score >= threshold:
            row_df1 = df1.loc[idx1]
            row_df2 = df2.loc[best_idx2]
            merged_row = pd.concat([row_df1, row_df2])
            merged_row['match_score'] = best_score
            matches.append(merged_row)

    return pd.DataFrame(matches)

def fuzzy_without_perfect_match(df1,df2,df1_colname,df2_colname):
    
    #DataFrame de coincidencias exactas
    perfect_match = df1.merge(df2, left_on=df1_colname, right_on=df2_colname, how="inner")

    #DataFrame donde NO hay coincidencias exactas en el df de la izquierda
    df1_without_perfect_match = df1.merge(perfect_match[[df2_colname]], left_on=df1_colname,right_on=df2_colname,how="left",indicator=True)
    df1_without_perfect_match = df1_without_perfect_match[df1_without_perfect_match['_merge'] == 'left_only']

    #DataFrame donde NO hay coincidencias exactas en el df de la izquierda
    df2_without_perfect_match = df2.merge(perfect_match[[df1_colname]], left_on=df2_colname,right_on=df1_colname, how="left",indicator=True)
    df2_without_perfect_match = df2_without_perfect_match[df2_without_perfect_match['_merge'] == 'left_only']

    #Eliminar columnas _merge y llave de la otra columna
    df1_without_perfect_match.drop(["_merge",df2_colname], axis=1, inplace=True)
    df2_without_perfect_match.drop(["_merge",df1_colname], axis=1, inplace=True)

    #Comparación fuzzy entre los dataframes sin matches perfectos
    no_perfect_matches = find_best_matches(df1_without_perfect_match,df2_without_perfect_match,df1_colname,df2_colname)
    return perfect_match, no_perfect_matches

def generate_weight_combinations(step=0.1):
    combos = []
    for w1, w2 in product(
        [i * step for i in range(int(1/step) + 1)],
        repeat=2
    ):
        w3 = 1.0 - w1 - w2
        if 0 <= w3 <= 1:
            combos.append((w1, w2, w3))
    return combos


def perfect_matches(df_nombres):
    
    columns = df_nombres.columns

    if len(columns) < 2:
        return pd.nan
    
    resultado = df_nombres[columns[0]].merge(df_nombres[columns[1]], how="inner")

    return resultado

# --


def find_fuzzy_matches(df1, df2, df1_colname, df2_colname, threshold):
    """
    Para cada name1:
    - Busca el mejor match en df2 según similitud.
    - Asigna una columna 'score' con el valor de similitud.
    - Asigna una columna 'actual' con 1 si pasa el threshold, 0 si no.
    - Elimina duplicados en name2, conservando el de mayor score.
    - Retorna un solo DataFrame con toda la información.
    """

    df1_clean = df1[df1[df1_colname].notna()].drop_duplicates(subset=df1_colname)
    df2_clean = df2[df2[df2_colname].notna()].drop_duplicates(subset=df2_colname)

    lista_1 = df1_clean[df1_colname].tolist()
    lista_2 = df2_clean[df2_colname].tolist()

    resultados = []

    for name in lista_1:
        best_score = 0
        best_match = None

        for candidate in lista_2:
            score = token_sort_ratio(name, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate

        resultados.append({
            "name1": name,
            "name2": best_match,
            "score": best_score,
            "actual": int(best_score >= threshold)
        })

    # Convertimos en DataFrame
    df_resultado = pd.DataFrame(resultados)

    # Ordenamos por score descendente y eliminamos duplicados en name2
    df_resultado = df_resultado.sort_values("score", ascending=False)
    df_resultado = df_resultado.drop_duplicates(subset="name2", keep="first")
    df_resultado.reset_index(drop=True, inplace=True)

    return df_resultado


