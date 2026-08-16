imports: {
    'module': import("framework.manager.loader");
};

any:framework := imports.module.Framework();
any:infrastructure := imports.module.Infrastructure();

exports: {
    'imports': framework.imports;
    'component': framework.component;
    'import_module': infrastructure.import_module;
};

tuple:test_suite := (
    {
        "action": exports.imports;
        "inputs": "import os";
        "outputs": ["os"];
        "assert": @received == @expected;
        "note": "imports estrae un modulo Python dal sorgente";
    },
    {
        "action": exports.component;
        "inputs": "missing.component";
        "outputs": none;
        "assert": @received == @expected;
        "note": "component restituisce none per una risorsa non registrata";
    },
    {
        "action": exports.import_module;
        "inputs": "framework.manager.loader";
        "outputs": true;
        "assert": @received.Framework != none;
        "note": "import_module risolve un modulo framework reale senza fixture";
    }
);