import os

import framework.service.diagnostic as diagnostic

# Alias abbreviati → percorso src relativo
_FILTER_ALIASES: dict[str, str] = {
    "managers":        "src/framework/manager",
    "ports":           "src/framework/port",
    "services":        "src/framework/service",
    "infrastructure":  "src/infrastructure",
}


def resolve_filter(raw: str | None) -> str | None:
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


class tester:
    def __init__(self, filter_value: str | None = None, loader=None, defender=None,
                 messenger=None, executor=None, **_ignored):
        self.loader    = loader
        self.defender  = defender
        self.messenger = messenger
        self.executor  = executor
        self.prefix    = resolve_filter(filter_value)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _matches_filter(self, path: str) -> bool:
        """True se il file deve essere eseguito dato il filtro attivo."""
        if self.prefix is None:
            return True
        return path.replace('\\', '/').startswith(self.prefix.replace('\\', '/'))

    # ── lifecycle ─────────────────────────────────────────────────────────────

    async def start(self):
        return self.run()

    async def run(self, **constants):
        label = self.prefix or 'tutti'
        diagnostic.log("INFO", f"Avvio esecuzione suite di test… filtro: {label}", emoji="🧪")

        interp = language.Interpreter()
        await interp.start()
        await interp.create_session("tester", env=language.DSL_FUNCTIONS | {'resource': self.loader.resource})

        for root, _, files in os.walk('./src'):
            for file in files:
                if not file.endswith('.test.dsl'):
                    continue
                path = os.path.join(root, file).replace('./', '')
                if not self._matches_filter(path):
                    continue
                print(path)
                res    = await self.loader.resource(path)
                source = flow.value_of(res) if flow.is_result(res) else res
                await interp.add_file(path, source)
                outcome = await self.dsl(interp, path)
                self.loader.record_contract(path, outcome)

    async def dsl(self, interp, path):
        # ── esecuzione ────────────────────────────────────────────────────────
        ctx = await interp.run_session(
            "tester", path,
            env={'loader': self.loader, 'executor': self.executor,
                 'messenger': self.messenger, 'defender': self.defender,
                 'resource': self.loader.resource},
        )

        # ── esecuzione test suite ─────────────────────────────────────────────
        test_suite = ctx.get('test_suite', []) or []
        if isinstance(test_suite, dict):
            test_suite = [test_suite]

        results = {"total": 0, "passed": 0, "failed": 0, "errors": [], "details": []}

        for i, test in enumerate(test_suite):
            if not isinstance(test, dict):
                continue
            results["total"] += 1
            target   = test.get('action')
            args     = test.get('inputs', ())
            expected = test.get('outputs')
            assert_  = test.get('assert')

            try:
                if isinstance(args, dict):
                    received = await interp.invoke(target, [], args)
                elif isinstance(args, (list, tuple)):
                    received = await interp.invoke(target, args)
                else:
                    received = await interp.invoke(target, [args])

                ok = assert_(received=received, expected=expected)
                results["passed" if ok else "failed"] += 1
                status = "OK" if ok else "FAIL"
                detail = {"target": target, "status": status}
                if not ok:
                    detail |= {"expected": expected, "received": received}
                results["details"].append(detail)

                if ok:
                    diagnostic.log("INFO", f"OK - Test N.{i}: {test['note']}", emoji="✅")
                else:
                    diagnostic.log("WARNING", f"FAIL - Test N.{i}: {test['note']}",
                                    affirmed=assert_, expected=expected,
                                    received=received, emoji="❌")

            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"target": target, "error": str(e)})
                results["details"].append({"target": target, "status": "ERROR", "message": str(e)})
                diagnostic.log("ERROR", f"Test N.{i}: ERROR", error=str(e), emoji="⚠️")

        status = "PASSED" if results["failed"] == 0 else "FAILED"
        diagnostic.log("INFO", f"DSL Test {path or 'Inline'}: {status}",
                        total=results["total"], passed=results["passed"],
                        failed=results["failed"])

        return {"success": results["failed"] == 0, "data": results}