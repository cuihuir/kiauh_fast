from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
KIAUH_ROOT = ROOT / "kiauh"
sys.path.insert(0, str(KIAUH_ROOT))

from components.crowsnest.crowsnest_optimized import (  # noqa: E402
    ensure_crowsnest_install_config,
    repair_crowsnest_service_user,
    run_crowsnest_makefile_install,
)


class CrowsnestOptimizedInstallTest(unittest.TestCase):
    def test_rewrites_root_base_user_in_existing_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            crowsnest_dir = Path(temp_dir) / "crowsnest"
            config_file = crowsnest_dir / "tools" / ".config"
            config_file.parent.mkdir(parents=True)
            config_file.write_text(
                "\n".join(
                    [
                        'BASE_USER="root"',
                        'CROWSNEST_CONFIG_PATH="/home/tope/printer_data/config"',
                        'CROWSNEST_LOG_PATH="/home/tope/printer_data/logs"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            ensure_crowsnest_install_config(crowsnest_dir, "tope")

            contents = config_file.read_text(encoding="utf-8")
            self.assertIn('BASE_USER="tope"', contents)
            self.assertNotIn('BASE_USER="root"', contents)
            self.assertIn(
                'CROWSNEST_CONFIG_PATH="/home/tope/printer_data/config"',
                contents,
            )

    def test_make_config_runs_without_sudo_before_install(self) -> None:
        completed = MagicMock(returncode=0)

        with patch(
            "components.crowsnest.crowsnest_optimized.run",
            return_value=completed,
        ) as run_mock, patch(
            "components.crowsnest.crowsnest_optimized.ensure_crowsnest_install_config",
            return_value=True,
        ):
            self.assertTrue(run_crowsnest_makefile_install())

        self.assertEqual(["make", "config"], run_mock.call_args_list[0].args[0])
        self.assertEqual(
            ["sudo", "make", "install"],
            run_mock.call_args_list[1].args[0],
        )

    def test_repairs_root_user_and_working_directory_in_service(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service_file = Path(temp_dir) / "crowsnest.service"
            service_file.write_text(
                "\n".join(
                    [
                        "[Service]",
                        "User=root",
                        "WorkingDirectory=/home/root/crowsnest",
                        "ExecStart=/home/tope/crowsnest-env/bin/python3 $CROWSNEST_ARGS",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with patch("components.crowsnest.crowsnest_optimized.run") as run_mock:
                self.assertTrue(
                    repair_crowsnest_service_user(
                        service_file=service_file,
                        base_user="tope",
                        reload_systemd=True,
                    )
                )

            contents = service_file.read_text(encoding="utf-8")
            self.assertIn("User=tope", contents)
            self.assertIn("WorkingDirectory=/home/tope/crowsnest", contents)
            run_mock.assert_called_once_with(
                ["sudo", "systemctl", "daemon-reload"],
                check=False,
            )


if __name__ == "__main__":
    unittest.main()
