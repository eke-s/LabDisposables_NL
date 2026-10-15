import os
import pandas as pd
import re
import glob

def sanitize_artikelnummer(artikelnummer: str) -> str:
    """
    Clean the 'artikelnummer' (articlenumber)
    - artikelnummer = a single articlenumber as a string
    """
    artikelnummer = str(artikelnummer) #ensure it's a string
    artikelnummer = artikelnummer.replace(',', '.') #replace ',' with '.'

    #check if it's only digits or digits with a single '.'
    if re.fullmatch(r'\d+(\.\d+)?', artikelnummer):
        artikelnummer = artikelnummer.lstrip('0') #remove leading zeros
        #remove trailing zeros if there's a decimal
        if '.' in artikelnummer: 
            artikelnummer = artikelnummer.rstrip('0').rstrip('.')
        
        #if everything was zeros, fallback to '0'
        if artikelnummer == '':
            artikelnummer = '0'
    
    return artikelnummer

def exists_in_database(artikelnummer_col: pd.Series) -> pd.Series:
    """
    Check if 'artikelnummer' (articlenumber) exists in database 
    - artikelnummer_col = column containing articlenumbers
    """
    #import database
    db_path = os.path.join("data", "database_*.xlsx")
    detected_file = glob.glob(db_path)
    if not os.path.exists(detected_file[0]):
        print(f"Database not found at {db_path}")
        return pd.Series([False] * len(artikelnummer_col))
    db = pd.read_excel(detected_file[0], dtype=str)
    db['artikelnummer_merged_string'] = db['artikelnummer_merged'].astype(str)

    artikelnummer_col_sanitized = artikelnummer_col.astype(str).apply(sanitize_artikelnummer) #clean up 'artikelnummer' from input data column
    
    #return a boolean Series for each item in input data column, True = present in database
    return artikelnummer_col_sanitized.isin(db['artikelnummer_merged_string'].values)

def get_data_from_database(input_df: pd.DataFrame, artikel_col: str = "artikelnummer") -> pd.DataFrame:
    """
    Enirches input_df with data from database, for rows where 'found_in_database' == True
    Returns a new dataframe with extra columns (originating from database)
    - input_df = dataframe which has column 'found_in_database'
    - artikel_col = column name which contains the articlenumbers
    """
    #import database
    db_path = os.path.join("data", "database_*.xlsx")
    detected_file = glob.glob(db_path)
    if not os.path.exists(detected_file[0]):
        raise FileNotFoundError(f"Database not found at {os.path.abspath(db_path)}")
    db = pd.read_excel(detected_file[0], dtype=str)
    db['artikelnummer_merged_string'] = db['artikelnummer_merged'].astype(str)

    input_df["artikelnummer_cleaned"] = input_df[artikel_col].astype(str).apply(sanitize_artikelnummer) #clean up 'artikelnummer' from input data column

    #only apply to 'artikelnummer' found in database
    subset = input_df[input_df["found_in_database"] == True].copy() 

    #make subset of input data for which 'found_in_database' is not True
    subset_no_db = input_df[input_df['found_in_database'] != True].copy()

    #only keep relevant columns from database (and rename them)
    db_relevant = db.rename(
        columns={
            col: f"{col}_db" if col not in ['categorie', 'artikelnummer_merged_string'] else col
            for col in db.columns
        }
    )

    #merge subset (where input data is 'found_in_database' = True) with database
    merged_subset = subset.merge(
        db_relevant,
        how="left",
        left_on="artikelnummer_cleaned",
        right_on="artikelnummer_merged_string",
        suffixes=("", "_db")
    )
    merged_subset = merged_subset.drop(columns = ['artikelnummer_merged_string', 'is_included_db']) #drop irrelevant columns

    merged_data = pd.concat([merged_subset, subset_no_db], ignore_index=True, sort=False) #merge the two subsets from input data ('found_in_database' == True and != True)

    return merged_data


