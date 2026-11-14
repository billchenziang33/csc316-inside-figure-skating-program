function cameraNameKey(name) {
	return String(name)
		.replace(/:sr$/i, '')
		.replace(/_\d+$/i, '')
		.replace(/(\d)\.(\d)/g, '$1$2')
		.normalize('NFKD')
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, '_')
		.replace(/^_+|_+$/g, '');
}

export function findExportedNameMatch(objects, expectedName) {
	const exact = objects.find((object) => object.name === expectedName);
	if (exact) return exact;

	const key = cameraNameKey(expectedName);
	const matches = objects.filter((object) => cameraNameKey(object.name) === key);
	return matches.length === 1 ? matches[0] : null;
}

export function findExportedNamesByPrefix(objects, expectedPrefix) {
	const prefix = cameraNameKey(expectedPrefix);
	return objects.filter((object) => {
		const key = cameraNameKey(object.name);
		return key === prefix || key.startsWith(`${prefix}_`);
	});
}
