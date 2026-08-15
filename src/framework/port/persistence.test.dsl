imports: {
    'module': import("framework.port.persistence");
};

exports: {
    'method_names': keys;
};

tuple:test_suite := (
    {
        "action": exports.method_names;
        "inputs": [imports.module.Port._method_decorators];
        "outputs": ["create", "read", "update", "delete", "query"];
        "assert": @received == @expected;
        "note": "Persistence Port espone i metodi CRUD del contratto";
    }
);
