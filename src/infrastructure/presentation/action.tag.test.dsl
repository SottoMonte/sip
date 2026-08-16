exports: {
    'echo': pass;
};

tuple:test_suite := (
    {
        "action": exports.echo;
        "inputs": "action tag";
        "outputs": none;
        "assert": @received != none;
        "note": "la suite action tag resta eseguibile senza import dotted";
    }
);