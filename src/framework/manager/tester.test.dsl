// Test per il Manager del Tester
// Questo file verifica che la funzione import() funzioni correttamente

imports: {
    'tester_module': import("framework.manager.tester");
    'presentation_module': import("framework.port.presentation")
};

exports: {
    'resolve_filter': imports.tester_module.resolve_filter;
    'resolve_target_name': imports.tester_module.resolve_target_name;
    'port': imports.presentation_module.Port
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
    },
    {
        "action": exports.resolve_target_name;
        "inputs": exports.resolve_filter;
        "outputs": "resolve_filter";
        "assert": @received == @expected;
        "note": "resolve_target_name restituisce il nome stabile della funzione esportata";
    },
    {
        "action": exports.port.initialize;
        "inputs": imports.presentation_module.Port;
        "outputs": none;
        "assert": @received == @expected;
        "note": "Un metodo di una classe esportata viene associato al relativo export oggetto";
    }
);



