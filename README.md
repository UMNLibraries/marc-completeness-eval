# marc-completeness-eval
A script to evaluate the completeness of MARC records across a file of records

This script scores each record in either all MARC binary files in a directory, or a single
file input by the user based on the presence or absence of several elements, and 
calculates mean and standard deviation across all record scores in a file. Outputs: 
one .csv file per MARC file evaluated. Full description and rubric available in
"Leveraging Python to improve ebook metadata selection, ingest, and management," 
Kelly Thompson and Stacie Traill, Code4Lib Journal Issue 38, 2017-10-18. 
https://journal.code4lib.org/articles/12828

This work is copyright (c) the Regents of the University of Minnesota, 2017. 
It was created by Stacie Traill and last updated 2018-10-30.