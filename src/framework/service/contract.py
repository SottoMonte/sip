import os
import framework.service.introspection as introspection
from pathlib import Path
import json

class Contract:
    """Gestione dei contratti (*.contract.json / *.json) associati a un
    qualunque file sorgente — non solo adapter: manager, service, port, ecc.

    Un contratto ha due responsabilità:
    1. dichiarare le dipendenze pip del componente (`requires`), quando
       presenti (tipicamente solo negli adapter, usato da Loader.install());
    2. certificare, componente per componente, che il codice in esecuzione
       è quello che ha superato i test — struttura:

        "hashes": {
          "Port": {
            "initialize": {"test": "<hash al momento del test>", "production": "<hash attuale>"},
            "close":      {"test": "...", "production": "..."}
          },
          "una_funzione_top": {"test": "...", "production": "..."}
        }

       I metodi di classe sono annidati sotto il nome della classe
       ('Port' → 'initialize'); le funzioni a livello di modulo, non
       avendo una classe sotto cui stare, restano piatte alla radice
       (vedi Reflection.module_components).
       Se un componente cambia dopo essere stato testato, il suo hash
       `production` non combacia più con `test` → al boot risulta stale.

    Un file senza contratto accanto non viene mai verificato: il contratto
    è opt-in, si applica a QUALSIASI file — non solo agli adapter.
    """

    @staticmethod
    def for_source(source_path: str) -> str:
        """Deriva il percorso del contratto da un file sorgente .py.
        Preferisce '<file>.contract.json', ripiega su '<file>.json'."""
        base, _ = os.path.splitext(source_path)
        contract, legacy = f"{base}.contract.json", f"{base}.json"
        if os.path.exists(contract):
            return contract
        return legacy if os.path.exists(legacy) else contract

    @staticmethod
    def read(path: str) -> dict:
        if not os.path.exists(path):
            return {}
        try:
            content = Path(path).read_text(encoding="utf-8").strip()
            return json.loads(content) if content else {}
        except Exception as e:
            print(f"[!] Errore lettura contratto '{path}': {e}")
            return {}

    @staticmethod
    def write(path: str, data: dict) -> None:
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _entry(hashes: dict, name: str) -> dict:
        """Ritorna il dict {test, production} per un componente, annidando
        sotto il nome della classe quando `name` è 'ClasseName.metodo'."""
        if "." in name:
            cls_name, method_name = name.split(".", 1)
            return hashes.setdefault(cls_name, {}).setdefault(method_name, {})
        return hashes.setdefault(name, {})

    @staticmethod
    def record_tested(source_path: str, component_hashes: dict[str, str]) -> None:
        """Chiamato dal tester quando i test relativi a specifici componenti
        (metodi o funzioni) passano. `component_hashes`: {nome: hash_sorgente}.
        Non richiede che esista già un contratto: se manca lo crea."""
        if not component_hashes:
            return
        path = Contract.for_source(source_path)
        contract = Contract.read(path)
        hashes = contract.setdefault("hashes", {})
        for name, component_hash in component_hashes.items():
            Contract._entry(hashes, name)["test"] = component_hash
        Contract.write(path, contract)

    @staticmethod
    def verify_module(source_path: str, module, strict: bool) -> bool:
        """Chiamato al caricamento di qualunque componente: se esiste un
        contratto accanto al file, verifica ogni suo componente pubblico
        (metodi di classi + funzioni di modulo) contro l'hash registrato al
        momento del test. Aggiorna `production` come traccia di audit.

        Nessun contratto presente → nessuna verifica, ritorna True subito.
        """
        contract_path = Contract.for_source(source_path)
        if not os.path.exists(contract_path):
            return True

        components = introspection.Reflection.module_components(module)
        if not components:
            return True

        contract = Contract.read(contract_path)
        hashes = contract.setdefault("hashes", {})

        stale = []
        for name, source in components.items():
            current = introspection.Reflection.hash_text(source)
            entry = Contract._entry(hashes, name)
            tested = entry.get("test")
            entry["production"] = current
            if tested is None or tested != current:
                stale.append(name)

        Contract.write(contract_path, contract)

        if stale:
            print(f"[!] '{source_path}': componenti non testati o modificati dopo l'ultimo test: {', '.join(stale)}")
        else:
            print(f"[✓] '{source_path}': tutti i componenti testati e verificati.")

        if strict and stale:
            raise RuntimeError(
                f"Avvio bloccato: '{source_path}' ha componenti non testati/modificati: "
                f"{', '.join(stale)} (usa --dev, --test o --skip-verify per bypassare)."
            )
        return not stale