import tempfile
import unittest
from pathlib import Path

from app.engine import PaperEngine


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = str(Path(self.folder.name) / "ledger.db")
        self.engine = PaperEngine(self.path, starting_balance=10000)
        self.now = 1900000000.0
        self.engine.update_prices({"BTC": 100.0, "ETH": 200.0, "SOL": 50.0}, self.now)

    def tearDown(self):
        self.engine.db.close()
        self.folder.cleanup()

    def test_paper_trade_enters_with_stop_and_target(self):
        order = self.engine.open("BTC", "LONG", 1, now=self.now + 1)
        self.assertTrue(order["ok"])
        self.assertGreater(order["target"], order["entry"])
        self.assertLess(order["stop"], order["entry"])
        self.assertLessEqual(order["qty"] * order["entry"], 2010)
        self.assertEqual(self.engine.status(self.now + 1)["mode"], "PAPER")

    def test_target_closes_and_fees_recorded(self):
        order = self.engine.open("BTC", "LONG", 1, now=self.now + 1)
        self.assertTrue(order["ok"])
        self.engine.update_prices({"BTC": order["target"] * 1.005}, self.now + 2)
        self.assertEqual(len(self.engine.status(self.now + 2)["positions"]), 0)
        closed = self.engine.trades()
        self.assertEqual(len(closed), 1)
        self.assertEqual(closed[0]["reason"], "TARGET")
        self.assertGreater(closed[0]["fee"], 0)
        self.assertGreater(closed[0]["pnl"], 0)

    def test_stop_closes_short(self):
        order = self.engine.open("ETH", "SHORT", 1, now=self.now + 1)
        self.assertTrue(order["ok"])
        self.engine.update_prices({"ETH": order["stop"] * 1.005}, self.now + 2)
        self.assertEqual(self.engine.trades()[0]["reason"], "STOP")
        self.assertLess(self.engine.trades()[0]["pnl"], 0)

    def test_duplicate_symbol_blocked(self):
        self.assertTrue(self.engine.open("BTC", "LONG", 1, now=self.now + 1)["ok"])
        self.assertEqual(self.engine.open("BTC", "SHORT", 1, now=self.now + 2)["reason"], "ALREADY_OPEN")

    def test_fails_closed_on_stale_data(self):
        self.assertEqual(self.engine.open("BTC", "LONG", 1, now=self.now + 90)["reason"], "STALE_MARKET_DATA")

    def test_invalid_order_blocked(self):
        self.assertEqual(self.engine.open("OTHER", "LONG", 1, now=self.now + 1)["reason"], "INVALID_ORDER")
        self.assertEqual(self.engine.open("BTC", "SIDEWAYS", 1, now=self.now + 1)["reason"], "INVALID_ORDER")

    def test_paused_and_kill_switch_latches(self):
        self.assertTrue(self.engine.set_control("pause", now=self.now + 1)["ok"])
        self.assertEqual(self.engine.open("BTC", "LONG", 1, now=self.now + 2)["reason"], "PAUSED")
        self.engine.set_control("resume", now=self.now + 2)
        self.assertTrue(self.engine.set_control("kill", now=self.now + 3)["ok"])
        self.assertEqual(self.engine.open("BTC", "LONG", 1, now=self.now + 4)["reason"], "KILL_SWITCH")
        self.assertEqual(self.engine.set_control("resume", now=self.now + 4)["reason"], "KILL_SWITCH_LATCHED_RESTART_REQUIRED")

    def test_db_persists_positions_and_kill_across_restart(self):
        order = self.engine.open("BTC", "LONG", 1, now=self.now + 1)
        self.assertTrue(order["ok"])
        self.engine.set_control("kill", now=self.now + 90)  # stale feed -> unresolved position remains
        self.engine.db.close()
        self.engine = PaperEngine(self.path)
        status = self.engine.status(self.now + 91)
        self.assertTrue(status["killed"])
        self.assertEqual(len(status["positions"]), 1)
        self.assertEqual(status["feed_status"], "STALE")

    def test_daily_loss_gate(self):
        self.engine._set("day_realized_pnl", -400)
        self.engine.db.commit()
        self.assertEqual(self.engine.open("SOL", "LONG", 1, now=self.now + 1)["reason"], "DAILY_LOSS_LIMIT")

    def test_rule_signal_warmup(self):
        self.assertEqual(self.engine.rule_signal("BTC")["side"], "WAIT")
        for k in range(40):
            self.engine.update_prices({"BTC": 100.0 + k * 0.15}, self.now + k + 1)
        self.assertIn(self.engine.rule_signal("BTC")["side"], ("LONG", "WAIT"))


if __name__ == "__main__":
    unittest.main()
