imports: {
    'factory': import("framework.service.factory");
};

any:repository := imports.factory.Repository(location: {"GITHUB": ["repos/{{ owner }}/{{ name }}"];});

exports: {
    'get_requirements': repository.get_requirements;
    'select': repository.select;
};

tuple:test_suite := (
    {
        "action": exports.get_requirements;
        "inputs": "";
        "outputs": [];
        "assert": @received == @expected;
        "note": "get_requirements gestisce un template vuoto";
    },
    {
        "action": exports.select;
        "inputs": (["static/path"], {});
        "outputs": "static/path";
        "assert": @received == @expected;
        "note": "select sceglie un template statico senza requisiti";
    }
);