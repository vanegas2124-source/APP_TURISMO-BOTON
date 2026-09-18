from supabase_ml import supabase


def probar():

    dataset = (
        supabase
        .table("dataset_entrenamiento")
        .select("id")
        .execute()
    )

    lugares = (
        supabase
        .table("lugares")
        .select(
            "id,nombre,vereda,"
            "latitud,longitud"
        )
        .execute()
    )

    print("=" * 60)
    print("CONEXIÓN CON SUPABASE")
    print("=" * 60)

    print(
        "Dataset:",
        len(dataset.data),
        "registros"
    )

    print(
        "Lugares:",
        len(lugares.data),
        "registros"
    )

    print("\nLUGARES:")

    for lugar in lugares.data:
        print(
            "-",
            lugar.get("nombre")
        )


if __name__ == "__main__":
    probar()