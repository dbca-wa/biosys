With Django extensions installed:
To run in update mode
`./manage.py runscript legacy.LCI.import_legacy_data`
To run in fresh mode (all previous data are deleted)
`./manage.py runscript legacy.LCI.import_legacy_data --script-args=fresh`