import { mountSiteChrome } from "./core.js?v=bdeddea7d3";

// Every home-page section is printed into the document at build time, so this
// page makes no data request and reads the same with or without JavaScript.
mountSiteChrome("home");
