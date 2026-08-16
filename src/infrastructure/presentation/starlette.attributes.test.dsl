exports: {
    'echo': pass;
};

tuple:test_suite := (
    {
        "action": exports.echo;
        "inputs": "width full";
        "outputs": none;
        "assert": @received != none;
        "note": "la suite attributi resta eseguibile senza import dotted";
    },
    {
        "action": exports.echo;
        "inputs": "color";
        "outputs": none;
        "assert": @received != none;
        "note": "la suite attributi copre un secondo caso senza import dotted";
    }
);