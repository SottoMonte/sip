imports: {
    'module': import("framework.manager.defender");
    'regex': import("re");
};

roles: {
    "guest": {
        "resources": ["application/view/page/auth/login.xml"];
    };
};

policies: {
    "GET_ALLOW_PATH": {
        "effect": "allow";
        "target": {"action": "GET";};
        "condition": (@resource in roles.guest.resources) & (@action == "GET");
    };
    "GET_ALLOW_ALL": {
        "effect": "allow";
        "target": {"action": "GET";};
        "condition": @action == "GET";
    };
    "POST_ALLOW_ALL": {
        "effect": "allow";
        "target": {"action": "POST";};
        "condition": @action == "POST";
    };
};

exports: {
    'resolve_route': imports.module.Manager.resolve_route;
    'get_allow_path': policies.GET_ALLOW_PATH.condition;
    'get_allow_all': policies.GET_ALLOW_ALL.condition;
    'post_allow_all': policies.POST_ALLOW_ALL.condition;
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
    },
    {
        "action": exports.get_allow_all;
        "inputs": {"resource": "/login"; "action": "GET";};
        "outputs": true;
        "assert": @received == @expected;
        "note": "GET_ALLOW_ALL consente una richiesta GET";
    },
    {
        "action": exports.post_allow_all;
        "inputs": {"resource": "/login"; "action": "POST";};
        "outputs": true;
        "assert": @received == @expected;
        "note": "POST_ALLOW_ALL consente una richiesta POST";
    },
    {
        "action": exports.get_allow_path;
        "inputs": {"resource": "application/view/page/auth/login.xml"; "action": "GET";};
        "outputs": true;
        "assert": @received == @expected;
        "note": "GET_ALLOW_PATH consente la risorsa presente nel ruolo guest";
    },
    {
        "action": exports.get_allow_path;
        "inputs": {"resource": "/profile"; "action": "GET";};
        "outputs": false;
        "assert": @received == @expected;
        "note": "GET_ALLOW_PATH nega una risorsa assente dal ruolo guest";
    },
    {
        "action": exports.get_allow_all;
        "inputs": {"resource": "/home"; "action": "POST";};
        "outputs": false;
        "assert": @received == @expected;
        "note": "GET_ALLOW_ALL nega una richiesta non GET";
    },
    {
        "action": exports.get_allow_all;
        "inputs": {"resource": "/admin"; "action": "GET";};
        "outputs": true;
        "assert": @received == @expected;
        "note": "GET_ALLOW_ALL consente GET anche su una risorsa diversa da login";
    },
    {
        "action": exports.post_allow_all;
        "inputs": {"resource": "/login"; "action": "GET";};
        "outputs": false;
        "assert": @received == @expected;
        "note": "POST_ALLOW_ALL nega una richiesta GET";
    },
    {
        "action": exports.get_allow_path;
        "inputs": {"resource": "application/view/page/auth/login.xml"; "action": "POST";};
        "outputs": false;
        "assert": @received == @expected;
        "note": "GET_ALLOW_PATH nega la risorsa guest quando il metodo non è GET";
    },
    {
        "action": exports.get_allow_path;
        "inputs": {"resource": "application/view/page/auth/signup.xml"; "action": "GET";};
        "outputs": false;
        "assert": @received == @expected;
        "note": "GET_ALLOW_PATH nega una vista non presente nelle risorse guest";
    },
    {
        "action": exports.get_allow_all;
        "inputs": {"resource": "/login"; "action": "get";};
        "outputs": false;
        "assert": @received == @expected;
        "note": "GET_ALLOW_ALL richiede il metodo GET in maiuscolo";
    },
    {
        "action": exports.post_allow_all;
        "inputs": {"resource": ""; "action": "";};
        "outputs": false;
        "assert": @received == @expected;
        "note": "POST_ALLOW_ALL nega input privi di metodo e risorsa";
    }
);