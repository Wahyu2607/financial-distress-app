from __future__ import annotations

import unittest
from pathlib import Path
import sys

# Tambahkan direktori root proyek ke sys.path agar modul src dapat diimpor langsung
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.calculations import (
    altman_z_score,
    altman_classification,
    mda_score,
    mda_classification,
    build_features_from_financials,
    xgboost_predict,
    xgboost_predict_detailed,
    diagnose_distress_drivers,
    calculate_advanced_metrics,
    evaluate_financial_resilience,
    simulate_what_if,
    calculate_distress_breakeven,
    get_xgboost_evaluation_metrics,
    altman_1968_score,
    evaluate_warning_factors,
    evaluate_model_concordance,
)


class TestFinancialDistressCalculations(unittest.TestCase):
    """
    Kumpulan pengujian unit otomatis untuk memverifikasi akurasi matematis
    formula Altman Z''-Score, MDA Fisher, XGBoost, dan diagnosa finansial
    sesuai landasan teori skripsi pada 704 data observasi emiten manufaktur BEI.
    """

    def setUp(self):
        self.altman_coefficients = {
            "X1": 6.56,
            "X2": 3.26,
            "X3": 6.72,
            "X4": 1.05,
        }
        self.altman_thresholds = {
            "distress": 1.10,
            "grey": 2.60,
        }
        self.mda_coefficients = {
            "X1": 6.1120,
            "X2": 3.2776,
            "X3": 4.8373,
            "X4": 0.0430,
        }
        self.mda_threshold = 0.3844

        # Contoh data laporan keuangan sehat (Aman)
        self.safe_financials = {
            "total_assets": 100_000_000_000.0,
            "total_liabilities": 30_000_000_000.0,
            "current_assets": 50_000_000_000.0,
            "current_liabilities": 20_000_000_000.0,
            "working_capital": 30_000_000_000.0,  # CA - CL
            "retained_earnings": 40_000_000_000.0,
            "ebit": 15_000_000_000.0,
            "common_stock_equity": 70_000_000_000.0,
            "total_revenue": 120_000_000_000.0,
            "interest_expense": 2_000_000_000.0,
            "net_income": 10_000_000_000.0,
            "operating_cash_flow": 12_000_000_000.0,
            "total_debt": 15_000_000_000.0,
        }

        # Contoh data laporan keuangan kesulitan finansial (Distress)
        self.distress_financials = {
            "total_assets": 100_000_000_000.0,
            "total_liabilities": 95_000_000_000.0,
            "current_assets": 20_000_000_000.0,
            "current_liabilities": 50_000_000_000.0,
            "working_capital": -30_000_000_000.0,  # Negatif
            "retained_earnings": -25_000_000_000.0,  # Negatif
            "ebit": -10_000_000_000.0,  # Rugi usaha
            "common_stock_equity": 5_000_000_000.0,
            "total_revenue": 40_000_000_000.0,
            "interest_expense": 8_000_000_000.0,
            "net_income": -15_000_000_000.0,
            "operating_cash_flow": -6_000_000_000.0,
            "total_debt": 70_000_000_000.0,
        }

    def test_build_features_from_financials(self):
        """Uji pembentukan rasio X1-X5 dari akun laporan keuangan."""
        ratios = build_features_from_financials(self.safe_financials)
        self.assertAlmostEqual(ratios["X1"], 30_000_000_000.0 / 100_000_000_000.0)  # 0.30
        self.assertAlmostEqual(ratios["X2"], 40_000_000_000.0 / 100_000_000_000.0)  # 0.40
        self.assertAlmostEqual(ratios["X3"], 15_000_000_000.0 / 100_000_000_000.0)  # 0.15
        self.assertAlmostEqual(ratios["X4"], 70_000_000_000.0 / 30_000_000_000.0)  # 2.3333
        self.assertAlmostEqual(ratios["X5"], 120_000_000_000.0 / 100_000_000_000.0)  # 1.20

    def test_capping_x4_rule(self):
        """Uji aturan pembatasan (capping) rasio X4 <= 3.0 sesuai teori skripsi hal 41 & 95."""
        high_equity_ratios = {
            "X1": 0.20,
            "X2": 0.30,
            "X3": 0.10,
            "X4": 15.0,  # Sangat ekstrem > 3.0
        }
        # Dengan capping aktif (default True)
        z_capped = altman_z_score(high_equity_ratios, self.altman_coefficients, cap_x4=True)
        # Nilai X4 yang digunakan harus 3.0, bukan 15.0
        expected_z = 6.56 * 0.20 + 3.26 * 0.30 + 6.72 * 0.10 + 1.05 * 3.0
        self.assertAlmostEqual(z_capped, expected_z, places=4)

        # Tanpa capping (cap_x4=False)
        z_uncapped = altman_z_score(high_equity_ratios, self.altman_coefficients, cap_x4=False)
        expected_uncapped = 6.56 * 0.20 + 3.26 * 0.30 + 6.72 * 0.10 + 1.05 * 15.0
        self.assertAlmostEqual(z_uncapped, expected_uncapped, places=4)
        self.assertGreater(z_uncapped, z_capped)

    def test_altman_classification(self):
        """Uji klasifikasi batas zona Altman Z''-Score."""
        # Distress: Z <= 1.10
        self.assertEqual(altman_classification(0.85, self.altman_thresholds), "distress")
        self.assertEqual(altman_classification(1.10, self.altman_thresholds), "distress")

        # Grey area: 1.10 < Z < 2.60
        self.assertEqual(altman_classification(1.50, self.altman_thresholds), "grey area")
        self.assertEqual(altman_classification(2.59, self.altman_thresholds), "grey area")

        # Aman: Z >= 2.60
        self.assertEqual(altman_classification(2.61, self.altman_thresholds), "aman")
        self.assertEqual(altman_classification(4.50, self.altman_thresholds), "aman")

    def test_mda_score_and_classification(self):
        """Uji formula dan cut-off MDA Fisher objektif 0.3844."""
        safe_ratios = {"X1": 0.30, "X2": 0.40, "X3": 0.15, "X4": 2.0}
        score_safe = mda_score(safe_ratios, self.mda_coefficients)
        expected_score = 6.1120 * 0.30 + 3.2776 * 0.40 + 4.8373 * 0.15 + 0.0430 * 2.0
        self.assertAlmostEqual(score_safe, expected_score, places=4)
        self.assertEqual(mda_classification(score_safe, self.mda_threshold), "aman")

        distress_ratios = {"X1": -0.30, "X2": -0.25, "X3": -0.10, "X4": 0.05}
        score_distress = mda_score(distress_ratios, self.mda_coefficients)
        self.assertLess(score_distress, self.mda_threshold)
        self.assertEqual(mda_classification(score_distress, self.mda_threshold), "distress")

    def test_diagnose_distress_drivers(self):
        """Uji penguraian faktor penyebab distress (worst and best drivers)."""
        ratios = {"X1": -0.20, "X2": 0.05, "X3": -0.15, "X4": 0.50}
        diag = diagnose_distress_drivers(ratios, self.altman_coefficients, self.altman_thresholds)
        self.assertIn("contributions", diag)
        self.assertIn("worst_driver", diag)
        self.assertIn("best_driver", diag)
        self.assertIn("findings", diag)
        self.assertEqual(len(diag["findings"]), 4)

    def test_what_if_simulation(self):
        """Uji simulasi sensitivitas What-If perbaikan kinerja."""
        base_ratios = build_features_from_financials(self.distress_financials)
        sim = simulate_what_if(
            self.distress_financials,
            self.altman_coefficients,
            self.altman_thresholds,
            delta_ebit_pct=50.0,
            working_capital_boost=20_000_000_000.0,
            base_ratios=base_ratios,
        )
        self.assertIn("z_orig", sim)
        self.assertIn("z_sim", sim)
        self.assertGreater(sim["z_sim"], sim["z_orig"])
        self.assertTrue(sim["improved"])

    def test_distress_breakeven(self):
        """Uji perhitungan titik impas target EBIT keluar dari zona distress."""
        be = calculate_distress_breakeven(
            self.distress_financials,
            self.altman_coefficients,
            self.altman_thresholds,
        )
        self.assertTrue(be.get("available"))
        self.assertIn("required_ebit_exit_distress", be)
        self.assertIn("gap_to_exit_distress", be)

    def test_evaluation_metrics_integrity(self):
        """Uji integritas data evaluasi model XGBoost empiris (Fitur No. 6)."""
        eval_data = get_xgboost_evaluation_metrics()
        self.assertIsInstance(eval_data, dict)
        self.assertIn("accuracy", eval_data)
        self.assertIn("roc_auc", eval_data)
        self.assertIn("confusion_matrix", eval_data)
        self.assertIn("classification_report", eval_data)
        self.assertIn("roc_curve", eval_data)

        # Akurasi dan ROC-AUC harus berada dalam rentang wajar [0.8, 1.0]
        self.assertGreaterEqual(eval_data["accuracy"], 0.80)
        self.assertGreaterEqual(eval_data["roc_auc"], 0.80)

        # CM Details harus memiliki 4 kuadran
        cm_det = eval_data.get("cm_details", {})
        self.assertIn("tn", cm_det)
        self.assertIn("fp", cm_det)
        self.assertIn("fn", cm_det)
        self.assertIn("tp", cm_det)

        # Uji Youden's J Statistic (Bab II Persamaan 18 Hal. 67)
        self.assertIn("youden_j", eval_data)
        self.assertIn("specificity", eval_data)
        self.assertGreaterEqual(eval_data["youden_j"], 0.70)

        # Uji Multi-Model Benchmark Table (Lampiran 4 Hal. 141-143)
        self.assertIn("multi_model_benchmark", eval_data)
        self.assertGreaterEqual(len(eval_data["multi_model_benchmark"]), 3)

    def test_altman_1968_score(self):
        """Uji Model Altman Z-Score Asli 5 Variabel (1968) sesuai Bab II Subbab 2.2.8 & Tabel 2.1."""
        safe_ratios = {"X1": 0.30, "X2": 0.40, "X3": 0.15, "X4": 2.0, "X5": 1.2}
        z_val, z_cls = altman_1968_score(safe_ratios)
        # Z = 1.2*0.30 + 1.4*0.40 + 3.3*0.15 + 0.6*2.0 + 0.999*1.2
        expected_z = 1.2*0.30 + 1.4*0.40 + 3.3*0.15 + 0.6*2.0 + 0.999*1.2
        self.assertAlmostEqual(z_val, expected_z, places=4)
        self.assertEqual(z_cls, "aman")  # > 2.99

        distress_ratios = {"X1": -0.20, "X2": -0.30, "X3": -0.10, "X4": 0.10, "X5": 0.50}
        z_d_val, z_d_cls = altman_1968_score(distress_ratios)
        self.assertLess(z_d_val, 1.81)
        self.assertEqual(z_d_cls, "distress")

    def test_evaluate_warning_factors(self):
        """Uji 5 Indikator Peringatan Dini Finansial (Gambar 3.2 Hal. 88 & 95, Lampiran 5)."""
        # Data perusahaan sehat: semua aman
        wf_safe = evaluate_warning_factors(self.safe_financials)
        self.assertEqual(wf_safe["triggered_count"], 0)
        self.assertEqual(wf_safe["risk_level"], "AMAN")
        self.assertFalse(wf_safe["ebit"]["flag"])
        self.assertFalse(wf_safe["tie"]["flag"])
        self.assertFalse(wf_safe["cfo"]["flag"])
        self.assertFalse(wf_safe["ce"]["flag"])
        self.assertFalse(wf_safe["nwc"]["flag"])

        # Data perusahaan distress: terpicu minimal 3 indikator (Kritis)
        wf_distress = evaluate_warning_factors(self.distress_financials)
        self.assertGreaterEqual(wf_distress["triggered_count"], 3)
        self.assertEqual(wf_distress["risk_level"], "KRITIS")
        self.assertTrue(wf_distress["ebit"]["flag"])  # EBIT < 0
        self.assertTrue(wf_distress["tie"]["flag"])   # TIE < 1
        self.assertTrue(wf_distress["cfo"]["flag"])   # CFO < 0
        self.assertTrue(wf_distress["nwc"]["flag"])   # NWC < 0

    def test_evaluate_model_concordance(self):
        """Uji evaluasi kesesuaian skor antar-model (Gambar 3.2 Proposal)."""
        # Kesesuaian penuh (Semua sepakat distress)
        conc_full_d = evaluate_model_concordance("distress", "distress", 1)
        self.assertTrue(conc_full_d["is_concordant"])
        self.assertIn("SESUAI", conc_full_d["status_text"])

        # Kesesuaian penuh (Semua sepakat aman)
        conc_full_safe = evaluate_model_concordance("aman", "aman", 0)
        self.assertTrue(conc_full_safe["is_concordant"])
        self.assertIn("SESUAI", conc_full_safe["status_text"])

        # Divergen (Altman distress, MDA aman, XGBoost distress)
        conc_div = evaluate_model_concordance("distress", "aman", 1)
        self.assertFalse(conc_div["is_concordant"])
        self.assertIn("DIVERGEN", conc_div["status_text"])


if __name__ == "__main__":
    unittest.main()
