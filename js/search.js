/**
 * search.js — 站内搜索
 * 点击放大镜展开灰线输入框，从 search-index.json（构建时生成）加载索引，
 * 按空格切分关键字，对标题/内容/分类/日期做 AND 匹配，下拉展示结果。
 */
(() => {
	const SEARCH_ICON = `<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"></circle><path d="M21 21l-4.35-4.35"></path></svg>`;

	function init() {
		setup();
	}

	function setup() {
		const box = document.querySelector(".search-box");
		const toggle = document.getElementById("search-toggle");
		const input = document.getElementById("search-input");
		const results = document.getElementById("search-results");
		if (!box || !toggle || !input || !results) return;

		toggle.innerHTML = SEARCH_ICON;

	let index = [];

	async function loadIndex() {
		try {
			const siteUrl = document.querySelector('meta[name="site-url"]')?.content;
			const res = await fetch(new URL("search-index.json", siteUrl));
			if (!res.ok) return;
			index = await res.json();
		} catch {
			// 索引加载失败则搜索不可用
		}
	}

	function escapeHtml(text) {
		return String(text)
			.replaceAll("&", "&amp;")
			.replaceAll("<", "&lt;")
			.replaceAll(">", "&gt;")
			.replaceAll('"', "&quot;");
	}

	function escapeRegex(text) {
		return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
	}

	// 将命中的关键字用 <mark> 高亮（大小写不敏感）
	function highlight(text, keywords) {
		let escaped = escapeHtml(text);
		for (const kw of keywords) {
			if (!kw) continue;
			const re = new RegExp(escapeRegex(escapeHtml(kw)), "gi");
			escaped = escaped.replace(
				re,
				(m) => `<mark class="search-highlight">${m}</mark>`,
			);
		}
		return escaped;
	}

	function search(query) {
		const keywords = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
		if (keywords.length === 0) {
			results.classList.remove("open");
			return;
		}

		const hits = index.filter((entry) => {
			const haystack = [
				entry.title,
				entry.description,
				entry.category,
				entry.date,
				entry.content,
			]
				.join("\n")
				.toLowerCase();
			return keywords.every((kw) => haystack.includes(kw));
		});

		if (hits.length === 0) {
			results.innerHTML = `<div class="search-empty">没有找到相关文章</div>`;
		} else {
			results.innerHTML = hits
				.slice(0, 20)
				.map((entry) => {
					const title = highlight(entry.title, keywords);
					const meta = highlight(
						`${entry.category} · ${entry.date}`,
						keywords,
					);
					return (
						`<a class="search-result" href="${escapeHtml(entry.url)}">` +
						`<span class="search-result-title">${title}</span>` +
						`<span class="search-result-meta">${meta}</span>` +
						`</a>`
					);
				})
				.join("");
		}
		results.classList.add("open");
	}

	function openSearch() {
		box.classList.add("open");
		input.focus();
	}

	function closeSearch() {
		box.classList.remove("open");
		results.classList.remove("open");
	}

	// 点击放大镜：展开/收起
	toggle.addEventListener("click", () => {
		if (box.classList.contains("open")) {
			closeSearch();
		} else {
			openSearch();
		}
	});

	let timer = null;
	input.addEventListener("input", () => {
		clearTimeout(timer);
		timer = setTimeout(() => search(input.value), 150);
	});

	input.addEventListener("focus", () => {
		if (input.value.trim()) {
			search(input.value);
		}
	});

	// 点击搜索框外关闭下拉；输入为空时收起输入框
	document.addEventListener("click", (e) => {
		if (e.target.closest(".search-box")) return;
		results.classList.remove("open");
		if (!input.value.trim()) {
			box.classList.remove("open");
		}
	});

	// Escape 收起
	document.addEventListener("keydown", (e) => {
		if (e.key === "Escape") {
			results.classList.remove("open");
			if (!input.value.trim()) {
				box.classList.remove("open");
			}
			input.blur();
		}
	});

		loadIndex();
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", init);
	} else {
		init();
	}
})();
