type:route := {
    "path": { "type": "string" };
    "method": { "type": "string"; "default": "GET" };
    "type": { "type": "string" "allowed": ["view","authenticate","terminate","activate","reinstate"] };
    "view": { "type": "string"; "default": "" };
    "controller": { "type": "string"; "default": "" };
};

type:policy := {
    "effect": { "type": "string"; "regex": "^(allow|deny)$"; "default": "deny" };
    "target": { 
        "schema": { "action": { "type": "string" }; "resource": { "type": "string" }; "location": { "type": "string" }; "context": { "type": "dict" } }; 
        "default": { "action": ""; "resource": ""; "location": ""; "context": {} };
    };
    "description": { "type": "string"; "default": "" };
    "condition": { "default": true };
};

type:user := {
  "identifier": { "type": "string" };
  "username": { "type": "string" };
  "role": { "type": "string"; "regex": "^(admin|user|guest)$" };
  "avatar": { "type": "string" };
};

type:role := {
    "id": { "type": "string" };
    "name": { "type": "string" };
    "description": { "type": "string" };
    "resources": { "type": "list"; "schema": { "type": "string" } };
};

roles:{
    role:admin := {
        id:"role-1";
        name:"admin";
        description:"admin";
        resources:["all"];
    };
    role:user := {
        id:"role-2";
        name:"user";
        description:"user";
        resources:["all"];
    };
    role:guest := {
        id:"role-3";
        name:"guest";
        description:"guest";
        resources:["application/view/page/auth/login.xml"];
    };
}

routes: {
    // SIP Italia home
    route:GET_INDEX := { path:"/"; method:"GET"; "type":"view"; view:"home/Home.xml" };
    route:GET_LANDING := { path:"/it/home"; method:"GET"; "type":"view"; view:"home/Home.xml" };
    // SIP Italia landing sections and catalog entry points
    route:GET_AZIENDA := { path:"/azienda"; method:"GET"; "type":"view"; view:"company/Company.xml" };
    route:GET_SHOP := { path:"/shop"; method:"GET"; "type":"view"; view:"shop/Shop.xml" };
    route:GET_SHOP_BILANCE := { path:"/shop/bilance"; method:"GET"; "type":"view"; view:"home/Home.xml" };
    route:GET_SHOP_ATTREZZATURE := { path:"/shop/attrezzature"; method:"GET"; "type":"view"; view:"shop/Shop.xml" };
    route:GET_SHOP_SOFTWARE := { path:"/shop/software"; method:"GET"; "type":"view"; view:"shop/Shop.xml" };
    route:GET_SHOP_ACCESSORI := { path:"/shop/accessori"; method:"GET"; "type":"view"; view:"shop/Shop.xml" };
    route:GET_SHOP_CATALOG := { path:"/shop/catalog"; method:"GET"; "type":"view"; view:"catalog/Catalog.xml"; controller:"catalog" };
    route:GET_SHOP_CATALOGO := { path:"/shop/catalogo"; method:"GET"; "type":"view"; view:"catalog/Catalog.xml"; controller:"catalog" };
    route:GET_PRODUCT_BILANCE := { path:"/shop/product/bilancia-touch-15"; method:"GET"; "type":"view"; view:"product/Product.xml"; controller:"product" };
    route:GET_PRODUCT_POS := { path:"/shop/product/cassa-pos-pro"; method:"GET"; "type":"view"; view:"product/Product.xml"; controller:"product" };
    route:GET_PRODUCT_CASHMATIC := { path:"/shop/product/cashmatic-strong"; method:"GET"; "type":"view"; view:"product/Product.xml"; controller:"product" };
    route:GET_PRODUCT_SOFTWARE := { path:"/shop/product/software-retail-suite"; method:"GET"; "type":"view"; view:"product/Product.xml"; controller:"product" };
    route:GET_CART := { path:"/shop/cart"; method:"GET"; "type":"view"; view:"cart/Cart.xml"; controller:"cart" };
    route:POST_CART := { path:"/shop/cart"; method:"POST"; "type":"view"; view:"cart/Cart.xml"; controller:"cart" };
    route:GET_CART_REMOVE := { path:"/shop/cart/remove"; method:"GET"; "type":"view"; view:"cart/Cart.xml"; controller:"cart" };
    route:GET_CHECKOUT := { path:"/shop/checkout"; method:"GET"; "type":"view"; view:"checkout/Checkout.xml"; controller:"checkout" };
    route:POST_ORDER := { path:"/shop/order/confirmation"; method:"POST"; "type":"view"; view:"order/Confirmation.xml"; controller:"checkout" };
    route:GET_ACCOUNT := { path:"/account"; method:"GET"; "type":"view"; view:"account/Account.xml"; controller:"account" };
    route:GET_ACCOUNT_LOGIN := { path:"/account/login"; method:"GET"; "type":"view"; view:"account/Login.xml"; controller:"account" };
    route:POST_ACCOUNT_LOGIN := { path:"/account/login"; method:"POST"; "type":"authenticate"; view:"account/Account.xml" };
    route:GET_ACCOUNT_REGISTER := { path:"/account/register"; method:"GET"; "type":"view"; view:"account/Login.xml" };
    route:GET_ACCOUNT_ORDERS := { path:"/account/orders"; method:"GET"; "type":"view"; view:"account/Orders.xml"; controller:"account" };
    route:GET_ORDER := { path:"/account/orders/{id}"; method:"GET"; "type":"view"; view:"account/Orders.xml"; controller:"account" };
    route:GET_ASSISTENZA := { path:"/assistenza"; method:"GET"; "type":"view"; view:"support/Support.xml" };
    route:GET_NEWS := { path:"/news"; method:"GET"; "type":"view"; view:"news/News.xml" };
    route:GET_CONTATTI := { path:"/contatti"; method:"GET"; "type":"view"; view:"contact/Contact.xml" };
    route:GET_PROFILE := { path:"/profile"; method:"GET"; "type":"view"; view:"profile.xml" };
    // Auth
    route:GET_LOGIN := { path:"/login"; method:"GET"; "type":"view"; view:"auth/login.xml" };
    route:GET_LOGOUT := { path:"/logout"; method:"GET"; "type":"view"; view:"auth/logout.xml" };
    route:POST_LOGIN := { path:"/login"; method:"POST"; "type":"authenticate"; view:"auth/login.xml" };
    route:POST_LOGOUT := { path:"/logout"; method:"POST"; "type":"terminate"; view:"auth/logout.xml" };
    route:GET_SIGNUP := { path:"/signup"; method:"GET"; "type":"view"; view:"auth/signup.xml" };
    route:POST_SIGNUP := { path:"/signup"; method:"POST"; "type":"activate"; };
    route:GET_RECOVERY := { path:"/recovery"; method:"GET"; "type":"reinstate"; view:"auth/signup.xml" };
    route:POST_RECOVERY := { path:"/recovery"; method:"POST"; "type":"reinstate"; };
    // Admin
    route:GET_ADMIN := { path:"/admin"; method:"GET"; "type":"view"; view:"admin.xml" };
    // Error
    route:GET_ERROR_404 := { path:"/404"; method:"GET"; "type":"view"; view:"error/404.xml" };
    // Twitch
    route:GET_BROWSER := { path:"/browse"; method:"GET"; "type":"view"; view:"twitch_browse.xml" };
    route:GET_HOME := { path:"/home"; method:"GET"; "type":"view"; view:"twitch_home.xml" };
    route:GET_USER_PROFILE := { path:"/user/{id}"; method:"GET"; "type":"view"; view:"twitch_channel.xml" };
    route:GET_TRIS := { path:"/tris"; method:"GET"; "type":"view"; view:"tris.xml"; controller:"tris" };
}

