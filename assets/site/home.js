import { mountSiteChrome } from "./core.js?v=6fca9bc909";

// Every home-page section is printed into the document at build time, so this
// page makes no data request and reads the same with or without JavaScript.
mountSiteChrome("home");
