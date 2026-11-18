from faro.busqueda import fusionar_rrf


def test_gana_el_que_aparece_en_las_dos_listas():
    sentido = ["PF001_garantia", "BO001_garantia", "PF002_garantia"]
    palabras = ["PF002_garantia", "PF002_compatibles"]
    assert fusionar_rrf([sentido, palabras])[0] == "PF002_garantia"


def test_con_una_sola_lista_respeta_su_orden():
    assert fusionar_rrf([["a", "b", "c"]]) == ["a", "b", "c"]


def test_sin_resultados_devuelve_lista_vacia():
    assert fusionar_rrf([[], []]) == []