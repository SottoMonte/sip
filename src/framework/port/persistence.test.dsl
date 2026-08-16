imports: {
    'module': import("framework.port.persistence")
};

exports: {
    'create': imports.module.Port.create;
    'read': imports.module.Port.read;
    'update': imports.module.Port.update;
    'delete': imports.module.Port.delete;
    'query': imports.module.Port.query;
    'view': imports.module.Port.view
};

tuple:test_suite := (
    {
        "action": exports.create;
        "inputs": imports.module.Port;
        "outputs": none;
        "assert": @received == @expected;
        "note": "Persistence Port espone create come hook astratto";
    },
    {
        "action": exports.read;
        "inputs": imports.module.Port;
        "outputs": none;
        "assert": @received == @expected;
        "note": "Persistence Port espone read come hook astratto";
    },
    {
        "action": exports.update;
        "inputs": imports.module.Port;
        "outputs": none;
        "assert": @received == @expected;
        "note": "Persistence Port espone update come hook astratto";
    },
    {
        "action": exports.delete;
        "inputs": imports.module.Port;
        "outputs": none;
        "assert": @received == @expected;
        "note": "Persistence Port espone delete come hook astratto";
    },
    {
        "action": exports.query;
        "inputs": imports.module.Port;
        "outputs": none;
        "assert": @received == @expected;
        "note": "Persistence Port espone query come hook astratto";
    },
    {
        "action": exports.view;
        "inputs": imports.module.Port;
        "outputs": none;
        "assert": @received == @expected;
        "note": "Persistence Port espone view come hook astratto";
    }
);
