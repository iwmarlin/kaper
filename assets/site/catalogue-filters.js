import { escapeHtml } from "./core.js?v=5b3a2d520f";

function fieldValue(field) {
  if (typeof field?.getValue === "function") return String(field.getValue() ?? "");
  return String(field?.value ?? "");
}

function setFieldValue(field, value) {
  if (typeof field?.setValue === "function") field.setValue(value);
  else if (field) field.value = value;
}

/* Query state belongs to the view, not to the dataset. Only the keys owned by
   a page are changed, so campaign parameters or a future shared parameter are
   not discarded. replaceState is deliberate: typing a search must not create
   one browser-history entry per keystroke. popstate is still restored when a
   reader returns to a filtered page from another document. */
export function createQueryState(fields, {
  defaults = {},
  onRestore = null,
} = {}) {
  const entries = Object.entries(fields).filter(([, field]) => field);

  function read() {
    const params = new URLSearchParams(window.location.search);
    for (const [key, field] of entries) {
      const defaultValue = String(defaults[key] ?? "");
      const requestedValue = params.has(key) ? params.get(key) : defaultValue;
      setFieldValue(field, requestedValue);
      // Native selects reject values for which they have no option; adapters
      // likewise normalize invalid modes or record IDs. Fall back explicitly
      // so a malformed or obsolete shared URL cannot create an empty active
      // chip or a UI state that the controls themselves cannot represent.
      if (fieldValue(field) !== requestedValue) setFieldValue(field, defaultValue);
    }
  }

  function write() {
    const url = new URL(window.location.href);
    for (const [key, field] of entries) {
      const value = fieldValue(field);
      const defaultValue = String(defaults[key] ?? "");
      if (!value || value === defaultValue) url.searchParams.delete(key);
      else url.searchParams.set(key, value);
    }
    const next = `${url.pathname}${url.search}${url.hash}`;
    const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    if (next !== current) window.history.replaceState(window.history.state, "", next);
  }

  const restore = () => {
    read();
    onRestore?.();
  };
  window.addEventListener("popstate", restore);

  return {
    read,
    write,
    destroy() {
      window.removeEventListener("popstate", restore);
    },
  };
}

function selectedOptionLabel(control) {
  return control?.options?.[control.selectedIndex]?.textContent?.trim() || fieldValue(control);
}

/* Works, People, Media and Sources share one accessible disclosure and active-
   filter model. Search remains outside the disclosure; facets collapse only on
   compact screens. Escape closes the panel and returns focus to its toggle,
   while crossing back to desktop clears stale mobile state. */
export function createCatalogueFilters({
  controls,
  options,
  toggle,
  panel,
  activeFilters,
  count,
  resetButton,
  onChange,
  onRestore = onChange,
  toggleLabel = "Filters and sort",
  compactMediaQuery = "(max-width: 900px)",
}) {
  const defaults = Object.fromEntries(Object.keys(controls).map((key) => [key, ""]));
  for (const option of options) defaults[option.key] = option.defaultValue;
  const queryState = createQueryState(controls, { defaults, onRestore });
  const compact = window.matchMedia?.(compactMediaQuery);

  const isOpen = () => toggle?.getAttribute("aria-expanded") === "true";
  const setOpen = (open, { returnFocus = false } = {}) => {
    panel?.classList.toggle("filters__advanced--open", open);
    toggle?.setAttribute("aria-expanded", String(open));
    if (returnFocus) toggle?.focus({ preventScroll: true });
  };
  const close = ({ returnFocus = false } = {}) => setOpen(false, { returnFocus });

  const handleToggle = () => setOpen(!isOpen());
  const handleEscape = (event) => {
    if (event.key !== "Escape" || !isOpen()) return;
    event.preventDefault();
    close({ returnFocus: true });
  };
  const handleBreakpoint = (event) => {
    if (!event.matches) close();
  };
  const handleChip = (event) => {
    const chip = event.target.closest("[data-filter-key]");
    if (!chip || !activeFilters?.contains(chip)) return;
    const option = options.find(({ key }) => key === chip.dataset.filterKey);
    if (!option || !controls[option.key]) return;
    setFieldValue(controls[option.key], option.defaultValue);
    const fallback = isOpen()
      ? controls[option.key]
      : (toggle?.offsetParent ? toggle : controls[option.key]);
    onChange?.();
    fallback?.focus?.({ preventScroll: true });
  };

  toggle?.addEventListener("click", handleToggle);
  activeFilters?.addEventListener("click", handleChip);
  document.addEventListener("keydown", handleEscape);
  if (compact?.addEventListener) compact.addEventListener("change", handleBreakpoint);
  else compact?.addListener?.(handleBreakpoint);

  function update() {
    const selected = options.filter(({ key, defaultValue }) => (
      fieldValue(controls[key]) !== String(defaultValue)
    ));
    const hasSearch = Boolean(fieldValue(controls.search).trim());

    if (count) {
      count.textContent = String(selected.length);
      count.hidden = selected.length === 0;
    }
    if (toggle) {
      toggle.setAttribute(
        "aria-label",
        selected.length ? `${toggleLabel}, ${selected.length} active` : toggleLabel,
      );
    }
    if (resetButton) resetButton.hidden = !hasSearch && selected.length === 0;
    if (activeFilters) {
      activeFilters.hidden = selected.length === 0;
      activeFilters.innerHTML = selected.map(({ key, label }) => `
        <button class="active-filter" type="button" data-filter-key="${escapeHtml(key)}"
          aria-label="Remove ${escapeHtml(label)} filter: ${escapeHtml(selectedOptionLabel(controls[key]))}">
          <span>${escapeHtml(label)}: ${escapeHtml(selectedOptionLabel(controls[key]))}</span>
          <span class="active-filter__remove" aria-hidden="true">×</span>
        </button>`).join("");
    }
  }

  return {
    read: queryState.read,
    write: queryState.write,
    update,
    close,
    destroy() {
      queryState.destroy();
      toggle?.removeEventListener("click", handleToggle);
      activeFilters?.removeEventListener("click", handleChip);
      document.removeEventListener("keydown", handleEscape);
      if (compact?.removeEventListener) compact.removeEventListener("change", handleBreakpoint);
      else compact?.removeListener?.(handleBreakpoint);
    },
  };
}
