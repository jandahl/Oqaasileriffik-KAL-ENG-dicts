# COLUMN_MAP Notes

Inspected against: 2018 Chicago/A.ods (re-verify on upstream updates)

| Key          | Col | ODS Header (Danish) | Notes                        |
|--------------|-----|---------------------|------------------------------|
| lexeme       |  0  | "Kalaallisut"       | citation form, always present |
| word_class   |  1  | "Ordklasse"         | N / V / Prop etc.             |
| stem         |  2  | "Stamme"            | may be empty → falls back to lexeme |
| valence      | -1  | n/a                 | not present in these files    |
| sandhi_type  | -1  | n/a                 | not present in these files    |
| gloss_en     |  3  | "Engelsk"           | English gloss                |
