"""PDF and XLSX generators for the Reporting module.

The generators consume a fully-composed ``ExecutiveReportData`` payload
(built by ``ReportingService``) and stream bytes back to the caller.
The generators do not touch the database directly — all SQL lives in
``ReportingRepository``.

The PDF generator uses ``reportlab`` and the XLSX generator uses
``openpyxl`` — both are added to ``pyproject.toml``.
"""
