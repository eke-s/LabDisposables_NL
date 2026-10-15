# NFU Labs Disposables

Laboratory disposables are essential for diagnostics and research, but they also contribute to resource consumption, waste generation, and climate change. As time and capacity for sustainability initiatives are limited, insight is needed into which products and reduction measures should be prioritized. Therefore, this study developed a methodology to estimate the climate and environmental impacts of laboratory disposables.

The analysis was based on procurement data from 2024 from all seven Dutch University Medical Centers (UMCs), comprising 190.025 purchase orders. A total of 78 laboratory disposable product categories were defined. Laboratory consumables, reusable products, and equipment were excluded. Purchase orders are automatically classified in a stepwise manner into one of the 78 product categories or excluded. First, products are matched to a custom product database using article numbers to determine whether they are known. For unknown products, the product category is predicted using a neural network with a confidence threshold of 0.7. Finally, several recurring prediction errors are corrected using RegEx pattern recognition.

Subsequently, the following product characteristics are corrected and enriched within the procurement data: number of items per package, dimensions, volume, sterility, and material composition. Each purchased product is assigned to a proxy product (subcategories within the product categories) to estimate product weight based on collected weight data. Climate impacts are estimated based on material use, product weight, manufacturing processes, and sterility requirements.

The results from the Dutch UMCs showed that twelve product categories together accounted for more than 80% of the total estimated climate impact. These categories also contributed substantially to the other environmental impact indicators examined in the study. The report identifies promising reduction measures for these categories. Broadly applicable strategies included avoiding unnecessary use, enabling safe reuse where feasible, selecting smaller or appropriately sized products, and adopting refill systems and bulk packaging. The impact and feasibility of these recommendations depend on local workflows, quality requirements, and safety conditions within individual healthcare institutions.

**SCOPE: please be aware that the presented methodology was developed in the context of Dutch Univeristy Medical Centers. When using the code outside of this context, the results should be carefully examined to assess validity. This holds true especially for the predictions of the neuronal network, but also for the coverage of data from other contexts in the RegEx patterns and proxy-products. An external validation and optimization project will be performed in the 1st half of 2027. Code will be updated subsequently.**

The full methodology can be found in the (Dutch) report: Landelijke Inventarisatie Klimaatimpact van Laboratoriumdisposables in de Universitaire Medische Centra (2026). Kat, R., Snoeren, E., Snijder, L., de Haas, A., Noort, B., UMCNL-werkgroep Circulaire Bedrijfsvoering. Funded by: Green Deal Duurzame Zorg: https://www.greendealduurzamezorg.nl/

<!-- Table of Contents -->
# Table of Contents

