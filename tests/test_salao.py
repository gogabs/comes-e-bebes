import unittest

from helpers import bench, focus, new_service, run

from comes import config as C
from comes.expediente import COZINHA, SALAO, STATIONS, Item


def seat(s, index=0, order=("suco",)):
    t = s.tables[index]
    s._seat(t)
    t.order = list(order)
    t.wanted = list(order)
    return t


class AtendimentoTest(unittest.TestCase):
    def test_ciclo_completo(self):
        s, ui, casa, _, _ = new_service()
        money = casa.money
        t = seat(s, 0, ("suco",))
        self.assertEqual(t.state, "sentado")
        run(s, max(C.CALL_DELAY) + 0.2)
        self.assertEqual(t.state, "pedir")
        self.assertIn("chamar", ui.played)
        focus(s, SALAO, 0)
        s.action_down()
        self.assertEqual(t.state, "esperando")
        self.assertIn("pediu um suco de laranja", ui.last())
        s.hands = [Item("suco")]
        s.action_down()
        self.assertEqual(t.state, "comendo")
        run(s, max(C.EAT_TIME) + 0.2)
        self.assertEqual(t.state, "pagar")
        s.action_down()
        self.assertEqual(t.state, "suja")
        self.assertGreater(casa.money, money)
        self.assertEqual(s.stats["served"], 1)
        s.action_down()
        self.assertEqual(t.state, "livre")
        self.assertEqual(s.hands[0].kind, "louca")
        focus(s, COZINHA, STATIONS.index("pia"))
        s.action_down()
        self.assertEqual(casa.dirt["louca"], 1)

    def test_prato_errado(self):
        s, ui, _, _, _ = new_service()
        t = seat(s, 1, ("misto",))
        t.state = "esperando"
        t.patience = t.patience_max = 100
        focus(s, SALAO, 1)
        s.hands = [Item("suco")]
        s.action_down()
        self.assertIn("Não foi isso", ui.last())
        self.assertEqual(len(s.hands), 1)

    def test_paciencia_acaba(self):
        s, ui, casa, _, _ = new_service()
        rep = casa.reputation
        t = seat(s, 0)
        run(s, max(C.CALL_DELAY) + C.PATIENCE_ORDER * 3)
        self.assertEqual(t.state, "livre")
        self.assertEqual(s.stats["left"], 1)
        self.assertLess(casa.reputation, rep)
        for stage in (1, 2, 3):
            self.assertIn("impaciencia%d" % stage, ui.played)

    def test_fogo_drena_paciencia(self):
        s, _, _, _, _ = new_service()
        t = seat(s, 0)
        run(s, max(C.CALL_DELAY) + 0.1)
        before = t.patience
        s.cookers["chapa"].fire = True
        run(s, 1.0)
        self.assertAlmostEqual(before - t.patience, C.FIRE_PATIENCE_DRAIN, delta=0.3)

    def test_gorjeta_por_qualidade(self):
        s, _, casa, _, _ = new_service()
        for quality, idx in ((1.0, 0), (0.5, 1)):
            t = seat(s, idx, ("xburger",))
            t.served = [("xburger", quality)]
            t.order = []
            t.state = "pagar"
            t.patience = t.patience_max = 100
        focus(s, SALAO, 0)
        s.action_down()
        tips_good = s.stats["tips"]
        focus(s, SALAO, 1)
        s.action_down()
        self.assertGreater(tips_good, 0)
        self.assertEqual(s.stats["tips"], tips_good)

    def test_sem_ingrediente_nao_pede(self):
        s, ui, casa, _, _ = new_service()
        for k in casa.stock:
            casa.stock[k] = []
        s._seat(s.tables[0])
        self.assertEqual(s.tables[0].state, "livre")
        self.assertIn("não tinha nada", ui.last())

    def test_pedido_respeita_cardapio(self):
        s, _, casa, _, _ = new_service(seed=3)
        casa.menu = {"misto": False, "xburger": False, "fritas": False, "suco": True}
        for _ in range(20):
            self.assertEqual(set(s._choose_order()), {"suco"})


class NavegacaoTest(unittest.TestCase):
    def test_bordas_e_camadas(self):
        s, ui, _, _, _ = new_service()
        s.step(1)
        s.step(1)
        self.assertEqual(ui.played[-1], "borda")
        s.go_layer(COZINHA)
        self.assertTrue(ui.last().startswith("Cozinha. Bancada"))

    def test_pulo_para_quem_precisa(self):
        s, ui, _, _, _ = new_service()
        t = seat(s, 2)
        t.state = "pedir"
        t.patience = t.patience_max = 50
        focus(s, COZINHA, 0)
        s.jump(1)
        self.assertEqual((s.layer, s.index[SALAO]), (SALAO, 2))
        self.assertIn("Mesa 3", ui.last())

    def test_nada_precisa(self):
        s, ui, _, _, _ = new_service()
        s.jump(1)
        self.assertIn("Nada precisa", ui.last())

    def test_bancada_abre_lista(self):
        s, ui, _, _, _ = new_service()
        focus(s, COZINHA, 0)
        s.action_down()
        self.assertEqual(ui.bench_opened, 1)


class FimDoDiaTest(unittest.TestCase):
    def test_fecha_e_termina(self):
        s, ui, casa, done, _ = new_service()
        t = seat(s, 0)
        t.state = "suja"
        t.louca = 2
        s.hands = [Item("misto")]
        run(s, C.DAY_SECONDS + 3, step=0.5)
        self.assertFalse(s.open)
        self.assertEqual(len(done), 1)
        self.assertEqual(casa.dirt["louca"], 2)
        self.assertEqual(casa.dirt["lixo"], 1)

    def test_espera_quem_ficou(self):
        s, _, _, done, _ = new_service()
        t = seat(s, 0)
        t.state = "comendo"
        t.timer = 1e9
        run(s, C.DAY_SECONDS + 5, step=0.5)
        self.assertEqual(done, [])

    def test_chegadas_no_dia(self):
        s, _, _, _, _ = new_service(seed=5)
        s.next_arrival = C.FIRST_ARRIVAL
        run(s, 60, step=0.5)
        self.assertTrue(any(t.state != "livre" for t in s.tables))


if __name__ == "__main__":
    unittest.main()
