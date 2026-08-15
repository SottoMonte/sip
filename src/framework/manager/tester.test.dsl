// Test per il Manager del Tester
// Questo file verifica che la funzione import() funzioni correttamente

imports: {
    'tester_module': import("framework.manager.tester")
};

exports: {
    'resolve_filter': imports.tester_module.resolve_filter
};

// Test semplice: verify import() funziona
tuple:test_suite := (
    {
        "action": exports.resolve_filter;
        "inputs": "managers";
        "outputs": "src/framework/manager";
        "assert": @received == @expected;
        "note": "Test import() - resolve_filter con 'managers'";
    },
    {
        "action": exports.resolve_filter;
        "inputs": "ports";
        "outputs": "src/framework/port";
        "assert": @received == @expected;
        "note": "Test import() - resolve_filter con 'ports'";
    }
);