- [Getting Started](#getting-started)
  * [Requirements](#requirements)
  * [Input Data](#input-data)
  * [Running The Code](#running-the-code)
  * [Expected Output Data](#expected-output-data)
- [Optionals](#optionals)
  * [Sterility](#sterility)
  * [Price Analysis](#price-analysis)
- [Troubleshooting](#troubleshooting)
  * [Sentence Transformers](#sentence-transformers)
  * [Outliers](#outliers)
  * [Other Data](#other-data)
- [Weight Data](#weight-data)
- [Further Plans & Updates](#further-plans-&-updates)
- [Authors Contact Information](#authors-contact-information)


<!-- Getting Started -->
## Getting Started

If you do not have python or VSCode installed, you can find the downloading information here (both programs must be installed seperately):
- VSCode: https://code.visualstudio.com/
- Python: https://www.python.org/downloads/

Download the code from this repository, and navigating into the projectfolder in the terminal (within VSCode for example), such that the path looks like this:
```bash
PS C:\Path\To\The\Folder\LabDisposables_NL-main>
```
### Requirements

This code was developed and tested using (newer versions of python might clash with the packages):

- **Python:** 3.11.9

The required Python packages are listed in the `requirements.txt` file, a few packages are quite big (500+ MB) so adequate space will be needed on your computer/laptop. Installation:
```bash
pip install -r requirements.txt
```
If this does not work, try:
```bash
python -m pip install -r requirements.txt
```

### Input Data

Input data has to be formatted as such (see `Example_Data.xlsx`, sheet `Input Data Template`), 'Missing Value Handling' shows what happens to rows missing a value for this column:

| Column Name | Description | Expected Format | Required? | Missing Value Handling |
|---|---|---|:---:|---|
| `index` | row index | Numeric | No | |
| `artikelnummer` | article number from supplier for identification | Text | Yes | database will not work |
| `leverancier` | supplier of article | Text | No | |
| `omschrijving` | description of article | Text | Yes | prediction model will not work |
| `verpakking_besteld` | number of packages ordered of article | Numeric | Yes | row will be removed |
| `type_verpakking` | type of packaging (see input variables 'in_eenheden' and 'in_paren') | Text | No | |
| `stuks_per_verpakking` | number of articles in a package | Numeric | No | |
| `prijs_per_bestelregel` | total price for order (all packages) | Numeric | No | |
| `prijs_per_verpakking` | total price per package | Numeric | No | |

If data for non-required columns is unavailable, the column should be included in the input data as an empty column, not omitted entirely.

### Running The Code

In `main.py` (line 242) it is required to add/change the input variables:
```python
if __name__ == "__main__":
    run_pipeline(
        path_input = r"C:\Put\Input\Path\Here", #Put the path to the input data here
        in_eenheden =['piece', 'stuks', 'fles', 'STU', 'FLE', 'ST', 'STK', 'FL', 'ROL', 'Stuks', 'STR'], #Put/add type_verpakking which are singular
        in_paren = ['paar'], #Put/add type_verpakking which are pairs
        steriliteit_toevoegen = False, #Change to 'True' when desired to include environmental impact approximation of sterilisation
        price_analysis = False, #Change to 'True' when desired to add price analysis (see Troubleshoot: Price Analysis in READ_ME file)
        use_existing_price_median = False) #Change to 'True' when 'prijs_per_stuk_medians.xlsx' has been created (see Troubleshoot: Price Analysis in READ_ME file)
```
notes:
- path_input = make sure that the input data is in the right format
- in_eenheden = any rows where `type_verpakking` is found in `in_eenheden` it is assumed that `verpakking_besteld` is the total number of articles ordered, and won't be multiplied by `stuks_per_verpakking`. The already provided text for `in_eenheden` is based on our data and must be changed/expanded on based on the abbreviations found in your own data
- in_paren = any rows where `type_verpakking` is found in `in_paren` it is assumed that `verpakking_besteld` is the total number of pairs ordered, and will be multiplied by 2 instead of by `stuks_per_verpakking`. The already provided text for `in_paren` is based on our data and must be changed/expanded on based on the abbreviations found in your own data
- steriliteit_toevoegen = when changed to 'True' an approximation of the environmental impact of sterilisation will be added to the rows found to be sterile by our model
- price_analysis = when changed to 'True' our price analysis will be applied to your data, this can only be used when either `prijs_per_bestelregel` or `prijs_per_verpakking` has been (partially) filled with data (see section Price Analysis for further explanation)
- use_existing_price_median = when changed to 'True' our price analysis will be applied to your data with the modifications made in `prijs_per_stuk_medians.xlsx`, this can only be used when either `prijs_per_bestelregel` or `prijs_per_verpakking` has been (partially) filled with data (see section Price Analysis for further explanation)

After changes are made to `main.py`, be sure to save the file before continuing. When completed, the pipeline can be ran, by using the following code in your terminal (within VSCode for example):
```bash
python main.py
```
While the code is running it will update you on the progress made, within the pipeline. Some warnings might appear (see the red box in the screenshot), these are normal. It should look like this:
<img width="822" height="307" alt="image" src="https://github.com/user-attachments/assets/f563707e-aed6-4da6-a1dc-6a9c4c512c50" />



### Expected Output Data
The output of the pipeline can be found in the folder /results (created when running main.py):
- `lab_disposables_summary.xlsx`: output data summarized per category (see `Input_Data_Format.xlsx`, sheet `Output Columns Explained` for explanation for each column in this file)
- `lab_disposables_full_output.xlsx`: output data with all rows included (not summarized) (see `Example_Data.xlsx`, sheet `Output Columns Explained` for explanation for each column in this file)
- `top12_aantallen`: bar chart showing top 12 laboratorium disposables for number of items
- `top12_milieu_impact`: bar chart showing top 12 laboratorium disposables for environmental impact
- `cumulative_milieu_impact`: cumulative percentages for each categories, showing the top 80% for environmental impact

## Optionals

### Sterility
Sterility is a bonus for environmental impact, which can be added to the pipeline by setting the input variable `steriliteit_toevoegen` to `TRUE`. In our data, for rows where the item was found to be sterile the sterility made up 0,38% - 1,95% of the total enivronmental impact. The sterility bonus did not change our results in a meaningful way.

### Price Analysis
Price Analysis makes a correction in the number of items within a row. We assume that `verpakking_besteld` are the number of packages ordered, unless the `type_verpakking` value is found within `in_eenheden` (or `in_paren`). In that case it is assumed that `verpakking_besteld` are the total number of items ordered. 

When price information is provided (`prijs_per_bestelregel` or `prijs_per_verpakking`), a correction can be done to account for rows where `verpakking_besteld` is truly the total number of items ordered, without `type_verpakking` being present in `in_eenheden` or `in_paren`. This can have a substantial influence on the output, as shown in our final results:

#### Before price analysis
<img width="1389" height="590" alt="Supp figuur 2" src="https://github.com/user-attachments/assets/5e49709e-44e3-4577-8083-f782ee0b6fe1" />

#### After price analysis
<img width="1389" height="590" alt="Supp figuur 1" src="https://github.com/user-attachments/assets/e29de764-ebb6-4260-ad19-1ffc8dc14f0a" />

The price analysis can be implemented by setting the input variable `price_analysis` to `TRUE`. It calculates the price per item (based on `prijs_per_bestelregel` or `prijs_per_verpakking`) and the median price per item for each category (it also calculates the `prijs_per_verpakking`, when there is only `prijs_per_bestelregel`). Then it compares the price per item and `prijs_per_verpakking` with the median price per item for each row, in rows where `prijs_per_verpakking` is closer to the median, it is assumed that the `verpakking_besteld` is actually the total number of items ordered.

The median price per item for each category is given as an output as `prijs_per_stuk_medians.xlsx`. The median price per item can be unrealistic, for example when there are only a few rows with `prijs_per_bestelregel` / `prijs_per_verpakking` available. This can be checked using `prijs_per_stuk_medians.xlsx`, if there are categories with inaccurate price per items (focussing on the biggest categories), you can correct this, by:

- filling in a more accurate `prijs_per_stuk_median` for a given category
- excluding a category from the price analysis by setting `included` to `FALSE`

When you have made changes to `prijs_per_stuk_medians.xlsx`, this can be implemented in the price analysis, by setting `use_existing_price_median` to `TRUE` and running the pipeline again.

## Troubleshooting

### Sentence Transformers
Our code makes use of the pre-trained Scentence Transformers model to vectorize the article descriptions. The Scentence Transformers library makes an online connection with huggingface.co. Security policies of your organisation might block this connection, which will results in aan SSL-error. Therefore we have included an option to run the model locally.

If you need to download the model locally, browse to "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2". Download all the files in the tab "Files and versions". Store these files locally on your computer in a folder named "all-MiniLM-L6-v2", make sure the orginal folder structure is identical to how it is presented online.

To run the code with the local model, you need to make the following adjustments in our code:
- In main.py: remove the "#" before line 4 and 5, to uncomment these lines of code (os.environ["HF_HUB_OFFLINE"] = "1" , os.environ["TRANSFORMERS_OFFLINE"] = "1")
- In /lib/prediction_model_functions.py:
1) remove the "#" before line 3 and 4, to uncomment these lines of code (os.environ["HF_HUB_OFFLINE"] = "1" , os.environ["TRANSFORMERS_OFFLINE"] = "1")
2) comment line 51 (remote inladen model) by placing a # at the start of the line
3) uncomments line 52 (lokaal inladen model) by removing the # at the start of the line
4) edit the filepath in line 52 such that it directs to you local "all-MiniLM-L6-v2" folder.

You should now be able to run the code without the security error.

### Outliers
Your results might be inaccurate due to outliers. Outliers are a small number of rows which have inaccuracies in `verpakking_besteld` or `stuks_per_verkpakking`. This can be caused by a typo or a large order (for multiple years), for example. Categories might seem more important/large than you would expect. You can easily fix this manually, we advise to focus on the largest categories.

#### How to find outliers
First navigate into `lab_disposables_full_output.xlsx` and filter the data to only show data where `is_included`, column L, is `TRUE`/`WAAR` (other rows are excluded from the analysis/visuals). Thereafter you can select the category you want to investigate (use `categorie`, column J). To see the largest orders, put `stuks_totaal` in a descending order. This allows you to check if there might be suspiciously big orders. In our output data, for a specific category, we had a largest order which seemed unrealistic compared to the 2nd and 3rd biggest orders, after investigating the order (article description, number of packages ordered, items per package, etc.) we concluded this was an outlier due to a mistake in the data:

<img width="250" height="190" alt="image" src="https://github.com/user-attachments/assets/4af7acfa-10e0-40b6-a166-dd0f0d382ef4" />

If you find an outlier that you suspect might be muddying your results, you can exclude it from the visualisations and `lab_disposables_summary.xlsx`. For that row put `is_included`, column L, to `FALSE`/`ONWAAR`. After you have completed your search for outliers, you can run your results again (see section below).

If the outlier is resulting from a validated mistake in the number of items per package, you may also manually correct the number of items per package in the input data and rerun the analysis. This way the corrected order can be included in the results.

#### Running results seperately
If you have manually excluded outliers and saved the changes, you can run your results (visualizations and `lab_disposables_summary.xlsx`) by running in your terminal:
```bash
python lib\visualizatie_resultaten_functions.py
```
### Other Data
Another useful check might be in the data labelled in the category 'Other', if there are a lot of missing categories/items you would expect to see in the top 12. We use a threshold on the confidence of the predictions of 0.7. You could for example do a manual check on the rows with a confidence between 0.6 and 0.7. Do this by first selecting 'Other' (use `categorie`, column J), and then ordering the confidence of the predictions in descending order (use `predicted_confidence`, column K)

## Weight Data
The document `Weight Data Lab Disposables_UMCNL.xlsx` contains all our weight data from laboratory disposables that we gathered. This document is not part of our pipeline, but may be used for other purposes. 


## Further Plans & Updates
In 2027 we intend to update this github repository with an improved prediction model and turn the code into a python library.

We will additionally be externally validating the code on datasets of research institutions other than academic hostpitals. This will help to improve the code and allow retaining of the prediction model on a larger and more variable dataset. We hope the code will thereafter be more relevant and applicable for organisations outside of the academic hospitals.

## Authors Contact Information
If you have any comments or suggestions about this repository and code please raise an issue or contact us:

Eke Snoeren, Amsterdam UMC: e.snoeren@amsterdamumc.nl

Renate Kat, UMCG: r.kat@umcg.nl

Bart Noort, RUG: a.c.noort@rug.nl

#


