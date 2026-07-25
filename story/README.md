# Realmbound encounter editor

Open **[`encounter-guide.html`](encounter-guide.html)** for the complete visual guide.

The guide explains:

- what every part of `encounters.json` does;
- how to add a battle to Python and HTML5;
- every supported encounter field;
- fixed money, random money, and item rewards;
- where encounters run;
- current limitations;
- JSON validation and testing;
- common errors and how to fix them.

## Critical rule

Every custom encounter must include:

```json
"user_added": true
```

Without that field, the encounter generator may remove the custom entry later.
