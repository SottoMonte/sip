imports: {
    'module': import("framework.manager.defender");
    'regex': import("re")
};

exports: {
    'resolve_route': imports.module.Manager.resolve_route
};

any:route_pattern := imports.regex.compile("^/users/(?P<id>[^/]+)$");
dict:routes := {
    "users": {
        "GET": {
            "pattern": route_pattern;
            "metadata": {"view": "user"};
        };
    };
};

tuple:test_suite := (
    {
        "action": exports.resolve_route;
        "inputs": (none, routes, "https://example.test/users/42?tag=one&tag=two#section=profile", "GET");
        "outputs": "user";
        "assert": @received.metadata.view == @expected & @received.params.id == "42" & @received.url_details.protocol == "https" & @received.url_details.query.tag == ["one", "two"] & @received.url_details.fragment.section == "profile";
        "note": "resolve_route trova una rotta GET ed estrae parametro, query e fragment";
    },
    {
        "action": exports.resolve_route;
        "inputs": (none, routes, "/users/42", "POST");
        "outputs": none;
        "assert": @received == @expected;
        "note": "resolve_route rifiuta un metodo non dichiarato per la rotta";
    },
    {
        "action": exports.resolve_route;
        "inputs": (none, routes, "/missing", "GET");
        "outputs": none;
        "assert": @received == @expected;
        "note": "resolve_route ritorna null quando il path non corrisponde";
    }
);