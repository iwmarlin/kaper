import { mountSiteChrome } from "./core.js?v=6658d19bfb";

// Every home-page section is printed into the document at build time, so this
// page makes no data request and reads the same with or without JavaScript.
mountSiteChrome("home");
