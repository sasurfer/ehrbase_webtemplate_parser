# Webtemplate Parser for EHRBase 
parse an EHRBase webtemplate and return one of:
1. All info for each leaf defined in the webtemplate  (use type_of_output=all)
2. The path in FLAT format vs the original path in the webtemplate node (use type_of_output=flatpath)
3. An example composition with all the leafs instantiated (use type_of_output=composition)

## 1. Requirements
Any Python v3 will do.

## 2. Parameters
| parameter  | Description              | values |  mandatory |
| ---------  | -----------              | ------ |   ------ |
| inputfile  | path to webtemplate file (produced by EHRBase) | e.g., ~/mywebtemplate.json | yes |
| outputfile | path to output filename  | e.g., ~/parsing_output |  yes  |
|type_of_output | output type chosen    | one of [all, flatpath, composition]  | no (default=all) |

## 3. How to run
From the code directory to obtain a composition in FLAT format for EHRBase:
```
python3 Webtemplate_parser.py --inputfile {full_path_to_webtemplate_file} --outputfile {full_path_to_output_file} --type_of_output composition
```

## 4. Output
### 4.1 type_of_output=all
We obtain rows like:
```
1) category, category, /category, category, DV_CODED_TEXT, [{'list': [{'label': 'event', 'localizedLabels': {'en': 'event'}, 'value': '433'}], 'suffix': 'code', 'terminology': 'openehr', 'type': 'CODED_TEXT'}], []
```
Meaning of each leaf/row:

| index | id   | name | webtemplate_path | FLAT_path | rm_type | inputs | children |
| ----  | ---- | ---- | -----            | ----      | ----    | ----   |  ------  |
|  1\)   | category |  category | /category | category | DV_CODED_TEXT | ```[{'list': [{'label': 'event', 'localizedLabels': {'en': 'event'}, 'value': '433'}], 'suffix': 'code', 'terminology': 'openehr', 'type': 'CODED_TEXT'}]``` |  [] |
### 4.2 type_of_output=flatpath
The result, for each leaf, is a dictionary with mapping between FLAT and webtemplate paths, which can be useful to find the webtemplate path to put in queries. A row will look like:
```
  "interhealth_cancer_registry/category": "/category",

  FLAT path -> webtemplate path
```
### 4.3 type_of_output=composition
A composition in FLAT format is obtained with all the leafs instantiated:
```
{
  "interhealth_cancer_registry/category|code": "433",
  "interhealth_cancer_registry/category|value": "event",
  "interhealth_cancer_registry/category|terminology": "openehr"
  ......
```

# Acknowledgments
This work has been partially funded by the the following sources:
<ul>
<li>“Total Patient Management” (ToPMa) project (grant by the Sardinian Regional Authority, grant number RC_CRP_077);</li>
<li>the “Processing, Analysis, Exploration, and Sharing of Big and/or Complex Data” (XDATA) project (grant by the Sardinian Regional Authority).</li>
</ul>
