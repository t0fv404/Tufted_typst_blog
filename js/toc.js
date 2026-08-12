/**
 * toc.js — 抽屉式树形目录 + 拖动伸缩
 * 点击导航栏左侧按钮从左边滑出目录抽屉，支持折叠/展开、点击外部关闭、拖拽调节宽度。
 */
(() => {
	function init() {
		buildDrawer();
	}

	function buildDrawer() {
		const toggleBtn = document.getElementById("toc-toggle");
		const drawer = document.getElementById("toc-drawer");
		if (!toggleBtn || !drawer) return;

	const inner = drawer.querySelector(".toc-drawer-inner");
	if (!inner) return;

	const section = document.querySelector("article > section");
	if (!section) return;

	const headings = Array.from(
		section.querySelectorAll("h1, h2, h3, h4, h5, h6"),
	);

	// ── 构建树 ──
	const tocRoot = { children: [], level: 0 };
	const stack = [tocRoot];

	headings.forEach((h, i) => {
		if (!h.id) h.id = "heading-" + i;

		const level = parseInt(h.tagName.charAt(1), 10);
		const node = { text: h.textContent || "", id: h.id, children: [], level };

		while (stack.length > 1 && stack[stack.length - 1].level >= level) {
			stack.pop();
		}
		stack[stack.length - 1].children.push(node);
		stack.push(node);
	});

	// ── 渲染树 ──
	function renderTree(nodes, parentEl) {
		const ul = document.createElement("ul");
		ul.className = "toc-tree";

		nodes.forEach((node) => {
			const li = document.createElement("li");
			li.className = "toc-node";

			const hasChildren = node.children.length > 0;
			const row = document.createElement("div");
			row.className = "toc-row";

			if (hasChildren) {
				const toggle = document.createElement("span");
				toggle.className = "toc-toggle";
				toggle.textContent = "▾";
				toggle.addEventListener("click", () => {
					const sub = li.querySelector(":scope > .toc-tree");
					if (sub) {
						const open = sub.style.display !== "none";
						sub.style.display = open ? "none" : "block";
						toggle.textContent = open ? "▸" : "▾";
					}
				});
				row.appendChild(toggle);
			} else {
				const spacer = document.createElement("span");
				spacer.className = "toc-spacer";
				row.appendChild(spacer);
			}

			const a = document.createElement("a");
			a.href = "#" + node.id;
			a.textContent = node.text;
			a.addEventListener("click", () => {
				drawer.classList.remove("open");
			});
			row.appendChild(a);
			li.appendChild(row);

			if (hasChildren) renderTree(node.children, li);
			ul.appendChild(li);
		});

		parentEl.appendChild(ul);
	}

	renderTree(tocRoot.children, inner);

	// ── 根据最长标题自动计算抽屉宽度 ──
	function calcDrawerWidth() {
		const allLinks = inner.querySelectorAll(".toc-row a");
		if (allLinks.length === 0) return;

		// 创建隐藏测量元素
		const measurer = document.createElement("span");
		measurer.style.cssText =
			"position:absolute;visibility:hidden;white-space:nowrap;font-size:0.95rem;font-family:inherit;";
		document.body.appendChild(measurer);

		let maxWidth = 0;
		allLinks.forEach((a) => {
			measurer.textContent = a.textContent;
			const w = measurer.getBoundingClientRect().width;
			// 考虑每层缩进 (1rem ≈ 16px per level)
			let indent = 0;
			const el = a.closest(".toc-node");
			if (el) {
				let level = 0;
				let p = el.parentElement;
				while (p && p.classList.contains("toc-tree")) {
					level++;
					p = p.parentElement && p.parentElement.closest(".toc-tree");
				}
				indent = level * 16;
			}
			maxWidth = Math.max(maxWidth, w + indent);
		});

		document.body.removeChild(measurer);

		// 抽屉宽度 = 文字 + 左padding(1.5rem) + 右padding(0.75rem) + 把手区(1rem) + 备量(1rem)
		const padding = (1.5 + 0.75 + 1 + 1) * 16; // rem to px at 16px base
		let width = Math.ceil((maxWidth + padding) / 16) * 16; // round to 16px grid
		const minW = 12 * 16; // 12rem
		const maxW = window.innerWidth * 0.8;

		width = Math.max(minW, Math.min(width, maxW));
		document.documentElement.style.setProperty(
			"--toc-drawer-width",
			width + "px",
		);
	}

	calcDrawerWidth();

	// ── 抽屉开关 ──
	toggleBtn.addEventListener("click", () => {
		drawer.classList.toggle("open");
	});

	// 点击抽屉外区域关闭
	document.addEventListener("click", (e) => {
		if (!drawer.classList.contains("open")) return;
		if (
			!drawer.contains(e.target) &&
			e.target !== toggleBtn &&
			!toggleBtn.contains(e.target)
		) {
			drawer.classList.remove("open");
		}
	});

	// ── 拖动伸缩把手调整抽屉宽度 ──
	const handle = document.getElementById("toc-resize-handle");
	const root = document.documentElement;

	if (handle) {
		let startX;
		let startWidth;

		function onDragStart(e) {
			startX = e.clientX || (e.touches && e.touches[0].clientX);
			startWidth = drawer.getBoundingClientRect().width;
			handle.classList.add("dragging");
			document.body.style.userSelect = "none";
			document.addEventListener("mousemove", onDragMove);
			document.addEventListener("mouseup", onDragEnd);
			document.addEventListener("touchmove", onDragMove, { passive: false });
			document.addEventListener("touchend", onDragEnd);
		}

		function onDragMove(e) {
			const x = e.clientX || (e.touches && e.touches[0].clientX);
			if (!x) return;
			const delta = x - startX;
			const newWidth = startWidth + delta;
			const maxWidth = window.innerWidth * 0.8;
			const clamped = Math.max(12 * 16, Math.min(newWidth, maxWidth));
			root.style.setProperty("--toc-drawer-width", clamped + "px");
			e.preventDefault && e.preventDefault();
		}

		function onDragEnd() {
			handle.classList.remove("dragging");
			document.body.style.userSelect = "";
			document.removeEventListener("mousemove", onDragMove);
			document.removeEventListener("mouseup", onDragEnd);
			document.removeEventListener("touchmove", onDragMove);
			document.removeEventListener("touchend", onDragEnd);
		}

		handle.addEventListener("mousedown", onDragStart);
		handle.addEventListener("touchstart", onDragStart, { passive: true });
	}
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", init);
	} else {
		init();
	}
})();
