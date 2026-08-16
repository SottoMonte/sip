imports: {
	'module': import("infrastructure.persistence.filesystem")
};

exports: {
	'filter': imports.module.Adapter.filter
};

tuple:test_suite := (
	{
		"action": exports.filter;
		"inputs": (imports.module.Adapter, ({"name": "README.md"; "type": "file"}, {"name": "src"; "type": "directory"}), {"filter": {"type": {"eq": "file"}}});
		"outputs": none;
		"assert": @received.success == true & @received.outputs != none;
		"note": "Adapter.filter seleziona gli elementi file dal dataset";
	},
	{
		"action": exports.filter;
		"inputs": (imports.module.Adapter, ({"relative_path": "src/application"; "type": "directory"}, {"relative_path": "README.md"; "type": "file"}), {"filter": {"startswith": {"relative_path": "src/"}}});
		"outputs": none;
		"assert": @received.success == true & @received.outputs != none;
		"note": "Adapter.filter normalizza lo slash e applica startswith sui percorsi";
	}
);
