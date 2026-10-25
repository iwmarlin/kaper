"""Reviewed editorial rules for online database and lexicon entries.

A citation identifies an entry; its biographical contents and identity
assessment belong in researchNote. Explicit reviewed notes preserve the
existing evidence instead of discarding it during citation normalization.
"""

from typing import Any


REVIEWED_DATABASE_FIELDS: dict[str, dict[str, Any]] = {
    "SRC0816": {
        "fullCitation": "Józef Kański. “Śmidowicz, Józef.” Encyklopedia, Polska Biblioteka Muzyczna. Polskie Wydawnictwo Muzyczne, 2023.",
        "researchNote": "Entry for the pianist and teacher (Zhytomyr, 2 September 1888 – Warsaw, 10 June 1962): pupil of Aleksander Michałowski at the Warsaw Music Institute, 1905–13; professor of piano at the school of the Warsaw Music Society from 1918, from 1919 the Fryderyk Chopin Higher School of Music, a post he held until 1950; professor at the State Higher School of Music in Warsaw from 1951 and dean of its piano faculty 1953–59; juror of the first three International Chopin Competitions. The entry names Kaper among Śmidowicz’s pupils, beside Władysław Szpilman, Witold Lutosławski, Leon Boruński and Wacław Grzybowski. It is an independent witness to the teaching relation that the archive otherwise documents through the school concert of June 1925, and it establishes what was taught: piano, in Śmidowicz’s class at the Chopin school."
    },
    "SRC0818": {
        "fullCitation": "Société des auteurs, compositeurs et éditeurs de musique. “Léo Lelièvre (fils).” Musée SACEM, Les créateurs, creator record 3449.",
        "researchNote": "Born 9 June 1899 in Paris, died 21 June 1966 in Prague; admitted to SACEM as author on 13 November 1919 and as composer on 21 April 1927, elected full member in 1927; Prix Ferny, 1939. The society through which both men licensed their work distinguishes the son by the qualifier “fils” and dates his membership from 1919, ten years before the first Casino de Paris covers that carry that qualifier. The place of death, Prague, is recorded here alone among the authority files consulted."
    },
    "SRC0819": {
        "fullCitation": "Société des auteurs, compositeurs et éditeurs de musique. “Jean Féline.” Musée SACEM, Les créateurs, creator record 3854.",
        "researchNote": "Lyricist, screenwriter and dialogue writer, born 30 October 1908 in Saumur, died 17 January 1945 in Paris; admitted to SACEM as author on 1 May 1935. The membership register gives 30 October 1908 as the date of birth, agreeing with the Paris death certificate of January 1945 and superseding the tentative year 1912 carried by the BnF heading. Admission as an author on 1 May 1935 establishes the date of his SACEM membership, not the beginning of his professional songwriting career.",
        "accessDate": "2026-10-25"
    },
    "SRC0822": {
        "fullCitation": "Société des auteurs, compositeurs et éditeurs de musique. “Jacques Monteux.” Musée SACEM, Les créateurs, creator record 3868.",
        "researchNote": "Dialogue writer and lyricist, born in Paris on 5 November 1899, died 7 April 1979; admitted to SACEM on 2 March 1926 and elected full member on 8 April 1933. The biography spells the surname “Monteaux” while the heading of the same record, the membership photograph and the authority files read Monteux. The dates of birth and death agree with the authority files to the day. His admission on 2 March 1926 predates by seven years the two Kaper and Jurmann songs he wrote for the French version of “Madame ne veut pas d’enfants”."
    },
    "SRC0823": {
        "fullCitation": "Société des auteurs, compositeurs et éditeurs de musique. “Henri Varna.” Musée SACEM, Les créateurs, creator record 2689.",
        "researchNote": "Author, born in Marseille on 31 October 1887, died in Paris on 10 April 1969; elected full member of SACEM on 30 August 1918. The membership register dates his election as a full member to 1918, nine years before he took over the direction of the Casino de Paris, and gives his birth and death to the day."
    },
    "SRC0824": {
        "fullCitation": "Société des auteurs, compositeurs et éditeurs de musique. “André de Badet.” Musée SACEM, Les créateurs, creator record 2993.",
        "researchNote": "Author, born at Escos on 30 June 1891, died at Clamart on 7 April 1977; elected full member of SACEM as author on 29 April 1933; Prix Célestin Joubert, 1964. The society dates his standing as a full member from April 1933, the season of the French songs he wrote for Kaper and Jurmann, and confirms the places of birth and death that the authority heading leaves out."
    },
    "SRC0825": {
        "fullCitation": "Société des auteurs, compositeurs et éditeurs de musique. “Louis Poterat.” Musée SACEM, Les créateurs, creator record 3842.",
        "researchNote": "Author, born at Troyes on 2 June 1901, died at Geneva on 6 January 1982; elected full member of SACEM on 27 April 1928; administrator of SACEM, vice-president and secretary general of the SDRM; Prix Albert Willemetz, 1946. Besides the dates, the register records the offices he later held in the society and in the mechanical rights body, which no other record consulted for him mentions."
    },
    "SRC0826": {
        "fullCitation": "Société des auteurs, compositeurs et éditeurs de musique. “Marc Cab.” Musée SACEM, Les créateurs, creator record 3141.",
        "researchNote": "Author, born at Nice on 11 December 1901, died at Bandol on 18 October 1978; admitted to SACEM as author on 21 November 1923; Prix Albert Willemetz, 1949. The society spells the name without a hyphen and supplies the places of birth and death, which the authority heading reduces to years alone."
    },
    "SRC0827": {
        "fullCitation": "Société des auteurs, compositeurs et éditeurs de musique. “René Nazelles.” Musée SACEM, Les créateurs, creator record 4243.",
        "researchNote": "Author and composer, born in Paris on 8 October 1888, died on 11 September 1975; elected full member of SACEM on 13 September 1911; Prix Salabert, 1958. The register settles the life dates that the BnF heading still gives as an open span, agreeing with the years recorded by the film and record databases, and dates his standing in the society from 1911."
    },
    "SRC0828": {
        "fullCitation": "Société des auteurs, compositeurs et éditeurs de musique. “Charles-Louis Pothier.” Musée SACEM, Les créateurs, creator record 3084.",
        "researchNote": "Author, born at Bordeaux on 18 April 1881, died at Clichy on 3 November 1962; elected full member of SACEM on 17 February 1912; Prix Trebitsch, 1943; Prix Albert Willemetz, 1947; Prix Centenaire, 1950; Prix Célestin Joubert, 1956; Grand Prix de la Chanson, 1958. The list of society prizes, running from 1943 to 1958, documents a standing in the profession that the catalogue records do not show, and the register confirms the places of birth and death."
    },
    "SRC0684": {
        "fullCitation": "Uwe Harten. “Gmeindl, Walter.” Oesterreichisches Musiklexikon online. Vienna: Verlag der Österreichischen Akademie der Wissenschaften. Last content update 25 April 2003. doi:10.1553/0x0001cf41.",
        "date": "2003-04-25",
        "dateRole": "record_update",
        "dateQualifier": "confirmed",
        "dateDisplay": "25 April 2003 (content update)",
        "accessDate": "2026-10-25",
        "researchNote": "The article presents Gmeindl primarily as a pedagogue. It gives 31 December 1890 at Hainburg an der Donau as his date of birth and 1 September 1958 at Hainburg as his date of death, and traces his appointments at the Munich Hofoper from 1915. Schreker engaged him in Berlin as a Dozent in 1922 and, in 1929, as professor of composition and head of the orchestra school of the Musikhochschule, where he later took the conducting class as well; Sergiu Celibidache and Ernst Pepping were among his pupils. It is the teaching post held during Kaper’s Berlin years, which the archive documents in the event of private study, 1926–1930. The lexicon spells the forename Walter, without the h in the archive’s person record. The live entry explicitly labels 25 April 2003 as “Letzte inhaltliche Änderung” (last content update). This is the date recorded here; it is not an independently established first-publication date."
    }
}


def normalize_database_source(source: dict[str, Any]) -> None:
    """Restore item-specific, reviewed fields without inferring new evidence."""
    fields = REVIEWED_DATABASE_FIELDS.get(str(source.get("id", "")))
    if fields:
        source.update(fields)

