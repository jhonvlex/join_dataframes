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



def test2(df, threshold):
    """
    Compara los nombres en cada fila a nivel de letras, usando similitud de Jaccard.

    Agrega la columna 'predicted' con 1 si la similitud de Jaccard >= threshold, 0 en caso contrario.
    """

    def jaccard_letras(n1, n2):
        set1 = set(n1.lower().replace(" ", ""))
        set2 = set(n2.lower().replace(" ", ""))

        if not set1 or not set2:
            return 0
        
        inter = set1 & set2
        union = set1 | set2
        return len(inter) / len(union)

    df = df.copy()
    df["predicted"] = df.apply(
        lambda row: int(jaccard_letras(row["name1"], row["name2"]) >= threshold),
        axis=1
    )
    
    return df


# V3