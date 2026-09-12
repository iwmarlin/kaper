# Individual life-date review — 9 September 2026

No birth or death year was changed. Only Fernand Vimont's unsupported `disputed` status was changed to `confirmed`.

| Person | Decision | Evidence and limits |
| --- | --- | --- |
| P003 Andrzej Włast | Retain disputed, 1895–1943 | SRC0623 documents ISNI's 1895; GND 1203212704 still gives 17 March 1885. The existing conflict assessment remains applicable. |
| P065 René Pujol | Retain disputed, 1878–1942 | SRC0613 / ECMF gives 15 May 1878; GND 1062158474 gives 18 August 1888. Both give 21 January 1942. |
| P090 Giuliano Pomeranz | Retain disputed, 1900–1996 | Rupeikaitė, SRC0546, note 20, pp. 53–54, gives 1900–1996. The Arolsen listing, SRC0545, explicitly identifies Giuliano, born in Wilno on 21 March 1901. This review checked the listing, not the underlying personal-file scans. |
| P110 Fernand Vimont | Confirm 1904–1981 | New SRC0856: BnF FRBNF16440429 gives 21 April 1904 – 8 June 1981 and cites INSEE death-register data. Its current authority record was retrieved through the BnF SRU service; Fri-Memoria independently displays the same years. The prior record carried no documented alternative dates. |
| P139 Jeanette MacDonald | Retain disputed, 1903–1965 | New SRC0857: BnF FRBNF13757145 gives 1903-06-18? and 1965-01-14?; GND 119403277 still gives 1907-06-18 and 1965-01-14. The BnF question marks are reported explicitly. This is a conflict between the cited authorities, not a new claim that 1907 is the correct birth year. |
| P162 Paul Kohner | Retain disputed, 1902–1988 | New SRC0858: Filmportal gives 29 March 1903; GND 116308869 gives 29 March 1902. Both give 16 March 1988. Neither source was silently preferred as a resolution of the conflict. |

GND machine-readable records were consulted via `https://lobid.org/gnd/{identifier}.json`. BnF's Vimont authority record is `https://catalogue.bnf.fr/ark:/12148/cb16440429b`; the record explicitly cites INSEE via Open Archives. This review did not independently inspect a civil birth certificate.

## Publication rules

`lifeDatesNote` is plain text; `lifeDatesSourceIds` is a curated subset of the person's existing `sourceIds`, not a second independent graph edge. Both are allowlisted as editorially derived fields. The ordinary Sources–People relationship remains bidirectional.

Both the exporter and public-data validator reject `disputed` without a public explanation, an explanation without evidence, malformed or duplicate evidence references, and evidence not linked through `sourceIds`. The normal graph validator checks that those Sources exist.

The shared renderer displays the note and source-record links immediately below the person facts, in “Life dates and evidence”, in both static HTML and the JavaScript view. Other person cards are unchanged. New Sources link back to People and the existing BnF/DFF organizations; no People, Organizations, Media or Contributions were added.
