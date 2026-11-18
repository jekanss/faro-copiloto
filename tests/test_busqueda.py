from faro.busqueda import fusionar_rrf, referencias_en


def test_gana_el_que_aparece_en_las_dos_listas():
    sentido = ["PF001_garantia", "BO001_garantia", "PF002_garantia"]
    palabras = ["PF002_garantia", "PF002_compatibles"]
    assert fusionar_rrf([sentido, palabras])[0] == "PF002_garantia"


def test_con_una_sola_lista_respeta_su_orden():
    assert fusionar_rrf([["a", "b", "c"]]) == ["a", "b", "c"]


def test_sin_resultados_devuelve_lista_vacia():
    assert fusionar_rrf([[], []]) == []


def test_detecta_la_referencia_aunque_venga_en_minuscula():
    assert referencias_en("garantia de la far-pf-002") == ["FAR-PF-002"]


def test_sin_codigo_no_hay_filtro():
    assert referencias_en("garantia de las pastillas del Spark 10W-30") == []


def test_varias_referencias_sin_repetir():
    pregunta = "FAR-PF-002 o FAR-PF-001, o la FAR-PF-002"
    assert referencias_en(pregunta) == ["FAR-PF-001", "FAR-PF-002"]