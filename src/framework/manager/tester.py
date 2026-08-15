import os
import uuid
from typing import Optional

import framework.service.diagnostic as diagnostic
import framework.service.language as language
import framework.service.flow as flow
import framework.manager.loader as loader_module


# Alias abbreviati → percorso src relativo
_FILTER_ALIASES: dict[str, str] = {
    "managers":        "src/framework/manager",
    "ports":           "src/framework/port",
    "services":        "src/framework/service",
    "infrastructure":  "src/infrastructure",
}


def resolve_filter(raw: str | None) -> Optional[str]:
    """Ritorna il prefisso di percorso su cui filtrare, o None (tutto).

    Esempi di input → output:
        managers                      → src/framework/manager
        managers/defender             → src/framework/manager/defender
        ports                         → src/framework/port
        infrastructure                → src/infrastructure
        infrastructure/authentication → src/infrastructure/authentication
        src/qualunque/percorso        → src/qualunque/percorso  (raw)
    """
    if not raw:
        return None
    # 1) Alias esatto  →  managers
    if raw in _FILTER_ALIASES:
        return _FILTER_ALIASES[raw]
    # 2) Alias + sub   →  managers/defender  oppure  infrastructure/authentication
    for alias, base in _FILTER_ALIASES.items():
        if raw.startswith(alias + '/'):
            return f"{base}/{raw[len(alias) + 1:]}"
    # 3) Percorso src diretto (fallback)
    return raw


class Manager:
    def __init__(self, loader: loader_module.Loader, **constants):
        """Inizializza il Manager per l'esecuzione dei test DSL.
        
        :param loader: Il Loader del framework (dipendenza iniettata)
        :param constants: Configurazioni aggiuntive (incluso filtro da CLI)
        """
        self.loader = loader
        self.filter_raw = constants.get('filter', None)
        self.prefix = resolve_filter(self.filter_raw)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _matches_filter(self, path: str) -> bool:
        """True se il file deve essere eseguito dato il filtro attivo."""
        if self.prefix is None:
            return True
        return path.replace('\\', '/').startswith(self.prefix.replace('\\', '/'))

    # ── lifecycle ─────────────────────────────────────────────────────────────
    
    async def startup(self, session=None):
        """Hook di startup (nessuna logica richiesta per il tester)."""
        pass
    
    async def shutdown(self, session=None):
        """Hook di shutdown (nessuna logica richiesta per il tester)."""
        pass

    async def run(self, **constants):
        """Esegue la suite di test DSL filtrata secondo il prefisso configurato."""
        filter_raw = constants.get('filter', self.filter_raw)
        self.filter_raw = filter_raw
        self.prefix = resolve_filter(filter_raw)
        label = self.prefix or 'tutti'
        diagnostic.log("INFO", f"Avvio esecuzione suite di test… filtro: {label}", emoji="🧪")

        interp = language.Interpreter()
        await interp.start()

        for root, _, files in os.walk('./src'):
            for file in files:
                if not file.endswith('.test.dsl'):
                    continue
                path = os.path.join(root, file).replace('./', '')
                if not self._matches_filter(path):
                    continue
                diagnostic.log("INFO", f"Esecuzione test: {path}", emoji="🔍")
                
                try:
                    res = await self.loader.resource(path)
                    source = flow.value_of(res) if flow.is_result(res) else res
                    await interp.load_file(path, source)
                    outcome = await self._execute_dsl(interp, path)
                    self.loader.record_contract(path, outcome)
                except Exception as e:
                    diagnostic.log("ERROR", f"Errore durante l'esecuzione di {path}: {e}", emoji="⚠️")
                    self.loader.record_contract(path, {"success": False, "data": {"error": str(e)}})

    async def _execute_dsl(self, interp: language.Interpreter, path: str) -> dict:
        """Esegue una suite di test DSL e registra i risultati.
        
        :param interp: L'interprete DSL
        :param path: Percorso del file .test.dsl
        :return: Dizionario con esito e dettagli dei test
        """
        # Crea una sessione per questo test
        session_id = str(uuid.uuid4())
        session_dict = {
            'id': session_id,
            'errors': [],
            'providers': {},
            'user': {'id': 'tester', 'role': 'system'}
        }
        
        # Registra la sessione nel runner
        interp.session_create(
            sid=session_id,
            env=language.DSL_FUNCTIONS | {
                'resource': self.loader.resource,
                'import': self.loader.import_module
            }
        )
        
        # Crea la SessionHandle
        session = language.SessionHandle(interp, session=session_dict)
        
        # Esegui il file DSL sulla sessione
        try:
            ctx = await session.run(path)
        except Exception as e:
            diagnostic.log("ERROR", f"Errore durante l'esecuzione del file DSL {path}: {e}", emoji="⚠️")
            return {"success": False, "data": {"error": str(e)}}
        
        # ── estrazione della suite di test ────────────────────────────────
        test_suite = ctx.get('test_suite', []) or []
        if isinstance(test_suite, dict):
            test_suite = [test_suite]
        
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
            "details": []
        }
        
        # ── esecuzione di ogni test ───────────────────────────────────────
        for i, test in enumerate(test_suite):
            if not isinstance(test, dict):
                continue
            
            results["total"] += 1
            target = test.get('action')
            args = test.get('inputs', ())
            expected = test.get('outputs')
            assert_fn = test.get('assert')
            test_note = test.get('note', f'Test #{i}')
            
            try:
                # Invoca l'azione target con gli argomenti forniti
                if isinstance(args, dict):
                    received = await interp.call(target, (), args)
                elif isinstance(args, (list, tuple)):
                    received = await interp.call(target, args)
                else:
                    received = await interp.call(target, (args,))
                
                # Valuta l'assertion
                ok = await interp.call(assert_fn, (), {"received": received, "expected": expected})
                results["passed" if ok else "failed"] += 1
                status = "OK" if ok else "FAIL"
                detail = {"target": str(target), "status": status, "note": test_note}
                
                if not ok:
                    detail |= {"expected": expected, "received": received}
                
                results["details"].append(detail)
                
                if ok:
                    diagnostic.log("INFO", f"OK - Test N.{i}: {test_note}", emoji="✅")
                else:
                    diagnostic.log(
                        "WARNING",
                        f"FAIL - Test N.{i}: {test_note}",
                        expected=expected,
                        received=received,
                        emoji="❌"
                    )
            
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"target": str(target), "error": str(e), "test_note": test_note})
                results["details"].append({
                    "target": str(target),
                    "status": "ERROR",
                    "message": str(e),
                    "note": test_note
                })
                diagnostic.log("ERROR", f"Test N.{i}: ERROR - {test_note}", error=str(e), emoji="⚠️")
        
        # ── riepilogo dei risultati ───────────────────────────────────────
        status = "PASSED" if results["failed"] == 0 else "FAILED"
        diagnostic.log(
            "INFO",
            f"DSL Test {path}: {status}",
            total=results["total"],
            passed=results["passed"],
            failed=results["failed"],
            emoji="📊"
        )
        
        # Chiudi la sessione
        await session.close()
        
        return {"success": results["failed"] == 0, "data": results}