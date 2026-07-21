// Entry module for the quick-md editor.
//
// This file is the single entry point that gets bundled (via esbuild) into
// static/js/qmd-editor.js, a self-contained ES module with all CodeMirror 6
// dependencies inlined. Bundling everything into one file guarantees there is
// exactly one copy of the CodeMirror 6 core packages (EditorView/State/etc.),
// which CM6 requires, and lets the editor work fully offline with no CDN.
//
// Re-export everything the editor page needs.
export { EditorView, basicSetup } from "codemirror";
export { EditorState, Compartment } from "@codemirror/state";
export { keymap } from "@codemirror/view";
export { defaultKeymap, indentWithTab } from "@codemirror/commands";
export { markdown } from "@codemirror/lang-markdown";
export { syntaxHighlighting, HighlightStyle } from "@codemirror/language";
export { tags } from "@lezer/highlight";
export { vim, getCM, Vim } from "@replit/codemirror-vim";