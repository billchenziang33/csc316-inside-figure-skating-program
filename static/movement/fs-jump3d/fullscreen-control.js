export async function toggleFullscreen({ element, documentRef = document, fallback }) {
	if (documentRef.fullscreenElement) {
		await documentRef.exitFullscreen();
		return 'native-exited';
	}
	if (fallback.active) {
		fallback.exit();
		return 'fallback-exited';
	}
	try {
		await element.requestFullscreen();
		return 'native-entered';
	} catch {
		fallback.enter();
		return 'fallback-entered';
	}
}
