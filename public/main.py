import sys
import os
import asyncio
import argparse

# Setup del path
cwd = os.getcwd()
sys.path.insert(1, cwd + '/src')

from framework.manager.loader import Loader


async def main(config):
    loader_instance = Loader()

    if config.get('install'):
        await loader_instance.install(config)
        return

    # Usa il parametro passato dal terminale
    app = await loader_instance.bootstrap(config)

    try:
        if config.get('test') is not None:
            await loader_instance.run_tests(config.get('test'))
            return

        await app.startup()
    except Exception as e:
        print(f"[!] Errore critico: {e}")
    finally:
        await app.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Avvia il framework con una configurazione specifica.")

    parser.add_argument(
        "--config",
        type=str,
        default="pyproject.toml",
        help="Percorso del file di configurazione (default: pyproject.toml)"
    )

    parser.add_argument("--debug", action="store_true", help="Abilita la modalità debug")
    parser.add_argument("--dev", action="store_true", help="Abilita la modalità dev")
    parser.add_argument("--install", action="store_true", help="Installa le dipendenze del framework")
    parser.add_argument(
        "--test",
        nargs="?",         # opzionale: accetta un valore oppure None se assente
        const="",          # se --test è dato senza valore: ""  (= tutto)
        default=None,      # se --test non è dato: None
        metavar="FILTER",
        help="Esegue i test del framework. Filtro opzionale es: services, managers, infrastructure/message"
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Bypassa il controllo 'codice testato' degli adapter all'avvio (usare con cautela)"
    )

    args = parser.parse_args()
    args_dict = vars(args)

    asyncio.run(main(args_dict))