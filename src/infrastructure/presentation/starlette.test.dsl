exports: {
    'echo': pass;
};

tuple:test_suite := (
    {
        "action": exports.echo;
        "inputs": "window";
        "outputs": none;
        "assert": @received != none;
        "note": "la suite Starlette resta eseguibile senza import dotted";
    }
);