import os, sys, inspect, json, uuid, ast, types, asyncio, signal, hashlib
from typing import Any, Type, Optional, Iterator
from graphlib import TopologicalSorter
from collections import defaultdict
from pathlib import Path
from jinja2 import Environment, BaseLoader
import tomli
from dataclasses import dataclass, field

@dataclass
class Resource:
    name: str
    path: str
    module: any = None
    kind: str = None
    config: dict = field(
        default_factory=dict
    )
    extend: dict = field(
        default_factory=dict
    )

class Handle:
    def __init__(self, obj=None):
        # Usiamo un dizionario interno dedicato per lo stato dell'Handle
        super().__setattr__('_state', {})
        super().__setattr__('obj', None)
        if obj is not None:
            self.swap(obj)
        self.init = True

    def swap2(self, obj):
        # Salva il nuovo oggetto
        super().__setattr__('obj', obj)
        if obj is not None:
            # Sincronizza lo stato salvato finora nell'Handle dentro il nuovo obj
            for key, value in self._state.items():
                setattr(obj, key, value)

    def swap(self,obj):

        old = self.obj

        if old is not None and obj is not None:
            for key,value in old.__dict__.items():
                if key not in ("__dict__",):
                    setattr(obj,key,value)

        super().__setattr__('obj',obj)

    def __getattr__(self, name):
        if name in ('obj', '_state'):
            return super().__getattribute__(name)
        return getattr(self.obj, name)

    def __setattr__(self, name, value):
        if name in ('obj', '_state'):
            super().__setattr__(name, value)
        else:
            # 1. Salva lo stato nell'Handle per non perderlo
            self._state[name] = value
            # 2. Aggiorna anche l'oggetto corrente (se esiste)
            if self.obj is not None:
                setattr(self.obj, name, value)

    def __repr__(self):
        if self.obj is None:
            return "<Handle object (empty)>"
        return str(self.obj).replace('.Manager', '.Manager.Handle')

class Infrastructure:
    """TOML, JSON, Jinja, schemi, risorse."""

    def __init__(self):
        self.jinja_env = Environment(loader=BaseLoader())
        self.jinja_env.filters.setdefault('tojson', json.dumps)
        self.jinja_env.globals['uuid4'] = lambda: str(uuid.uuid4())

    async def load_schemes(self, directories: list) -> dict:
        raw = {}
        for d in directories:
            if not os.path.exists(d):
                continue
            for f in os.listdir(d):
                if not f.endswith('.json'):
                    continue
                try:
                    raw[f[:-5]] = json.load(open(os.path.join(d, f), encoding='utf-8'))
                except json.JSONDecodeError as e:
                    print(f"[!] JSON {f}: {e}")

        cache = {}

        def resolve(name: str) -> Any:
            if name in cache: return cache[name]
            obj = raw.get(name)
            if obj is None: return None
            cache[name] = {}

            def _r(v):
                if isinstance(v, dict):  return {k: _r(x) for k, x in v.items()}
                if isinstance(v, list):  return [_r(x) for x in v]
                if isinstance(v, str) and '{{' in v:
                    s = v.strip()
                    if s.startswith('{{') and s.endswith('}}') and '|' not in s:
                        ref = s[2:-2].strip()
                        if ref in raw: return resolve(ref)
                        g = self.jinja_env.globals.get(ref); return g() if callable(g) else g
                    return self.jinja_env.from_string(v).render(**{**self.jinja_env.globals, **raw, **cache})
                return v

            cache[name] = _r(obj); return cache[name]

        final = {name: resolve(name) for name in raw}
        print(f"[+] Schemi: {', '.join(sorted(final))}" if final else "[!] Nessuno schema")
        return final

    async def resource(self, path) -> str:
        if str(path).startswith('application/'):
            path = 'src/' + path
        return open(path, 'rb').read().decode()

