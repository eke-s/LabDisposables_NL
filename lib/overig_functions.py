import pandas as pd
import numpy as np
import re
import ast

def extract_stuks(value):
    """
    Extract 'stuks_per_verpakking' (pieces per package) values from string
    - value = a string (from column 'type_verpakking')
    """
    value = str(value)
    
    #case 1: pattern like 4x60 (extract value)
    match_multi = re.search(r'(\d+)\s*x\s*(\d+)', value)
    if match_multi:
        return int(match_multi.group(1)) * int(match_multi.group(2))
    
    #case 2: single number like 200 (extract value)
    match_single = re.search(r'\d+', value)
    if match_single:
        return int(match_single.group())
    
    return None

def combine_columns(row, cols):
    """
    Combine non-empty values from selected columns into a dictionary
    - row = a single row from a dataframe
    - cols = list of column names to check in the row
    """
    d = {} #create empty dictionary

    #check each selected column and add only non-empty values to the dictionary
    for col in cols:
        val = row[col]
        if pd.notna(val) and val != '':
            d[col] = val
    return d

def safe_idxmax(row): 
    """"
    Return the column with the highest value, or None if all values are missing
    - row = a single row from a dataframe    
    """
    return row.idxmax() if row.notna().any() else None

def safe_eval_list(x):
    """
    Convert a value into a list
    - x = value to convert
    """

    #keep as is, if already a list
    if isinstance(x, list):
        return x

    #convert pandas Series or numpy arrays to a list
    if isinstance(x, (pd.Series, np.ndarray)):
        return list(x)

    #return an empty list if x is empty
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return []

    #convert strings that represent a list into an actual list
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except (ValueError, SyntaxError):
            return [x]

    #wrap any other single value in a list
    return [x]

def merge_materials(row):
    """
    Combine material values from two columns into a single list
    - row = a single row from a dataframe
    """

    regex = safe_eval_list(row['materialen_regex'])
    clean = safe_eval_list(row['materialen_clean_db'])

    return regex + clean

def extract_numbers(s):
    """
    Extract numbers from a string and return them as floats
    - s = string containing the numbers to extract
    """

    if pd.isna(s):
        return []

    #find numbers with an optional decimal separator
    matches = re.findall(r'\d+(?:[.,]\d+)?', s)

    #convert commas to dots and cast the values to floats
    return [float(m.replace(',', '.')) for m in matches]

def prijsanalyse_median(data, use_existing_median, median_excel_path = "prijs_per_stuk_medians.xlsx"):
    """
    Compare prices per piece with the median price per category, 
    if true then (for certain categories) it is assumed that 'verpakking_besteld' (packages ordered) is the true number of pieces ordered, as opposed to 'stuks_totaal'
    - data = dataframe containing the price and product information
    - use_existing_median = determines wether to use prijs_per_stuk_medians.xlsx (if exists)
    - median_excel_path = path where price analysis is located/will be located
    """
    #calculate prijs_per_stuk
    if data['prijs_per_verpakking'].notna().any():
        #calculate the price per piece using prijs_per_verpakking
        data['prijs_per_stuk'] = (data['prijs_per_verpakking'] / data['stuks_per_verpakking_final'])
    elif data['prijs_per_bestelregel'].notna().any():
        #calculate the price per piece using prijs_per_bestelregel
        data['prijs_per_stuk'] = (data['prijs_per_bestelregel'] / data['stuks_totaal'])
    else:
        #return data unchanged if no price data is available
        return data

    #treat zero prices as missing values
    data['prijs_per_stuk'] = data['prijs_per_stuk'].replace(0, np.nan)

    ### either calculate new medians OR load existing medians
    if not use_existing_median:
        #calculate the median price per category
        median_per_categorie = (
            data.groupby('categorie')['prijs_per_stuk']
            .agg(
                prijs_per_stuk_median='median',
                aantal_waarden='count'
            )
            .reset_index()
        )

        #create the Excel file that the user can edit
        median_excel = median_per_categorie[['categorie', 'prijs_per_stuk_median']].copy()

        #all categories are included by default
        median_excel['included'] = True

        #save the medians to Excel
        median_excel.to_excel(median_excel_path, index=False)

    else:
        #load the existing Excel file
        median_excel = pd.read_excel(median_excel_path)

        #check that the required columns exist
        required_columns = {'categorie','prijs_per_stuk_median','included'}
        missing_columns = required_columns - set(median_excel.columns)
        if missing_columns:
            raise ValueError(
                f"The Excel file is missing the following columns: "
                f"{missing_columns}"
            )
        
    #add the category median to the original dataframe
    data = data.merge(median_excel[['categorie', 'prijs_per_stuk_median', 'included']], on='categorie', how='left')

    #calculate the alternative price per piece
    data['prijs_per_verpakking'] = np.where(
        data['prijs_per_bestelregel'].notna(),
        data['prijs_per_bestelregel']  / data['verpakking_besteld'],
        data['prijs_per_verpakking']
    )

    #check whether the alternative price per piece is closer to the median
    data['prijs_verpakking_dichterbij_median'] = (
        abs(data['prijs_per_verpakking'] - data['prijs_per_stuk_median'])
        <
        abs(data['prijs_per_stuk'] - data['prijs_per_stuk_median'])
    )

    #create the mask, a row is only included if:
    # 1. The packaging price is closer to the median
    # 2. The category is marked as included in the Excel file

    mask = (
        data['prijs_verpakking_dichterbij_median'].eq(True)
        & data['included'].eq(True)
    )

    #replace total pieces with ordered package quantity

    data.loc[mask, 'stuks_totaal'] = (data.loc[mask, 'verpakking_besteld'])

    return data