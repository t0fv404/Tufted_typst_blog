/**
 * RSS 按钮 — 点击复制 RSS 订阅链接，短暂显示勾号反馈。
 */
(() => {
	const RSS_ICON = `<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" fill="currentColor" viewBox="0 0 256 256"><path d="M208,32H48A16,16,0,0,0,32,48V208a16,16,0,0,0,16,16H208a16,16,0,0,0,16-16V48A16,16,0,0,0,208,32ZM76,200a12,12,0,1,1,12-12A12,12,0,0,1,76,200Zm52,0a8,8,0,0,1-8-8,56.06,56.06,0,0,0-56-56,8,8,0,0,1,0-16,72.08,72.08,0,0,1,72,72A8,8,0,0,1,128,200Zm48,0a8,8,0,0,1-8-8A104.11,104.11,0,0,0,64,88a8,8,0,0,1,0-16A120.13,120.13,0,0,1,184,192,8,8,0,0,1,176,200Z"></path></svg>`;
	const CHECK_ICON = `<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" fill="currentColor" viewBox="0 0 256 256"><path d="M229.66,77.66l-128,128a8,8,0,0,1-11.32,0l-56-56a8,8,0,0,1,11.32-11.32L96,188.69,218.34,66.34a8,8,0,0,1,11.32,11.32Z"></path></svg>`;

	async function copyText(text) {
		if (navigator.clipboard && window.isSecureContext) {
			await navigator.clipboard.writeText(text);
			return;
		}
		const textarea = document.createElement("textarea");
		textarea.value = text;
		textarea.style.position = "fixed";
		textarea.style.opacity = "0";
		document.body.appendChild(textarea);
		textarea.select();
		document.execCommand("copy");
		textarea.remove();
	}

	function setup() {
		const button = document.getElementById("rss-copy");
		if (!button) return;

		button.innerHTML = RSS_ICON;

		let resetTimer = null;

		button.addEventListener("click", async () => {
			const url = new URL("/feed.xml", window.location.origin).href;
			try {
				await copyText(url);
			} catch {
				return;
			}
			button.innerHTML = CHECK_ICON;
			button.setAttribute("aria-label", "RSS 链接已复制");
			if (resetTimer) clearTimeout(resetTimer);
			resetTimer = setTimeout(() => {
				button.innerHTML = RSS_ICON;
				button.setAttribute("aria-label", "复制 RSS 链接");
			}, 1500);
		});
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", setup);
	} else {
		setup();
	}
})();
