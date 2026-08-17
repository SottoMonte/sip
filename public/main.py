from __future__ import annotations

import argparse
import asyncio
import io
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PYPROJECT = ROOT / "pyproject.toml"

sys.path.insert(0, str(SRC))


# ============================================================
# CONFIGURATION
# ============================================================

def load_config() -> dict:
    """
    Legge la configurazione del progetto da pyproject.toml.
    """

    with PYPROJECT.open("rb") as file:
        return tomllib.load(file)


def framework_config() -> dict:
    """
    Restituisce la configurazione del framework.

    Esempio:

        [tool.framework]
        repository = "https://github.com/SottoPoppa/framework"
        version = "main"
    """

    config = load_config()

    try:
        return config["tool"]["framework"]

    except KeyError as exc:
        raise RuntimeError(
            "Configurazione [tool.framework] "
            "non trovata in pyproject.toml."
        ) from exc


# ============================================================
# DEPENDENCIES
# ============================================================

def setup_core_dependencies():
    """
    Installa il progetto in editable mode.
    """

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-e",
            str(ROOT),
        ],
        check=True,
    )


# ============================================================
# FRAMEWORK DOWNLOAD
# ============================================================

def framework_url() -> str:
    """
    Costruisce l'URL dell'archivio GitHub del framework.
    """

    config = framework_config()

    repository = config["repository"].rstrip("/")
    version = str(config["version"])

    if version in ("main", "master"):
        reference = f"heads/{version}"
    else:
        reference = f"tags/{version}"

    return (
        f"{repository}/archive/refs/"
        f"{reference}.zip"
    )


def download_framework() -> bytes:
    """
    Scarica l'archivio del framework.
    """

    config = framework_config()

    print(
        f"[*] Download framework "
        f"{config['version']}..."
    )

    request = urllib.request.Request(
        framework_url(),
        headers={
            "User-Agent": "SottoPoppa-Framework",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=60,
    ) as response:
        return response.read()


# ============================================================
# FRAMEWORK INSTALL / UPDATE
# ============================================================

def install_framework():
    """
    Installa o aggiorna:

        src/framework/
        src/infrastructure/

    Non modifica:

        src/application/
        public/
        pyproject.toml
    """

    archive = download_framework()

    with tempfile.TemporaryDirectory() as temp:

        temp_path = Path(temp)

        with zipfile.ZipFile(
            io.BytesIO(archive)
        ) as zip_file:

            zip_file.extractall(temp_path)

        roots = [
            path
            for path in temp_path.iterdir()
            if path.is_dir()
        ]

        if len(roots) != 1:
            raise RuntimeError(
                "Archivio del framework non valido."
            )

        framework_root = roots[0]
        source = framework_root / "src"

        if not (
            source / "framework"
        ).is_dir():
            raise RuntimeError(
                "Il framework non contiene "
                "src/framework/."
            )

        if not (
            source / "infrastructure"
        ).is_dir():
            raise RuntimeError(
                "Il framework non contiene "
                "src/infrastructure/."
            )

        SRC.mkdir(
            parents=True,
            exist_ok=True,
        )

        for name in (
            "framework",
            "infrastructure",
        ):
            source_dir = source / name
            target_dir = SRC / name

            if target_dir.exists():
                shutil.rmtree(target_dir)

            shutil.copytree(
                source_dir,
                target_dir,
            )

            print(
                f"[✓] src/{name}/ aggiornato."
            )

    print(
        "[✓] Framework pronto."
    )


# ============================================================
# FRAMEWORK
# ============================================================

def framework_installed() -> bool:
    """
    Controlla se il framework è presente.
    """

    return (
        SRC / "framework"
        / "manager"
        / "loader.py"
    ).is_file()


def get_loader():
    """
    Importa e restituisce il Loader.
    """

    if not framework_installed():
        raise RuntimeError(
            "Framework non installato.\n\n"
            "Esegui:\n\n"
            "    python public/main.py --setup"
        )

    from framework.manager.loader import Loader

    return Loader()


# ============================================================
# APPLICATION
# ============================================================

async def run_framework(config: dict):

    loader_instance = get_loader()

    # --------------------------------------------------------
    # INSTALL
    # --------------------------------------------------------

    if config.get("install"):
        await loader_instance.install(config)
        return

    # --------------------------------------------------------
    # VERIFY
    # --------------------------------------------------------

    if config.get("verify"):
        return await loader_instance.verify_contracts(
            config
        )

    # --------------------------------------------------------
    # BOOTSTRAP
    # --------------------------------------------------------

    app = await loader_instance.bootstrap(
        config
    )

    try:

        # ----------------------------------------------------
        # TEST
        # ----------------------------------------------------

        if config.get("test") is not None:
            return await loader_instance.run_tests(
                config.get("test")
            )

        # ----------------------------------------------------
        # APPLICATION
        # ----------------------------------------------------

        await app.startup()

    except Exception as e:

        print(
            f"[!] Errore critico: {e}"
        )

        return False

    finally:

        await app.shutdown()


# ============================================================
# COMMANDS
# ============================================================

async def main(config: dict):

    # --------------------------------------------------------
    # SETUP
    # --------------------------------------------------------

    if config.get("setup"):

        setup_core_dependencies()

        install_framework()

        return

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    if config.get("update"):

        install_framework()

        return

    # --------------------------------------------------------
    # NORMAL FRAMEWORK EXECUTION
    # --------------------------------------------------------

    return await run_framework(
        config
    )


# ============================================================
# CLI
# ============================================================

def parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Avvia SottoPoppa Framework."
        )
    )

    parser.add_argument(
        "--config",
        type=str,
        default="pyproject.toml",
        help=(
            "Percorso del file di configurazione "
            "(default: pyproject.toml)"
        ),
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Abilita la modalità debug",
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help="Abilita la modalità dev",
    )

    parser.add_argument(
        "--install",
        action="store_true",
        help=(
            "Installa le dipendenze "
            "del framework"
        ),
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help=(
            "Verifica i contract in modalità "
            "strict senza avviare l'applicazione"
        ),
    )

    parser.add_argument(
        "--test",
        nargs="?",
        const="",
        default=None,
        metavar="FILTER",
        help=(
            "Esegue i test del framework. "
            "Filtro opzionale."
        ),
    )

    parser.add_argument(
        "--setup",
        action="store_true",
        help=(
            "Prepara l'ambiente e installa "
            "il framework"
        ),
    )

    parser.add_argument(
        "--update",
        action="store_true",
        help=(
            "Aggiorna framework e infrastructure"
        ),
    )

    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help=(
            "Bypassa il controllo "
            "'codice testato' degli adapter"
        ),
    )

    return parser


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    args = parser().parse_args()

    try:

        result = asyncio.run(
            main(vars(args))
        )

        if result is False:
            sys.exit(1)

    except KeyboardInterrupt:

        print(
            "\n[!] Operazione interrotta."
        )

        sys.exit(130)

    except Exception as exc:

        print(
            f"\n[!] {exc}"
        )

        sys.exit(1)