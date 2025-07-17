from rapidfuzz.fuzz import token_sort_ratio

#  Compara name1 y name2 palabra por palabra según reglas personalizadas:
# - Si hay más de 2 palabras: máximo 1 diferente → match
# - Si hay 2 palabras: deben ser idénticas
def test(df):
    """
    Aplica una heurística para predecir si dos nombres son casi iguales.

    Agrega una columna 'predicted' al DataFrame con valores 1 o 0.
    """

    def comparar_nombre_personalizada(n1, n2):
        palabras_1 = n1.lower().split()
        palabras_2 = n2.lower().split()

        # Caso exacto: ambos con 2 palabras idénticas
        if len(palabras_1) == 2 and len(palabras_2) == 2:
            return int(palabras_1 == palabras_2)

        # Para el resto, se mide la diferencia
        union_total = set(palabras_1).union(set(palabras_2))
        interseccion = set(palabras_1).intersection(set(palabras_2))
        n_diff = len(union_total) - len(interseccion)

        return int(n_diff <= 1)  # Se acepta si solo difieren en una palabra o menos

    df = df.copy()
    df["predicted"] = df.apply(lambda row: comparar_nombre_personalizada(row["name1"], row["name2"]), axis=1)
    return df

# NUEVA LINEA

def jaccard_sim(n1, n2):
    set1, set2 = set(n1.split()), set(n2.split())
    if not set1 or not set2:
        return 0
    return len(set1 & set2) / len(set1 | set2)

def palabras_distintas(n1, n2):
    set1, set2 = set(n1.split()), set(n2.split())
    return len(set1.symmetric_difference(set2))

def ensemble_name_match(df, w_token=0.6, w_jaccard=0.3, w_penal=0.1, threshold=80):
    """
    Calcula un score de similitud ponderado entre pares de nombres y predice matches.
    
    Requiere que el DataFrame tenga columnas: 'name1', 'name2', y 'actual'.

    Devuelve:
        DataFrame con columnas:
        - score_ensemble: puntuación combinada
        - match_pred: predicción binaria del modelo
        - actual: etiqueta verdadera (ya debe estar en el DataFrame)
    """
    df = df.copy()

    def calcular_score(row):
        n1, n2 = row['name1'], row['name2']
        score_token = token_sort_ratio(n1, n2)
        score_jaccard = jaccard_sim(n1, n2) * 100
        penal = palabras_distintas(n1, n2) * 10

        return (w_token * score_token +
                w_jaccard * score_jaccard -
                w_penal * penal)

    df["score_ensemble"] = df.apply(calcular_score, axis=1)
    df["match_pred"] = df["score_ensemble"].apply(lambda x: 1 if x >= threshold else 0)

    # Ya no se genera 'match_true', asumimos que 'actual' ya está
    return df
