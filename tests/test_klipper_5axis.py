from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
KIAUH_ROOT = ROOT / "kiauh"
sys.path.insert(0, str(KIAUH_ROOT))

from components.klipper_5axis.klipper_5axis import _install_system_packages


class Klipper5AxisSystemPackagesTest(unittest.TestCase):
    def test_installs_arm_cross_compiler_dependencies(self) -> None:
        with patch("components.klipper_5axis.klipper_5axis.run") as run_mock:
            _install_system_packages()

        command = run_mock.call_args.args[0]
        self.assertIn("gcc-arm-none-eabi", command)
        self.assertIn("binutils-arm-none-eabi", command)
        self.assertIn("libnewlib-arm-none-eabi", command)


if __name__ == "__main__":
    unittest.main()
