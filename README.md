# Employee Weekly Timesheet

A printable weekly timesheet web app for **Aimex Homecare Services**. Employees
enter shift times; the sheet totals daily and weekly hours and is tuned to print
cleanly on a single **A3** page across Chrome, Firefox, and Safari.

**Live site:** https://ohuru-ian.github.io/employee-timesheet/

## Features

- Weekly grid (Sunday–Saturday) with **fixed day names** and **auto-filled dates**
- Multiple shifts per day with automatic hour totals
- **Locked fields** (day names, dates, signature dates) to prevent accidental edits
- Employee & supervisor signatures (type or draw)
- One-page print output, consistent across browsers

## Project structure

| File | Purpose |
|------|---------|
| `index.html` | The live timesheet page |
| `timesheet_template.html` | Template used to generate filled sheets |
| `generate_timesheet.py` | Generates an HTML timesheet from a JSON file |
| `timesheet_schema.json` | JSON schema for the input data |
| `sample_timesheet_agnes_2025-10-19.{html,json}` | Example sheet and data |

## Generating a sheet

```bash
python generate_timesheet.py data.json -o output.html
```

## License

**Proprietary — All Rights Reserved.** See [LICENSE](LICENSE). This code may not
be copied, reused, or redistributed without written permission.

© 2025–2026 Ian Ohuru (OHURU-IAN). Contact: ohuruian@gmail.com
