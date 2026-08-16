imports: {
    'module': import("framework.manager.storekeeper");
};

exports: {
    'manager': imports.module.Manager;
};

tuple:test_suite := (
    {
        "action": exports.manager;
        "inputs": {"providers": []; "defender": none; "orchestrator": none; "messenger": none};
        "outputs": true;
        "assert": @received != none;
        "note": "Manager storekeeper costruisce un componente con dipendenze esplicite";
    }
);