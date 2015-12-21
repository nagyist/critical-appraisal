Critical Appraisal Parser
=========================

Python 3 parser for a very specific CSV format containing evidence based medicine references.

CSV Export
----------

CSV must be exported with **UTF-8** encoding.
Name the file `CriticalAppraisal.py`.

Website Title
-------------

You can change the title of the generated website by putting a file `title.txt` containing your desired title into the main directory.
If no such file is found the title defaults to “Evidence Synopsis Information”.

Running
-------

Must use Python 3 for reliable utf-8 recognition.
Place `CriticalAppraisal.py` in the same directory, then run the following command or simply double-click `create.command`:

```bash
python3 parse.py
```

The HTML file `CriticalAppraisal.html` will be put in the same directory.