class Framework:
    """
    Kernel del framework (versione compatta e semplificata).

    Responsabilità:
    - Creare namespace dinamici
    - Caricare moduli Python ed eseguire verifiche contrattuali
    - Gestire componenti e dipendenze
    """

    def __init__(self):
        self.components = {}
        self.errors = []
        self.strict = False

    def _pkg(self, name: str):
        if not name:
            return None
        if name in sys.modules:
            return sys.modules[name]

        pkg = types.ModuleType(name)
        pkg.__path__ = []
        pkg.__package__ = name.rpartition(".")[0]
        sys.modules[name] = pkg

        if "." in name:
            parent, child = name.rsplit(".", 1)
            setattr(self._pkg(parent), child, pkg)

        return pkg

    def imports(self,code: str) -> list[str]:
        try:
            tree = ast.parse(code)
        except Exception:
            return []

        result = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result.add(alias.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    result.add(node.module)

        return list(result)

    async def load_module(self, name: str, path: str, extra: dict = None, force: bool = False):
        if name in sys.modules and not force:
            return sys.modules[name]

        self._pkg(name.rpartition(".")[0])
        module = types.ModuleType(name)
        module.__file__ = path

        if extra:
            module.__dict__.update(extra)

        sys.modules[name] = module

        if "." in name:
            pkg, short = name.rsplit(".", 1)
            setattr(self._pkg(pkg), short, module)

        try:
            code = Path(path).read_bytes()
            exec(compile(code, path, "exec"), module.__dict__)
        except Exception:
            sys.modules.pop(name, None)
            raise

        print(f"[+] {name}")
        return module

    async def add(self, resource, extra: dict = None):
        module = await self.load_module(resource.name, resource.path, extra)
        resource.module = module
        self.components[resource.name] = resource

        Contract.verify_module(resource.path, module, self.strict)
        print(f"[~] {resource.name}")
        return resource

    async def load(self, resource, extra_by_name: dict = None):
        extra_by_name = extra_by_name or {}
        short_name = resource.name.split(".")[-1]
        return await self.add(resource, extra_by_name.get(short_name))

    async def reload(self, resource):
        module = await self.load_module(
            resource.name, resource.path, resource.extend, force=True
        )
        resource.module = module
        print(f"[✓] Reload {resource.name}")
        return resource

    async def load_core(self, services: dict, ports: dict, extra_by_name: dict = None):
        extra_by_name = extra_by_name or {}
        modules = {**services, **ports}
        graph, pending = {}, {}

        for name, path in modules.items():
            ns_type = "service" if name in services else "port"
            namespace = f"framework.{ns_type}.{name}"
            pending[name] = Resource(name=namespace, path=path)

            imports = self.imports(Path(path).read_text())
            graph[name] = {x.split(".")[-1] for x in imports} & modules.keys()

        for name in TopologicalSorter(graph).static_order():
            resource = pending[name]
            short_name = resource.name.split(".")[-1]
            await self.add(resource, extra_by_name.get(short_name))
            print(f"[✓] Creato {resource.name}")

    def dependencies_from_class(self, target):
        hints = get_type_hints(target.__init__)
        signature = inspect.signature(target.__init__)
        deps = []

        for name, parameter in signature.parameters.items():
            if name == "self" or parameter.kind == inspect.Parameter.VAR_KEYWORD:
                continue

            annotation = hints.get(name)
            if annotation is None:
                continue

            args = get_args(annotation)
            deps.extend(args if args else [annotation])

        return {target: deps}

    def resolve_order(self, nodes, dependencies):
        graph = {node: set(dependencies.get(node, [])) for node in nodes}
        return list(TopologicalSorter(graph).static_order())

    def component(self, name: str):
        return self.components.get(name)

    def components_iter(self):
        return self.components.values()

    def components_ports(self):
        return [c for c in self.components.values() if c.name.startswith("framework.adapter.")]

    def resource_by_path(self, path: str):
        target_path = str(Path(path))
        return next((res for res in self.components.values() if str(Path(res.path)) == target_path), None)

    def check(self):
        if self.errors:
            raise RuntimeError("\n".join(self.errors))

class Application:
    """Manager del Ciclo di Vita Globale dell'App."""

    def __init__(self, loader, managers: list, session=None):
        self._loader = loader
        self._managers = managers
        self._stop_event = asyncio.Event()
        self._running_tasks: list = []
        self._session = session
        self._reload_lock = asyncio.Lock()

    async def _message_consumer_worker(self):
        try:
            while not self._stop_event.is_set():
                messenger = self._loader.get_managers().get('messenger')
                message = await messenger.read(self._session, domain="event")
                current_managers = self._loader.get_managers()
                for name, manager in list(current_managers.items()):
                    #print(manager)
                    if hasattr(manager, 'reload'):
                        try:
                            await manager.reload(self._session, message)
                        except Exception as e:
                            print(f"[!] Errore durante il reload in {name}: {e}")
        except asyncio.CancelledError:
            print("[*] Worker di messaggistica terminato.")

    async def startup(self) -> None:
        print("[*] Avvio dei manager del framework...")
        if self._loader.kwargs.get('dev'):
            self._running_tasks.append(asyncio.create_task(self._message_consumer_worker()))

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._stop_event.set)

        for manager in self._managers:
            if hasattr(manager, "startup"):
                res = await manager.startup(self._session)
                if res:
                    if isinstance(res, list):
                        for coro in res: self._running_tasks.append(asyncio.create_task(coro))
                    elif asyncio.iscoroutine(res) or inspect.isawaitable(res):
                        self._running_tasks.append(asyncio.create_task(res))

        print("[+] Framework completamente attivo. In ascolto...")
        await self._stop_event.wait()

    async def shutdown(self) -> None:
        print("\n[*] Spegnimento controllato dei servizi...")
        for manager in reversed(self._managers):
            if hasattr(manager, "shutdown"):
                await manager.shutdown(self._session)
        for task in self._running_tasks:
            if not task.done():
                task.cancel()
        print("[*] Framework spento correttamente.")

