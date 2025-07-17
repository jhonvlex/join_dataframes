from rapidfuzz.fuzz import token_sort_ratio

#  Compara name1 y name2 palabra por palabra según reglas personalizadas:
# - Si hay más de 2 palabras: máximo 1 diferente → match
# - Si hay 2 palabras: deben ser idénticas
def test(df):

    def comparar_nombre_personalizada(n1, n2):
        palabras_1 = n1.lower().split()
        palabras_2 = n2.lower().split()

        # Caso: ambos nombres tienen exactamente 2 palabras
        if len(palabras_1) == 2 and len(palabras_2) == 2:
            return int(palabras_1 == palabras_2)

        # Para el resto: contar diferencias entre palabras comunes
        palabras_comunes = min(len(palabras_1), len(palabras_2))
        diferencias = sum(p1 != p2 for p1, p2 in zip(palabras_1, palabras_2))

        # Contar diferencias con lógica más robusta
        union_total = set(palabras_1).union(set(palabras_2))
        interseccion = set(palabras_1).intersection(set(palabras_2))
        n_diff = len(union_total) - len(interseccion)

        return int(n_diff <= 1)

    df = df.copy()
    df["match_pred"] = df.apply(lambda row: comparar_nombre_personalizada(row["name1"], row["name2"]), axis=1)
    return df

#Similitud entre conjuntos de palabras
def jaccard_sim(n1, n2):

    set1, set2 = set(n1.split()), set(n2.split())
    if not set1 or not set2:
        return 0
    return len(set1 & set2) / len(set1 | set2)

# Cuenta palabras diferentes entre dos nombres
def palabras_distintas(n1, n2):
    
    set1, set2 = set(n1.split()), set(n2.split())
    return len(set1.symmetric_difference(set2))

# Calcula un score combinado de similitud para comparar nombres:
# - Devuelve match_pred (predicción)
# - Devuelve match_true (etiqueta real)
def ensemble_name_match(df, w_token=0.6, w_jaccard=0.3, w_penal=0.1, threshold=80):

    df = df.copy()

    def calcular_score(row):
        n1, n2 = row['name1'], row['name2']
        score_token = token_sort_ratio(n1, n2)  # 0-100
        score_jaccard = jaccard_sim(n1, n2) * 100
        penal = palabras_distintas(n1, n2) * 10  # penalización proporcional

        score_final = (w_token * score_token +
                       w_jaccard * score_jaccard -
                       w_penal * penal)
        
        return score_final

    df["score_ensemble"] = df.apply(calcular_score, axis=1)
    df["match_pred"] = df["score_ensemble"].apply(lambda x: 1 if x >= threshold else 0)
    df["match_true"] = df.apply(lambda row: 1 if row["name1"] == row["name2"] else 0, axis=1)

    return df