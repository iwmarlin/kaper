import { escapeHtml } from "./core.js?v=c77ada42a0";

const INDEX_RETURN_PREFIX = "kaper:index-return:";

/* Record URLs stay canonical and shareable; the reader's catalogue context is
   kept separately for the lifetime of the browser tab.  Only known local
   index files can be written or restored, so storage can never turn a record
   breadcrumb into an open redirect. */
export const RECORD_INDEXES = Object.freeze({
  work: {
    file: "works.html",
    label: "Works",
    filterKeys: ["search", "type", "period", "certainty"],
    backLabel: "Back to Works",
    filteredBackLabel: "Back to filtered Works",
  },
  person: {
    file: "people.html",
    label: "People",
    filterKeys: ["search", "role", "period"],
    backLabel: "Back to People",
    filteredBackLabel: "Back to filtered People",
  },
  media: {
    file: "media.html",
    label: "Media",
    filterKeys: ["search", "category", "period", "rights", "scope"],
    backLabel: "Back to Media",
    filteredBackLabel: "Back to filtered Media",
  },
  source: {
    file: "sources.html",
    label: "Sources",
    filterKeys: ["search", "type", "dateRole", "access"],
    backLabel: "Back to Sources",
    filteredBackLabel: "Back to filtered Sources",
  },
  event: {
    file: "life.html",
    label: "Timeline",
    filterKeys: ["search", "category"],
    backLabel: "Back to Timeline",
    filteredBackLabel: "Back to filtered Timeline",
  },
  place: {
    file: "map.html",
    label: "Map",
    filterKeys: ["search", "place"],
    backLabel: "Back to Map",
    filteredBackLabel: "Back to saved Map view",
  },
});

function matchingIndexUrl(recordType, value = null) {
  const config = RECORD_INDEXES[recordType];
  if (!config || typeof window === "undefined" || typeof document === "undefined") return null;
  try {
    const expected = new URL(config.file, document.baseURI);
    const candidate = value === null
      ? new URL(window.location.href)
      : new URL(String(value), document.baseURI);
    if (candidate.origin !== expected.origin || candidate.pathname !== expected.pathname) return null;
    return candidate;
  } catch {
    return null;
  }
}

export function rememberIndexLocation(recordType) {
  const config = RECORD_INDEXES[recordType];
  const current = matchingIndexUrl(recordType);
  if (!config || !current) return;
  try {
    window.sessionStorage.setItem(
      `${INDEX_RETURN_PREFIX}${recordType}`,
      `${config.file}${current.search}${current.hash}`,
    );
  } catch {
    // Private browsing and local-file policies may disable storage. The
    // canonical index link remains fully functional in that case.
  }
}

export function recordIndexReturn(recordType) {
  const config = RECORD_INDEXES[recordType];
  if (!config) return null;
  let candidate = null;
  try {
    candidate = matchingIndexUrl(
      recordType,
      window.sessionStorage.getItem(`${INDEX_RETURN_PREFIX}${recordType}`),
    );
  } catch {
    candidate = null;
  }
  if (!candidate) candidate = matchingIndexUrl(recordType, config.file);
  const href = candidate
    ? `${config.file}${candidate.search}${candidate.hash}`
    : config.file;
  const params = candidate?.searchParams || new URLSearchParams();
  const isFiltered = config.filterKeys.some((key) => params.has(key) && params.get(key) !== "");
  return {
    ...config,
    href,
    isFiltered,
    resolvedBackLabel: isFiltered ? config.filteredBackLabel : config.backLabel,
  };
}

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
  indexType = null,
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
    if (indexType) rememberIndexLocation(indexType);
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
  indexType = null,
}) {
  const defaults = Object.fromEntries(Object.keys(controls).map((key) => [key, ""]));
  for (const option of options) defaults[option.key] = option.defaultValue;
  const queryState = createQueryState(controls, { defaults, onRestore, indexType });
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