policies: {
    policy:GET_ALLOW_PATH := {
        effect:"allow";
        target: { action: "GET"; };
        description:"Allow GET method for resources in guest role"; 
        condition: (@resource in roles.guest.resources) & (@action == "GET");
    };
    policy:GET_ALLOW_ALL := {
        effect:"allow";
        target: { action: "GET"; };
        description:"Allow all GET requests";
        condition: @action == "GET";
    };
    policy:POST_ALLOW_ALL := {
        effect:"allow";
        target: { action: "POST"; };
        description:"Allow all POST requests";
        condition: @action == "POST";
    };
}

rules : {
    "/": [policies.GET_ALLOW_ALL];
    "/it/home": [policies.GET_ALLOW_ALL];
    "/azienda": [policies.GET_ALLOW_ALL];
    "/shop": [policies.GET_ALLOW_ALL];
    "/shop/bilance": [policies.GET_ALLOW_ALL];
    "/shop/attrezzature": [policies.GET_ALLOW_ALL];
    "/shop/software": [policies.GET_ALLOW_ALL];
    "/shop/accessori": [policies.GET_ALLOW_ALL];
    "/shop/catalog": [policies.GET_ALLOW_ALL];
    "/shop/catalogo": [policies.GET_ALLOW_ALL];
    "/shop/product/bilancia-touch-15": [policies.GET_ALLOW_ALL];
    "/shop/product/cassa-pos-pro": [policies.GET_ALLOW_ALL];
    "/shop/product/cashmatic-strong": [policies.GET_ALLOW_ALL];
    "/shop/product/software-retail-suite": [policies.GET_ALLOW_ALL];
    "/shop/cart": [policies.GET_ALLOW_ALL, policies.POST_ALLOW_ALL];
    "/shop/cart/remove": [policies.GET_ALLOW_ALL];
    "/shop/checkout": [policies.GET_ALLOW_ALL];
    "/shop/order/confirmation": [policies.POST_ALLOW_ALL];
    "/account": [policies.GET_ALLOW_ALL];
    "/account/login": [policies.GET_ALLOW_ALL, policies.POST_ALLOW_ALL];
    "/account/register": [policies.GET_ALLOW_ALL];
    "/account/orders": [policies.GET_ALLOW_ALL];
    "/assistenza": [policies.GET_ALLOW_ALL];
    "/news": [policies.GET_ALLOW_ALL];
    "/contatti": [policies.GET_ALLOW_ALL];
    "/profile": [policies.GET_ALLOW_PATH];
    "/login": [policies.GET_ALLOW_ALL,policies.POST_ALLOW_ALL];
    "/logout": [policies.GET_ALLOW_PATH];
    "/signup": [policies.GET_ALLOW_ALL,policies.POST_ALLOW_ALL];
    "/recovery": [policies.GET_ALLOW_ALL,policies.POST_ALLOW_ALL];
    "/admin": [policies.GET_ALLOW_PATH];
    "/browse": [policies.GET_ALLOW_ALL];
    "/home": [policies.GET_ALLOW_ALL];
    "/user/{id}": [policies.GET_ALLOW_ALL];
    "/tris": [policies.GET_ALLOW_ALL];
    "/static/js/dsl.js": [policies.GET_ALLOW_ALL];
    //"/404": [policies.GET_ALLOW_ALL];
}
