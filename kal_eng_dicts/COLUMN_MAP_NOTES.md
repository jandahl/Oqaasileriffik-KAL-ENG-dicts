# COLUMN_MAP Notes

Inspected against: `2018 Chicago/A.ods` — re-verify if upstream files are updated.

Headers are in **Kalaallisut** (not Danish). Column 2 header `"Tuluttuua"` is used
as a sheet-identity marker: `is_gloss_sheet()` skips any sheet whose col-2 header
differs from `"Tuluttuua"`. This correctly excludes `principal parts1`, `Copy of Gloss`,
`Ark1`, and other auxiliary sheets that appear in some ODS files.

Word-class lookup is case-insensitive (lowercased before dict lookup).

## Column mapping

| Key          | Col | ODS Header (Kalaallisut)             | Notes                                           |
|--------------|-----|--------------------------------------|-------------------------------------------------|
| lexeme       |  0  | "Ujartugassaq" / "Kalaallisut"       | citation form, always present                   |
| word_class   |  1  | "Suussusaa" / "Suussusia"            | Kalaallisut terms, mapped in WORD_CLASS_TO_PATH |
| stem         | -1  | n/a                                  | no stem column; falls back to lexeme            |
| valence      | -1  | n/a                                  | not present in these files                      |
| sandhi_type  | -1  | n/a                                  | not present in these files                      |
| gloss_en     |  2  | "Tuluttuua"                          | English gloss (tuluttut = English, -ua = its)   |

## Word-class values observed (col 1)

Values are from the Kalaallisut-language ODS files. Several typos and variant
spellings were found across different lettered files; these are mapped explicitly
in `WORD_CLASS_TO_PATH` with inline comments.

| ODS value (lowercased)                          | class_path                       | Notes            |
|-------------------------------------------------|----------------------------------|------------------|
| taggit                                          | nominal_root / common_noun       | loanword         |
| taggit qasseersiut                              | nominal_root / common_noun       | plural-only loan |
| taggit ataasersiut                              | nominal_root / common_noun       | singular-only    |
| taggit atiusoq                                  | nominal_root / proper_noun       |                  |
| taggit qasseersiut (ataas inuak/qajaq/saaneq/sanik) | nominal_root / common_noun  | parenthetical variants |
| taggit (naal qupp.)                             | nominal_root / common_noun       |                  |
| proprium/egennavn                               | nominal_root / proper_noun       | mixed KAL/DA     |
| stednavn                                        | nominal_root / proper_noun       | Danish: place name |
| oqaluut                                         | verbal_root                      |                  |
| oqaluut susaatsoq                               | verbal_root / transitive         |                  |
| oqaluut susaatsoq qasseersiut                   | verbal_root / transitive         | plural-only verb |
| oqaluut susaatsoq (taggit)                      | verbal_root / transitive         |                  |
| oqaluut susaatsoq plus htr??                    | verbal_root / transitive         | annotated        |
| oqaluut susalik                                 | verbal_root / intransitive       |                  |
| oqaluut susaasalik                              | verbal_root / intransitive       |                  |
| oqaluut susalik (oqaluut susaasalik)            | verbal_root / intransitive       |                  |
| oqaluut aappiuttartoq                           | verbal_root                      |                  |
| oqaluut pisimasorsiut                           | verbal_root                      |                  |
| oqaluut taggisaasaq                             | verbal_root                      |                  |
| oqaluut inatsiniut                              | verbal_root                      | legal term       |
| o/i                                             | verbal_root / intransitive       | English abbrev.  |
| oqaaseeraq                                      | enclitic                         |                  |
| oqaaseeraq kattut                               | enclitic                         |                  |
| oqaaseeraq oqaqqarniut                          | enclitic                         |                  |

## Unmapped values (12 entries, ~0.07% of total)

These cannot be safely mapped without deeper linguistic expertise and are left
with `class_path: []`. They produce WARNING log lines.

| ODS value               | File / row              | Reason unmapped         |
|-------------------------|-------------------------|-------------------------|
| t                       | K.ods row 79            | too truncated to resolve |
| naal.                   | M.ods row 623           | unclear abbreviation    |
| o (×4)                  | S.ods rows 923-938      | too truncated to resolve |
| t king                  | S.ods row 1710          | unclear                 |
| naleqq ilaalu ilanngullugit | I.ods row 1472      | complex Kalaallisut phrase |
| naleqq qupperneq i      | Q.ods row 1642          | complex phrase          |
| naleqq sapaatip-akunnera | S.ods row 353          | complex phrase          |
| naleqq soorlu imaattoq/soorlu imaattut | S.ods row 670 | complex phrase    |
| naleqq Sulinermik Inuissutissarsiuteqartut Kattuffiat | S.ods row 775 | proper noun of org |
