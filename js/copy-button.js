/**
 * 通用复制按钮 — 点击复制 data-copy-value 指定的文本，短暂显示勾号反馈。
 *
 * 可选属性：
 *   data-copy-value  要复制的文本（必填）
 *   data-copy-label  复制成功后显示的 aria-label（可选，默认保持原样）
 */
(() => {
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
		document.querySelectorAll("[data-copy-value]").forEach((button) => {
			const value = button.dataset.copyValue;
			const copiedLabel = button.dataset.copyLabel ?? "";
			const originalIcon = button.innerHTML;
			const originalLabel = button.getAttribute("aria-label") ?? "";
			let resetTimer = null;

			button.addEventListener("click", async () => {
				try {
					await copyText(value);
				} catch {
					return;
				}
				button.innerHTML = CHECK_ICON;
				if (copiedLabel) button.setAttribute("aria-label", copiedLabel);
				if (resetTimer) clearTimeout(resetTimer);
				resetTimer = setTimeout(() => {
					button.innerHTML = originalIcon;
					if (copiedLabel) button.setAttribute("aria-label", originalLabel);
				}, 1500);
			});
		});
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", setup);
	} else {
		setup();
	}
})();
