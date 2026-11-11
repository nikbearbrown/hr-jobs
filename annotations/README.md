# Hand annotations

`overrides.csv` is where a person corrects the classifier. One row per listing:

| Column | What goes in it |
|---|---|
| `key` | The listing's `key` from `data/current/jobs.csv` |
| `sub_discipline` | One of: academic_personnel, military_hr, labor_relations, employee_relations, eeo, compensation, benefits_leave, talent_acquisition, learning_od, hris_analytics, payroll, hr_operations, hr_strategy, generalist, unclassified |
| `note` | Why (optional) |
| `annotated_by`, `date` | Who and when (optional) |

On the next run the listing takes the sub-discipline given here, and its `classified_by` column reads `annotation`.
A row whose sub-discipline is not in the list is ignored.

The listings that most need a person are the ones marked `unclassified` in `jobs.csv`: their titles say only "HR"
and their ad text did not settle the function.
