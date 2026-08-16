exports: {
    'echo': pass;
};

tuple:test_suite := (
    {
        "action": exports.echo;
        "inputs": "api adapter";
        "outputs": none;
        "assert": @received != none;
        "note": "la suite API resta eseguibile anche senza discovery del modulo dotted";
    }
);