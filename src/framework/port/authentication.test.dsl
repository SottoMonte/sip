imports: {
    'module': import("framework.port.authentication");
};

exports: {
    'method_names': keys;
};

tuple:test_suite := (
    {
        "action": exports.method_names;
        "inputs": [imports.module.Port._method_decorators];
        "outputs": ["sign_in", "sign_up", "sign_out", "sign_aid", "get_user"];
        "assert": @received == @expected;
        "note": "Authentication Port espone tutti i metodi del contratto";
    }
);
