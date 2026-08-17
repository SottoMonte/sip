from __future__ import annotations

import argparse
import asyncio
import io
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
FRAMEWORK_ROOT = SRC_ROOT / "framework"
INFRASTRUCTURE_ROOT = SRC_ROOT / "infrastructure"
PYPROJECT = PROJECT_ROOT / "pyproject.toml"


FRAMEWORK_CONFIG_SECTION = ("tool", "sottopoppa", "framework")

MANAGED_DIRECTORIES = (
    FRAMEWORK_ROOT,
    INFRASTRUCTURE_ROOT,
)


def print_header():
    print()
    print("=" * 60)
    print(" SottoPoppa Framework")
    print("=" * 60)
    print()


def load_pyproject() -> dict:
    if not PYPROJECT.exists():
        raise RuntimeError(
            f"pyproject.toml non trovato: {PYPROJECT}"
        )

    try:
        return tomllib.loads(
            PYPROJECT.read_text(encoding="utf-8")
        )
    except Exception as exc:
        raise RuntimeError(
            f"Impossibile leggere pyproject.toml: {exc}"
        ) from exc


def get_framework_config() -> dict:
    config = load_pyproject()

    try:
        framework = (
            config["tool"]
            ["sottopoppa"]
            ["framework"]
        )
    except KeyError as exc:
        raise RuntimeError(
            "Configurazione framework mancante in pyproject.toml.\n\n"
            "Aggiungi:\n\n"
            "[tool.sottopoppa.framework]\n"
            'repository = "https://github.com/SottoPoppa/framework"\n'
            'version = "main"'
        ) from exc

    repository = framework.get("repository")
    version = framework.get("version")

    if not repository:
        raise RuntimeError(
            "tool.sottopoppa.framework.repository non configurato."
        )

    if not version:
        raise RuntimeError(
            "tool.sottopoppa.framework.version non configurato."
        )

    return {
        "repository": repository.rstrip("/"),
        "version": str(version),
    }


def normalize_repository_url(repository: str) -> str:
    repository = repository.rstrip("/")

    if repository.endswith(".git"):
        repository = repository[:-4]

    return repository


def framework_archive_url(
    repository: str,
    version: str,
) -> str:
    repository = normalize_repository_url(repository)

    if version in ("main", "master"):
        return (
            f"{repository}/archive/refs/heads/"
            f"{version}.zip"
        )

    return (
        f"{repository}/archive/refs/tags/"
        f"{version}.zip"
    )


def download_framework(
    repository: str,
    version: str,
) -> bytes:
    url = framework_archive_url(
        repository,
        version,
    )

    print(f"[*] Download framework")
    print(f"    Repository : {repository}")
    print(f"    Version    : {version}")
    print(f"    URL        : {url}")
    print()

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SottoPoppa-Framework",
            "Accept": "application/zip",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=60,
        ) as response:
            return response.read()

    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError(
                f"Framework '{version}' non trovato.\n"
                f"Controlla branch/tag nella repository:\n"
                f"{repository}"
            ) from exc

        raise RuntimeError(
            f"Errore HTTP durante il download del framework: "
            f"{exc.code}"
        ) from exc

    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Impossibile raggiungere la repository del framework: "
            f"{exc.reason}"
        ) from exc


def safe_extract_zip(
    archive_data: bytes,
    destination: Path,
) -> Path:
    temporary_root = Path(
        tempfile.mkdtemp(
            prefix="sottopoppa-framework-"
        )
    )

    archive_path = temporary_root / "framework.zip"

    try:
        archive_path.write_bytes(archive_data)

        with zipfile.ZipFile(
            archive_path,
            "r",
        ) as archive:

            members = archive.namelist()

            if not members:
                raise RuntimeError(
                    "L'archivio del framework è vuoto."
                )

            for member in members:
                member_path = Path(member)

                if member_path.is_absolute():
                    raise RuntimeError(
                        f"Archivio non sicuro: {member}"
                    )

                target = (
                    temporary_root
                    / member_path
                ).resolve()

                if (
                    temporary_root.resolve()
                    not in target.parents
                    and target != temporary_root.resolve()
                ):
                    raise RuntimeError(
                        f"Archivio non sicuro: {member}"
                    )

            archive.extractall(
                temporary_root
            )

        directories = [
            path
            for path in temporary_root.iterdir()
            if path.is_dir()
        ]

        if len(directories) != 1:
            raise RuntimeError(
                "Formato archivio framework non riconosciuto."
            )

        return directories[0]

    except Exception:
        shutil.rmtree(
            temporary_root,
            ignore_errors=True,
        )
        raise


