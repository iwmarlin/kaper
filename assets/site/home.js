import { mountSiteChrome } from "./core.js?v=aa2642b3e5";

// Every home-page section is printed into the document at build time, so this
// page makes no data request and reads the same with or without JavaScript.
mountSiteChrome("home");
