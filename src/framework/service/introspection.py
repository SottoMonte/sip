import os

class Reflection:
    """Utility di reflection sui moduli Python."""

    @staticmethod
    def imports(code: str) -> list[str]:
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

    @staticmethod
    def hash_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def class_methods(cls) -> dict[str, str]:
        """Sorgente dei metodi pubblici definiti direttamente su `cls`
        (esclude ereditati, dunder e privati). {nome_metodo: sorgente}."""
        methods = {}
        for name, member in vars(cls).items():
            if name.startswith('_'):
                continue
            fn = member.__func__ if isinstance(member, (staticmethod, classmethod)) else member
            if not inspect.isfunction(fn):
                continue
            try:
                methods[name] = inspect.getsource(fn)
            except (OSError, TypeError):
                continue
        return methods

    @staticmethod
    def module_components(module) -> dict[str, str]:
        """Sorgente di tutti i componenti pubblici definiti DIRETTAMENTE in
        `module` (esclude import): funzioni a livello di modulo e metodi
        delle classi definite nel modulo.

        Generalizza `class_methods` a qualunque tipo di file (adapter,
        manager, service, ...): non presuppone che il modulo esponga una
        classe con un nome specifico.

        Chiavi risultanti:
            'nome_funzione'            per funzioni a livello di modulo
            'NomeClasse.nome_metodo'   per metodi di classi nel modulo
        """
        components: dict[str, str] = {}
        for name, member in vars(module).items():
            if name.startswith('_'):
                continue
            if inspect.isfunction(member) and getattr(member, "__module__", None) == module.__name__:
                try:
                    components[name] = inspect.getsource(member)
                except (OSError, TypeError):
                    continue
            elif inspect.isclass(member) and member.__module__ == module.__name__:
                for method_name, source in Reflection.class_methods(member).items():
                    components[f"{name}.{method_name}"] = source
        return components

    @staticmethod
    def dependencies(cls):
        return {
            name: p.annotation
            for name, p in inspect.signature(cls.__init__).parameters.items()
            if name != "self"
            and p.annotation is not inspect.Parameter.empty
        }

    @staticmethod
    def is_port_list(annotation):
        return (
            getattr(annotation, "__origin__", None)
            is list
        )

    @staticmethod
    def file_dependencies(file_path: str, root="src"):

        try:
            tree = ast.parse(Path(file_path).read_text())
        except Exception:
            return []

        deps = {file_path}

        def add(path):
            if path.exists():
                deps.add(str(path))

        for node in ast.walk(tree):

            if isinstance(node, ast.Import):

                for alias in node.names:
                    add(
                        Path(root, *alias.name.split(".")).with_suffix(".py")
                    )

            elif isinstance(node, ast.ImportFrom):

                if node.module is None:
                    continue

                base = Path(root, *node.module.split("."))

                module = base.with_suffix(".py")

                if module.exists():
                    add(module)
                    continue

                for alias in node.names:

                    if alias.name == "*":
                        continue

                    add(
                        (base / alias.name).with_suffix(".py")
                    )

        return sorted(deps)

    @staticmethod
    def dependencies(cls):
        return {
            name: p.annotation
            for name, p in inspect.signature(cls.__init__).parameters.items()
            if (
                name != "self"
                and p.annotation is not inspect.Parameter.empty
            )
        }

    @staticmethod
    def is_port_list(annotation):
        return (
            getattr(annotation, "__origin__", None)
            is list
        )