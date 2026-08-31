/**
 * Enhances rendered code blocks with language labels, line numbers, and a copy button.
 */
document.addEventListener("DOMContentLoaded", () => {
	function getCodeText(codeBlock) {
		const clone = codeBlock.cloneNode(true);
		clone.querySelectorAll("br").forEach((br) => br.replaceWith("\n"));
		return clone.textContent;
	}

	const codeBlocks = document.querySelectorAll("pre > code");

	codeBlocks.forEach((codeBlock) => {
		const pre = codeBlock.parentElement;
		const language = codeBlock.dataset.lang || "";

		// ========== Add language label ==========
		if (!pre.querySelector(".code-language")) {
			const label = document.createElement("span");
			label.className = "code-language";
			label.textContent = language;
			pre.insertBefore(label, pre.firstChild);
			pre.classList.add("has-code-language");
		}

		// ========== Add line numbers ==========
		// Check if already processed
		if (!pre.querySelector(".line-numbers-rows")) {
			// Convert <br> tags before counting lines.
			const text = getCodeText(codeBlock);
			// Remove trailing newline if it exists to avoid extra line number
			const cleanText = text.replace(/\n$/, "");
			const lineCount = cleanText.split(/\r\n|\r|\n/).length;

			// Create line numbers container
			const rows = document.createElement("span");
			rows.className = "line-numbers-rows";

			for (let i = 1; i <= lineCount; i++) {
				const span = document.createElement("span");
				span.textContent = i;
				rows.appendChild(span);
			}

			// Insert before code block
			pre.insertBefore(rows, codeBlock);
			pre.classList.add("has-line-numbers");
		}

		// ========== Add copy button ==========
		// Check if copy button already exists
		if (pre.querySelector(".copy-button")) return;

		// Create the copy button
		const copyButton = document.createElement("button");
		copyButton.className = "copy-button";
		copyButton.textContent = "Copy";
		let resetTimer = null;

		// Add click event listener
		copyButton.addEventListener("click", () => {
			const codeText = getCodeText(codeBlock);

			navigator.clipboard
				.writeText(codeText)
				.then(() => {
					// Success feedback
					copyButton.textContent = "Copied!";
					copyButton.classList.add("copied");

					if (resetTimer) clearTimeout(resetTimer);
					resetTimer = setTimeout(() => {
						copyButton.textContent = "Copy";
						copyButton.classList.remove("copied");
						resetTimer = null;
					}, 2000);
				})
				.catch((err) => {
					console.error("Failed to copy text: ", err);
					copyButton.textContent = "Error";
					if (resetTimer) clearTimeout(resetTimer);
					resetTimer = setTimeout(() => {
						copyButton.textContent = "Copy";
						resetTimer = null;
					}, 2000);
				});
		});

		// Make sure pre is positioned relatively so we can absolute position the button
		pre.style.position = "relative";

		// Append button to pre
		pre.appendChild(copyButton);
	});
});