class Loader:
    """Orchestratore: Framework per discovery/reflection, Infrastructure per I/O, Container per la DI."""

    services = {
        'flow':     'src/framework/service/flow.py',
        'factory':  'src/framework/service/factory.py',
        'language': 'src/framework/service/language.py',
        'scheme':   'src/framework/service/scheme.py',
        'manage':   'src/framework/port/manage.py',
        'container': 'src/framework/service/container.py',
        'introspection': 'src/framework/service/introspection.py',
        'contract': 'src/framework/service/contract.py',
        'diagnostics': 'src/framework/service/diagnostics.py',
    }
    ports = {
        'message':      'src/framework/port/message.py',
        'presentation': 'src/framework/port/presentation.py',
        'persistence':  'src/framework/port/persistence.py',
        'network':      'src/framework/port/network.py',
    }
    managers = {
        'defender':      'src/framework/manager/defender.py',
        'messenger':     'src/framework/manager/messenger.py',
        'presenter':     'src/framework/manager/presenter.py',
        'storekeeper':   'src/framework/manager/storekeeper.py',
        'orchestrator':  'src/framework/manager/orchestrator.py',
        'networker':     'src/framework/manager/networker.py',
        'tester':        'src/framework/manager/tester.py',
    }

    def __init__(self):
        self.framework = Framework()
        self.infra = Infrastructure()
        self.container.put(Loader, self)
        self.handle = Handle(self)
        sys.modules['framework.loader'] = sys.modules[__name__]
        self.current_config: dict = {}
        self.kwargs: dict = {}

    def _port_interface(self, port_key: str) -> Optional[Type]:
        port_mod = sys.modules.get(f"framework.port.{port_key}")
        return getattr(port_mod, "Port", None) if port_mod else None

    async def _discover_adapters(self, config: dict) -> None:
        # La verifica del contratto (se presente) avviene automaticamente
        # in Framework.add() per ogni risorsa caricata: qui basta caricare.
        for port_key in self.ports:
            for adapter_name, adapter_config in config.get(port_key, {}).items():
                configs = adapter_config if isinstance(adapter_config, list) else [adapter_config]
                ns = f"framework.adapter.{port_key}.{adapter_name}"
                path = f"src/infrastructure/{port_key}/{adapter_name}.py"
                await self.framework.load(Resource(name=ns, path=path, kind="ADAPTER", config=configs))
    
    def _args(self, dependencies: dict) -> dict:
        lista = []
        for ann in dependencies:
            if ann.__module__.startswith("framework.port"):
                print(ann)
                lista.append(self.container.get_port(ann))
            else:
                if self.container.get(ann):
                    lista.append(self.container.get(ann))
        return lista

    def _build_manager(self, resource, save=True):
        manager_cls = resource.module.Manager

        deps = (
            self.framework
            .dependencies_from_class(manager_cls)
            .get(manager_cls, [])
        )

        args = self._args(deps)

        obj = Handle(
            manager_cls(*args, **(resource.config or {}))
        )

        if save:
            self.container.put(manager_cls, obj)

        return obj

    def _build_managers(self, resources) -> list:

        dependencies = {}
        managers = []

        # Discovery classi e dipendenze
        for resource in resources:

            manager = getattr(
                resource.module,
                "Manager",
                None
            )

            if manager is None:
                print(f"[!] Nessun Manager in {resource.name}")
                continue

            dependencies |= self.framework.dependencies_from_class(manager)

            managers.append(manager)


        # Ordinamento dependency graph
        order = self.framework.resolve_order(
            managers,
            dependencies
        )


        instances = []

        for manager_cls in order:

            if manager_cls not in managers:
                continue


            # caso Loader
            if (
                manager_cls.__module__ == "framework.loader"
                or "loader.Loader" in manager_cls.__qualname__
            ):
                self.container.put(
                    manager_cls,
                    self,
                    singleton=True
                )
                continue


            deps = dependencies.get(
                manager_cls,
                []
            )

            args = self._args(deps)


            # recupera config dal resource
            resource = next(
                (
                    r for r in resources
                    if r.module.Manager is manager_cls
                ),
                None
            )


            config = {}

            if resource:
                config = resource.config or {}


            obj_in = manager_cls(
                *args,
                **config
            )


            obj = Handle(obj_in)


            self.container.put(
                manager_cls,
                obj,
                singleton=True
            )


            instances.append(obj)


            print(
                f"[✓] Manager {manager_cls.__module__}.{manager_cls.__name__}"
            )


        return instances

    def _build_adapters(self, resources, save=True):
        created = []
        for resource in resources:

            parts = resource.name.split(".")

            if len(parts) < 4:
                continue


            port = parts[2]


            interface = self._port_interface(port)

            if interface is None:
                print(
                    f"[!] Porta non trovata: {port}"
                )
                continue


            adapter_cls = getattr(
                resource.module,
                "Adapter",
                None
            )


            if adapter_cls is None:
                print(
                    f"[!] Nessun Adapter in {resource.name}"
                )
                continue


            configs = resource.config

            if not isinstance(configs, list):
                configs = [configs]


            for config in configs:

                dependencies = (
                    self.framework
                    .dependencies_from_class(adapter_cls)
                    .get(adapter_cls, [])
                )


                args = self._args(
                    dependencies
                )


                obj_in = adapter_cls(
                    *args,
                    **config
                )


                obj = Handle(
                    obj_in
                )

                created.append(obj)

                if save:
                    self.container.add_port(interface,obj)


                print(
                    f"[✓] Adapter {adapter_cls.__name__} "
                    f"name={config.get('name')}"
                )
        return created

    async def reload(self, session, changed_path) -> bool:
        if changed_path.endswith('.py'):
            '''if '/infrastructure/' in changed_path:
                a = changed_path.split('/')
                for i,x in enumerate(a):
                    if x == "infrastructure":
                        index = i
                port = a[index+1]
                interface = f"framework.port.{port}.Port"
                adapters = self.container.get_port(interface)
                print(adapters)
                self.container.clear_port(interface)
                resource = self.framework.resource_by_path(changed_path)
                resource = await self.framework.reload(resource)
                self._build_adapters([resource])
                adapters = self.container.get_port(interface)
                print(adapters)
                return True'''
            if '/infrastructure/' in changed_path:
                port = changed_path.split("/")[changed_path.split("/").index("infrastructure")+1]
                interface = f"framework.port.{port}.Port"

                old_handles = self.container.get_port(interface)
                adapters = self.container.get_port(interface)
                print(adapters)
                resource = self.framework.resource_by_path(changed_path)
                await self.framework.reload(resource)

                new_handles = self._build_adapters([resource],False)

                for old, new in zip(old_handles, new_handles):
                    old.swap(new.obj)

                adapters = self.container.get_port(interface)
                print(adapters)
                return True

            elif '/framework/manager/' in changed_path:
                resource = self.framework.resource_by_path(changed_path)
                await self.framework.reload(resource)

                old = self.container.get(resource.name)

                new = self._build_manager(resource, save=False)

                old.swap(new.obj)

                self.container.remove(resource.name)
                self.container.put(resource.module.Manager, old)
            else:
                print("module",changed_path)

    async def load_schemes(self, directories: list) -> dict:
        return await self.infra.load_schemes(directories)

    async def resource(self, path) -> str:
        return await self.infra.resource(path)

    def file_dependencies(self, file_path: str, root: str = "src") -> list:
        return self.framework.reflection.file_dependencies(file_path, root)

    def record_contract(self, test_path: str, outcome: dict) -> None:
        """Aggiorna il contratto del sorgente corrispondente a `test_path` in
        base ai risultati dei test (l'`outcome` prodotto dal tester dopo
        l'esecuzione di un file .test.dsl).

        Convenzione: '<file>.test.dsl' testa '<file>.py' nella stessa
        cartella — vale per qualunque tipo di file, non solo adapter.
        Un componente (metodo di classe o funzione di modulo) viene marcato
        come testato solo se TUTTI i test che lo referenziano sono passati;
        un solo FAIL lo esclude. Il tester non conosce Contract/Reflection:
        gli basta passare i risultati grezzi, questo metodo fa il resto.
        """
        norm = test_path.replace('\\', '/')
        if not norm.endswith('.test.dsl'):
            return
        source_path = norm[:-len('.test.dsl')] + '.py'

        resource = self.framework.resource_by_path(source_path)
        if resource is None or resource.module is None:
            return

        available = Reflection.module_components(resource.module)
        if not available:
            return

        passed, failed = set(), set()
        for detail in outcome.get("data", {}).get("details", []):
            target = detail.get("target")
            if target is None:
                continue
            candidates = [str(target), str(target).rsplit(".", 1)[-1]]
            name = next((c for c in candidates if c in available), None)
            if name is None:
                continue
            (passed if detail["status"] == "OK" else failed).add(name)

        tested = passed - failed
        if not tested:
            return

        component_hashes = {name: Reflection.hash_text(available[name]) for name in tested}
        Contract.record_tested(source_path, component_hashes)
        print(f"[🔏] Contratto aggiornato: {source_path} → {', '.join(sorted(component_hashes))}")

    def get_managers(self) -> dict:
        result = {
            "loader": self.handle
        }

        for resource in self.framework.components_iter():

            # solo manager
            if not resource.name.startswith(
                "framework.manager."
            ):
                continue

            manager_cls = getattr(
                resource.module,
                "Manager",
                None
            )

            if manager_cls is None:
                continue

            obj = self.container.get(manager_cls)

            if obj:
                name = resource.name.split(".")[-1]
                result[name] = obj

        return result

    async def run_tests(self, filter_value: str | None = None):
        """Costruisce ed esegue la suite di test DSL, con lo stesso wiring
        (DI dei manager) usato per il resto del framework. Centralizza qui
        la conoscenza di come si costruisce un TesterManager, così i
        chiamanti (es. main.py) non devono duplicare la logica."""
        from framework.manager.tester import tester as TesterManager
        t = TesterManager(filter_value=filter_value, **self.get_managers())
        await t.run()
        return t

    async def bootstrap(self, config_toml_path: str) -> Application:
        # kwargs/strict impostati subito: load_core (services+ports), poco
        # sotto, carica componenti anch'essi soggetti a verifica contratto.
        self.kwargs = config_toml_path
        self.framework.strict = not (
            self.kwargs.get('dev')
            or self.kwargs.get('test') is not None
            or self.kwargs.get('skip_verify')
        )

        schemes = await self.load_schemes(["src/framework/scheme", "src/application/model"])

        await self.framework.load_core(
            self.services, self.ports,
            extra_by_name={"scheme": {"schemes": schemes, "jinja_env": self.infra.jinja_env}},
        )

        config = tomli.loads(open(config_toml_path['config'], "rb").read().decode())
        self.current_config = config

        print("\n[*] Discovery...")
        manager_resources = []

        for name, path in self.managers.items():

            resource = Resource(
                name=f"framework.manager.{name}",
                path=path,
                kind="MANAGER",
                config=config.get("manager", {}).get(name, {})
            )

            await self.framework.load(resource,)

            manager_resources.append(resource)

        await self._discover_adapters(config)


        print("\n[*] Build...")


        instances = self._build_managers(manager_resources)
        adapters = self._build_adapters(self.framework.componetes_ports())
        #print(self.container.get("framework.manager.messenger.Manager").providers)
        
        defender = self.container.get("framework.manager.defender.Manager")
        await defender.startup()
        session = await defender.session_create()
        print(f"[*] Sessione creata: {session}")

        app = Application(self.container, self, instances, session)
        self.app = app
        return app

    async def install(self, config_or_path: Any = "pyproject.toml") -> None:
        """
        Scansiona e installa SOLO le dipendenze e contratti degli adapter abilitati in pyproject.toml.
        """
        import subprocess

        if isinstance(config_or_path, dict):
            config_file = config_or_path.get('config', 'pyproject.toml')
        else:
            config_file = str(config_or_path)

        print(f"\n[*] Caricamento configurazione da '{config_file}'...")
        try:
            config = tomli.loads(open(config_file, "rb").read().decode())
        except Exception as e:
            print(f"[!] Errore nel caricare '{config_file}': {e}")
            return

        print("[*] Individuazione adapter abilitati in pyproject.toml...")
        enabled_adapters = []

        # Scansiona tutte le chiavi nel toml escluse 'project' e 'manager'
        for port_key, port_val in config.items():
            if port_key in ("project", "manager"):
                continue
            if isinstance(port_val, dict):
                for adapter_name in port_val.keys():
                    enabled_adapters.append((port_key, adapter_name))

        if not enabled_adapters:
            print("[*] Nessun adapter abilitato trovato in pyproject.toml.")
            return

        print(f"[*] Adapter abilitati attivi ({len(enabled_adapters)}):")
        for port_key, adapter_name in enabled_adapters:
            print(f"  - [{port_key}] {adapter_name}")

        contracts = []
        all_requires = set()

        for port_key, adapter_name in enabled_adapters:
            base_path = f"src/infrastructure/{port_key}/{adapter_name}"
            contract_path = Contract.for_source(f"{base_path}.py")
            data = Contract.read(contract_path)
            if data:
                contracts.append((contract_path, base_path, data))
                for req in data.get("requires", []):
                    all_requires.add(req)

        # 1. Installazione dipendenze 'requires' per gli adapter abilitati
        if all_requires:
            req_list = sorted(list(all_requires))
            print(f"\n[*] Dipendenze 'requires' rilevate per gli adapter abilitati ({len(req_list)}):")
            for req in req_list:
                print(f"  - {req}")

            print("[*] Installazione pacchetti in corso via pip...")
            cmd = [sys.executable, "-m", "pip", "install"] + req_list
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print("[✓] Dipendenze installate con successo!")
                else:
                    print(f"[!] Errore durante pip install:\n{result.stderr}")
            except Exception as e:
                print(f"[!] Impossibile eseguire il processo di installazione: {e}")
        else:
            print("\n[*] Nessuna dipendenza 'requires' specificata nei contratti degli adapter abilitati.")

        print("\n[✓] Procedura --install completata per gli adapter abilitati.\n")