def find_framework_source(
    extracted_root: Path,
) -> Path:
    src = extracted_root / "src"

    if not src.is_dir():
        raise RuntimeError(
            "La repository del framework non contiene "
            "la directory src/."
        )

    framework = src / "framework"
    infrastructure = src / "infrastructure"

    if not framework.is_dir():
        raise RuntimeError(
            "La repository del framework non contiene "
            "src/framework/."
        )

    if not infrastructure.is_dir():
        raise RuntimeError(
            "La repository del framework non contiene "
            "src/infrastructure/."
        )

    return extracted_root


def replace_managed_directory(
    source: Path,
    destination: Path,
):
    if destination.exists():
        shutil.rmtree(destination)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copytree(
        source,
        destination,
    )


def install_framework(
    repository: str,
    version: str,
):
    print_header()

    archive_data = download_framework(
        repository,
        version,
    )

    extracted_root = None

    try:
        extracted_root = safe_extract_zip(
            archive_data,
            PROJECT_ROOT,
        )

        find_framework_source(
            extracted_root
        )

        source_src = extracted_root / "src"

        print("[*] Installazione framework...")

        replace_managed_directory(
            source_src / "framework",
            FRAMEWORK_ROOT,
        )

        replace_managed_directory(
            source_src / "infrastructure",
            INFRASTRUCTURE_ROOT,
        )

        print(
            "[✓] src/framework/ aggiornato."
        )

        print(
            "[✓] src/infrastructure/ aggiornato."
        )

    finally:
        if extracted_root is not None:
            shutil.rmtree(
                extracted_root,
                ignore_errors=True,
            )

        parent = (
            extracted_root.parent
            if extracted_root
            else None
        )

        if parent and parent.exists():
            shutil.rmtree(
                parent,
                ignore_errors=True,
            )

    print()
    print("[✓] Framework installato.")
    print()


def framework_installed() -> bool:
    return (
        FRAMEWORK_ROOT.is_dir()
        and (
            FRAMEWORK_ROOT
            / "manager"
            / "loader.py"
        ).is_file()
        and INFRASTRUCTURE_ROOT.is_dir()
    )


def run_setup():
    if framework_installed():
        print(
            "[!] Framework già presente."
        )
        print(
            "    Usa --update per aggiornarlo."
        )
        return True

    config = get_framework_config()

    install_framework(
        config["repository"],
        config["version"],
    )

    return True


def run_update():
    config = get_framework_config()

    if not framework_installed():
        print(
            "[*] Framework non installato."
        )
        print(
            "[*] Eseguo automaticamente il setup..."
        )
        print()

    install_framework(
        config["repository"],
        config["version"],
    )

    return True


def setup_core_dependencies():
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-e",
            str(PROJECT_ROOT),
        ],
        check=True,
    )


async def run_framework(config: dict):
    if not framework_installed():
        print(
            "[!] Framework non installato."
        )
        print(
            "[*] Esegui:"
        )
        print()
        print(
            "    python public/main.py --setup"
        )
        print()
        return False

    sys.path.insert(
        0,
        str(SRC_ROOT),
    )

    from framework.manager.loader import Loader

    loader = Loader()

    if config.get("install"):
        return await loader.install(config)

    if config.get("verify"):
        return await loader.verify_contracts(
            config
        )

    app = await loader.bootstrap(
        config
    )

    try:
        if config.get("test") is not None:
            return await loader.run_tests(
                config.get("test")
            )

        await app.startup()

    except Exception as exc:
        print(
            f"[!] Errore critico: {exc}"
        )
        return False

    finally:
        await app.shutdown()

    return True


async def main(config: dict):
    if config.get("setup"):
        return run_setup()

    if config.get("update"):
        return run_update()

    return await run_framework(
        config
    )


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "SottoPoppa Framework"
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
        "--setup",
        action="store_true",
        help=(
            "Scarica e installa il framework."
        ),
    )

    parser.add_argument(
        "--update",
        action="store_true",
        help=(
            "Aggiorna framework e infrastructure "
            "dal repository configurato."
        ),
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Abilita la modalità debug.",
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help="Abilita la modalità dev.",
    )

    parser.add_argument(
        "--install",
        action="store_true",
        help=(
            "Installa le dipendenze "
            "dichiarate dal framework."
        ),
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help=(
            "Verifica i contract senza "
            "avviare l'applicazione."
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
        "--skip-verify",
        action="store_true",
        help=(
            "Bypassa il controllo "
            "'codice testato'."
        ),
    )

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = asyncio.run(
            main(vars(args))
        )

        if result is False:
            sys.exit(1)

    except KeyboardInterrupt:
        print()
        print("[!] Operazione interrotta.")

        sys.exit(130)

    except Exception as exc:
        print()
        print(
            f"[!] {exc}"
        )

        sys.exit(1)