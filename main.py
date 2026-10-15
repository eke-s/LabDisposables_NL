#import all necessary libraries, see requirements.txt
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
#os.environ["HF_HUB_OFFLINE"] = "1" #For local loading of the sentence transformers model
#os.environ["TRANSFORMERS_OFFLINE"] = "1" #For local loading of the sentence transformers model
import pandas as pd
import numpy as np
import tensorflow as tf
tf.get_logger().setLevel("ERROR")
tf.keras.utils.disable_interactive_logging()
from lib.database_functions import *
from lib.prediction_model_functions import *
from lib.regex_functions import *
from lib.overig_functions import *
from lib.proxy_functions import *
from lib.visualizatie_resultaten_functions import *

def run_pipeline(path_input: str, in_eenheden: list, in_paren: list, steriliteit_toevoegen: bool, price_analysis: bool, use_existing_price_median: bool):
    """
    Run the pipeline to calculate environmental impact (kg CO2 eq) per row in input data
    - path_input = path to input data
    - in_eenheden = list of 'type_verpakking' values which are equal to single pieces (ex.: stuks)
    - in_paren = list of 'type_verpakking' values which are equal to pairs (ex. paren)
    - steriliteit_toevoegen = boolean which determines whether to add the sterility bonus or not
    - price_analysis = boolean which determines whether to apply the price analysis
    - use_existing_price_median =  when price analysis is turned on, this determines whether to use a price analysis excel (see read_me.txt!)
    """
    input_df = pd.read_excel(path_input)

    ### Preprocessing: retain & rename important columns, extract 'stuk_per_verpakking_type' (pieces per package) from 'type_verpakking' (type of packaging), remove rows with negative 'verpakking_besteld' (amount of packages ordered)
    data = input_df[["omschrijving", "artikelnummer", "stuks_per_verpakking", "verpakking_besteld", "index", "type_verpakking", "prijs_per_verpakking", "prijs_per_bestelregel", "leverancier"]].copy()

    data['stuks_per_verpakking_type'] = data['type_verpakking'].apply(extract_stuks) #extract 'stuks_per_verpakking' (pieces per package) values in 'type_verpakking'(type of packaging)
    data['type_verpakking'] = data['type_verpakking'].astype(str).str.replace(' ', '', regex=False)
    print('preprocessing: done')

    #only keep rows where 'verpakking_besteld' (number of packages ordered) is a whole number and bigger than 0
    data = data[
        (data["verpakking_besteld"] > 0) & 
        (data["verpakking_besteld"] % 1 == 0)
    ]

    ### Step 1: check if 'artikelnummer' (articlenumber) is present in database + get info from database about product/articlenumber
    data['found_in_database'] = exists_in_database(data['artikelnummer'])
    data = get_data_from_database(data)
    print('step 1 database: done')

    ### Step 2: predict the 'categorie' (category) for 'artikelnummer' (articlenumber) which are not present in database
    data = preprocess_artikelomschrijving(data, 'omschrijving', stopwords) #preprocess 'omschrijving' (article description) for vectorization
    data, X_st = encode_sentence_transformer(data) #vectorize the 'preprocessed_omschrijving' (preprocessed article description) for the neural network
    keras = load_model("./models/LabNFUmodel_versie1.keras") #import the neural network (trained on annotated data)
    data = predict_category(data, 'emb_st', keras, "./models/label_encoder_labNFU_versie1.pkl", 0.70) #predict 'categorie' (category) with neural network, only accepting the labels with >70% confidence
    print('step 2 prediction model: done')

    ### Step 3: make column 'is_included' where categories falling out of the disposables scope are excluded from the analysis
    data['is_included'] = True

    exclude_categories = ['Mechanical Pipettes', 'Cryo Boxes', 'Racks', 'Sample Bags', 'Buckets', 'Tubes Other',
              'Wash Bottles', 'Gloves (Reusable)', 'Scissors', 'Storage Boxes',
              'Slide Boxes', 'Needle Containers', 'Transport Boxes', 'Naaldelektrode',
              'Weighing Scale', 'Biopsy Bags', 'Cryo Bags', 'Face Protectors',
              'Funnels (Disposable)','Funnels (Reusable)', 'Other',
              'Reagent Reservoirs (Reusable)', 'Reusabele Cell Counting Slides', 'Wrist Seals', 'Biopsy Needles',
              'Batteries', 'Inkt Cartridges', 'Markers', 'Printer Ribbons', 'Other_Try']

    data.loc[data['categorie'].isin(exclude_categories), 'is_included'] = False
    print('step 3 included/excluded categories: done')

    ### Step 4: get metadata from 'omschrijving' (article description) with regex and from database columns
    data['getallen_gevonden'] = data.index.to_series().apply(lambda _: []) #create column to save all numbers found with regex and in database columns

    ### Step 4A: 'stuks_per_verpakking' (pieces per packaging)
    data[["verpakkingssoort_regex", "stuks_per_verpakking_regex"]] = data["omschrijving"].apply(lambda x: pd.Series(get_number_of_items(x))) #extract 'stuks_per_verpakking_regex' (pieces per packaging from regex) and 'verpakkingssoort_regex' (type of packaging from regex extraction)
    data['getallen_gevonden'] = data.apply(lambda row: row['getallen_gevonden'] + [row['stuks_per_verpakking_regex']],axis=1)

    ### Step 4B: materials
    materialen_df = pd.read_excel(r"data\materialen_regex_versie1.xlsx") #list of materials and their synonyms
    data['materialen_regex'] = data['omschrijving_preprocessed'].apply(extract_materials, materialen = materialen_df) #extract the materials found in 'omschrijving' (article description)

    #merge materials from 'materialen_regex' and 'materialen_clean_db' (cleaned version of materials found in database article descriptions)
    data['materialen_totaal'] = data.apply(merge_materials, axis=1)

    ### Stap 4C: volume
    data[['volume_ml_regex', 'volume_origineel']] = (data['omschrijving'].apply(lambda x: pd.Series(get_volume(x)))) #extract 'volume_origineel' (volume as originally found in 'omschrijving) and 'volume_ml_regex' (original volume transformed in ml metric unit of volume)
    data['getallen_gevonden'] = data.apply(lambda row: row['getallen_gevonden'] + [row['volume_origineel']],axis=1)

    data['inhoud_liter_regex_lev_db'] = pd.to_numeric(data['inhoud_liter_regex_lev_db'],errors='coerce') #'inhoud_liter_regex_lev_db' (for rows with products found in database, where the suppliers description (from database) contained volumetric information) made into numerical data
    data['inhoud_liter_regex_manual_db'] = pd.to_numeric(data['inhoud_liter_regex_manual_db'],errors='coerce') #'inhoud_liter_regex_manual_db' (for rows with products found in database, where the manual description (from database) contained volumetric information) made into numerical data
    data['inhoud_liter_db'] = pd.to_numeric(data['inhoud_liter_db'],errors='coerce')  #'inhoud_liter_db' (for rows with products found in database, where the supplier included volumetric information) made into numerical data

    #transform volumetric columns from liters to milliliters
    data['inhoud_ml_regex_lev_db'] = data['inhoud_liter_regex_lev_db'] * 1000
    data['inhoud_ml_regex_manual_db'] = data['inhoud_liter_regex_manual_db'] * 1000
    data['inhoud_ml_db'] = data['inhoud_liter_db'] * 1000

    cols_fallback = ['inhoud_ml_db', 'inhoud_ml_regex_lev_db', 'inhoud_ml_regex_manual_db'] #volumetrics columns to fall back on if the other volumetric columns do not contain information
    data['volume_ml_final'] = (data['volume_ml_regex'].fillna(data[cols_fallback].max(axis=1, skipna=True))) #create volume_ml_final from 'volume_ml_regex', with the cols_fallback if empty
    data = data.drop(columns=['inhoud_ml_regex_lev_db', 'inhoud_ml_regex_manual_db', 'inhoud_liter_regex_lev_db', 'inhoud_liter_regex_manual_db', 'volume_ml_regex', 'inhoud_ml_db', 'inhoud_liter_db']) #drop all other volumetrics columns, that is not 'volume_ml_final'

    ### Stap 4D: size
    # option 1: get size from article discription
    data[['grootte_regex', 'grootte_eenheid_regex', 'grootte_origineel', 'grootte_afmetingen']] = (data['omschrijving'].apply(get_size).apply(pd.Series)) #extract 'grootte_regex' (size), 'grootte_eenheid_regex' (unit for size: cm, cm2, cm3), 'grootte_origineel' (dimensions from which the size were calculated), 'grootte_afmetingen' (dimensions from which the size were calculated, transformed to cm)
    data['getallen_gevonden'] = data.apply(lambda row: row['getallen_gevonden'] + (row['grootte_origineel'] or []),axis=1)
    
    #back-up optiion 1: size from suppliers (from database)
    mask_fill_db = data['grootte_regex'].isna() & data['grootte_db'].notna() #select rows where 'grootte_regex' is empty and 'grootte_db' (size from suppliers) is not empty
    data.loc[mask_fill_db, 'grootte_regex'] = data.loc[mask_fill_db, 'grootte_db'].astype(float) #where mask applies copy size from 'grootte_db'
    data.loc[mask_fill_db, 'grootte_eenheid_regex'] = data.loc[mask_fill_db, 'eenheid_grootte_db'] #where mask applies copy unit of size from 'eenheid_grootte_db'

    #back-up option 2: size from manual description (from database)
    data['omschrijving_manual_db'] = data['omschrijving_manual_db'].fillna('') 
    mask_still_empty = data['grootte_regex'].isna() #select rows where 'grootte_regex' is empty

    #where mask applies, extract 'grootte_regex' (size), 'grootte_eenheid_regex' (unit for size: cm, cm2, cm3), 'grootte_origineel' (dimensions from which the size were calculated), 'grootte_afmetingen' (dimensions from which the size were calculated, transformed to cm)
    result_fallback = (data.loc[mask_still_empty, 'omschrijving_manual_db'].apply(get_size_backup).apply(pd.Series)) 
    result_fallback.columns = ['grootte_regex','grootte_eenheid_regex', 'grootte_origineel', 'grootte_afmetingen']
    data.loc[mask_still_empty, result_fallback.columns] = result_fallback

    #back-up option 3: size supplier description (from database)
    data['omschrijving_leverancier_db'] = data['omschrijving_leverancier_db'].fillna('')
    mask_still_empty2 = data['grootte_regex'].isna() #select rows where 'grootte_regex' is empty

    #where mask applies, extract 'grootte_regex' (size), 'grootte_eenheid_regex' (unit for size: cm, cm2, cm3), 'grootte_origineel' (dimensions from which the size were calculated), 'grootte_afmetingen' (dimensions from which the size were calculated, transformed to cm)
    result_fallback2 = (data.loc[mask_still_empty2, 'omschrijving_leverancier_db'].apply(get_size_backup).apply(pd.Series))
    data.loc[mask_still_empty2, result_fallback.columns] = result_fallback2

    data = data.drop(columns=['grootte_db', 'eenheid_grootte_db', 'omschrijving_manual_db', 'omschrijving_leverancier_db']) #drop irrelvant columns related to size
    print('step 4 metadata extracion: done')

    ### Step 5: recategorize based on regex findings
    data['recategorized'] = False
    data[['categorie', 'recategorized']] = data.apply(lambda row: pd.Series(recategorisation(row['omschrijving'],row['categorie'], row['volume_ml_final'], row['materialen_totaal'], row['recategorized'], row['proxy_product_db'])), axis=1)

    #exclude categories (updated based on recategorisation)
    data.loc[data['categorie'].isin(exclude_categories), 'is_included'] = False
    print('step 5 recategorization: done')

    ### Step 6: making 'stuks_per_verpakking_final' (final pieces per package)
    impute = pd.read_excel("./data/impute_spv_versie1.xlsx") #import the accepted ranges for 'stuks_per_verpakking' (pieces per packaging) and the imputation rate per category

    data.loc[data['stuks_per_verpakking'] % 1 != 0, 'stuks_per_verpakking'] = np.nan #select rows where 'stuks_per_verpakking' are non-whole numbers and replaces the number with 0

    #transform all 'stuks_per_verpakking' columns to be numerical
    data['stuks_per_verpakking'] = pd.to_numeric(data['stuks_per_verpakking'], errors='coerce')
    data['stuks_per_verpakking_db'] = pd.to_numeric(data['stuks_per_verpakking_db'], errors='coerce')
    data['stuks_per_verpakking_type'] = pd.to_numeric(data['stuks_per_verpakking_type'], errors='coerce')
    data['stuks_per_verpakking_regex'] = pd.to_numeric(data['stuks_per_verpakking_regex'], errors='coerce')
    data['stuks_per_verpakking_regex_db'] = pd.to_numeric(data['stuks_per_verpakking_regex_db'], errors='coerce')

    #transform the minimum and maximum of pieces per packaging per category and the imputation per category to be numerical   
    impute['min_range'] = pd.to_numeric(impute['min_range'], errors='coerce')
    impute['max_range'] = pd.to_numeric(impute['max_range'], errors='coerce')
    impute['imputation'] = pd.to_numeric(impute['imputation'], errors='coerce')
    merged = data.merge(impute, on="categorie", how="left") #merge the minimum and maximum of pieces per packaging per category into the 'data' dataframe (matching on the category)

    cols_spv = ["stuks_per_verpakking","stuks_per_verpakking_db","stuks_per_verpakking_regex","stuks_per_verpakking_regex_db","stuks_per_verpakking_type"] #select all 'stuks_per_verpakking' columns
    valid_range = merged["min_range"].notna() & merged["max_range"].notna() #mask which selects only the rows in the data which have a valid (not NA) minomum-maximum range

    for col in cols_spv: #iterate over every 'stuks_per_verpakking' column
        mask = merged[col].between(merged["min_range"], merged["max_range"]) & valid_range #create a mask to identify rows where the value (from the 'stuks_per_verpakking' column) is within the allowed range (and the range isn't NA)
        merged.loc[valid_range & ~mask, col] = np.nan #remove all values (from selected 'stuks_per_verpakking' column) that don't get identified by the mask (when the range isn't NA)
    
    merged["stuks_per_verpakking_final"] = merged[cols_spv].max(axis=1, skipna=True) #make 'stuks_per_verpakking_final' by selecting the maximum value from all 'stuks_per_verpakking' columns
    merged["spv_final_source"] = merged[cols_spv].apply(safe_idxmax, axis=1) #'spv_final_source' is the name of the 'stuks_per_verpakking' column that was selected for 'stuks_per_verpakking_final'
    mask_imputed = merged["stuks_per_verpakking_final"].isna() #select rows where 'stuks_per_verpakking_final' is NA (and thus there are no 'stuks_per_verpakking' values available or within the minimum-maximum range)
    merged.loc[mask_imputed, "stuks_per_verpakking_final"] = merged.loc[mask_imputed, "imputation"] #impute the rows for which 'stuks_per_verpakking_final' is empty
    merged.loc[mask_imputed, "spv_final_source"] = "imputation" #for imputed rows, set 'spv_final_source' to 'imputation'
    mask_one = merged["stuks_per_verpakking_final"].isna() #select rows where 'stuks_per_verpakking_final' is still NA (and thus there also isn't an imputation value available for the category)
    merged.loc[mask_one, "stuks_per_verpakking_final"] = 1 # impute 'stuks_per_verpakking_final' = 1 for leftover rows
    merged.loc[mask_one, "spv_final_source"] = "imputed_1" #for leftover rows, set 'spv_final_source' to 'imputed_1'

    data = merged[data.columns.tolist() + ["stuks_per_verpakking_final", "spv_final_source"]].copy() #only keep columns originally in 'data' + 'stuks_per_verpakking_final' and 'spv_final_source'

    data['getallen_gevonden'] = data.apply(lambda row: row['getallen_gevonden'] + [row['stuks_per_verpakking_final']],axis=1)
    
    data["spv_info"] = data.apply(combine_columns, axis=1, cols=cols_spv) #save information of all 'stuks_per_verpakking' in 'spv_info'
    data = data.drop(columns=cols_spv) #drop all 'stuks_per_verpakking' columns (except stuks_per_verpakking_final)
    print('step 6 stuks_per_verpakking_final: done')

    ### Step 7: classifying into proxy-producten
    weight_data = pd.read_excel(r"data\weight_data_versie1.xlsx") #import weights of proxy-products
    milieuimpact_data = pd.read_excel(r"data\milieuimpact_versie1.xlsx") #import 'milieuimpact' (environmental impact) of different materials 

    #determine the 'milieuimpact' (enivronmental impact), 'proxy_product' 'gewicht_per_stuk' (weight per piece), 'materialen' (materials)
    data[['milieu_impact', 'proxy_product', 'gewicht_per_stuk', 'materialen']] = data.apply(lambda row: pd.Series(proxy_en_materiaalimpact(row['omschrijving'],row['categorie'],row['materialen_totaal'],
            row['volume_ml_final'],row['grootte_regex'],row['grootte_eenheid_regex'],row['getallen_gevonden'],row['grootte_afmetingen'],row['proxy_product_db'], row['artikelnummer'], "impact_per_kg", weight_data, milieuimpact_data)),axis=1)

    #correct 'stuks_per_verpakking_final' for 'Caps' (category) with proxy_product 'Bottle', as these are sold in lower quantities (avoid overestimation)
    data.loc[(data['proxy_product'].str.contains('Bottle', na=False)) & (data['categorie'] == 'Caps'), 'stuks_per_verpakking_final'] = 1
    data.loc[(data['proxy_product'].str.contains('Bottle', na=False)) & (data['categorie'] == 'Caps'), 'spv_final_source'] = 'imputed_corrected'

    #correct 'stuks_per_verpakking_final' for 'Coverslips' (category) with proxy_product 'Coverslipping Tape', as these are sold in lower quantities (avoid overestimation)
    data.loc[(data['proxy_product'].str.contains('Coverslipping Tape', na=False)) & (data['categorie'] == 'Coverslips'), 'stuks_per_verpakking_final'] = 5
    data.loc[(data['proxy_product'].str.contains('Coverslipping Tape', na=False)) & (data['categorie'] == 'Coverslips'), 'spv_final_source'] = 'imputed_corrected'
    print('step 7 proxy-products: done')

    ### Step 8: calculate 'stuks_totaal' (total items)
    data['stuks_totaal'] = np.where(
        data['type_verpakking'].isin(in_eenheden), #if 'type_verpakking' (type of packaging) is in 'in_eenheden' then 'stuks_totaal' = 'verpakking_besteld' (number of packages ordered)
        data['verpakking_besteld'],
        np.where(
            data['type_verpakking'].isin(in_paren), #if 'type_verpakking' is in 'in_paren' then 'stuks_totaal' = 2 * 'verpakking_besteld'
            data['verpakking_besteld'] * 2,
            data['stuks_per_verpakking_final'] * data['verpakking_besteld'] #else 'stuks_totaal' = 'stuks_per_verpakking_final' * 'verpakking_besteld'
        )
    )
    print('step 8 stuks_totaal: done')

    ### Bonus: implement price analysis
    if price_analysis:
        data = prijsanalyse_median(data, use_existing_price_median, median_excel_path = "prijs_per_stuk_medians.xlsx") 
        print('bonus price analysis: done')

    ### Step 9: calculate total environmental impact per order line
    data['milieu_impact_totaal'] = (data['milieu_impact'] * data['stuks_totaal'])
    print('step 9 environmental impact: done')

    ### Bonus: sterility (only when 'steriliteit_toevoegen' == True)
    if steriliteit_toevoegen:
        steriliteit_data = pd.read_excel(r"data\steriliteit_versie1.xlsx") #import sterility data (lists which categories should have sterility == True as a default)
        data = flag_regex_words(data, 'omschrijving_preprocessed', steriliteit_data) #search for sterility (or non-sterility) description in article description
        steriel_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'bonus - steriel', "impact_per_kg"].values[0],errors="coerce") #import sterility bonus value (per kg)
        data['milieu_impact_steriel_alle_stuks'] = (steriel_milieuimpact * (data['gewicht_per_stuk']/1000) * data['stuks_totaal']) * data['steriliteit_final'] #calculate the total sterility bonus per order line (when sterility == True)
        data['milieu_impact_steriel_totaal'] = data['milieu_impact_totaal'] + data['milieu_impact_steriel_alle_stuks'] #compute environmental impact with sterility included
        data = data.drop(columns=['steriliteit'])
        print('bonus sterility: done')

    ### Step 10: drop excessive columns
    data = data.drop(columns=['emb_st', 'index', 'artikelnummer_merged_db', 'leverancier_info_db','materialen_clean_db', 'artikelnummer_cleaned',
                              'getallen_gevonden', 'materialen_regex', 'grootte_origineel', 'Unnamed: 0_db', 'is_gesteriliseerd_db', 'verpakkingssoort_regex_db',
                              'proxy_product_db', 'omschrijving_preprocessed', 'predicted_label', 'verpakkingssoort_regex',
                              'volume_origineel'])
    print('step 10 drop excessive columns: done')

    ### Step 11: make output file
    results = analyze_lab_disposables(data)
    data.to_excel('./results/lab_disposables_full_output.xlsx')
    print('pipeline complete!')

#TODO: Change input variables
if __name__ == "__main__":
    run_pipeline(
        path_input = r"C:\Put\Path\Input\Data\Here", #Put the path to the input data here
        in_eenheden =['piece', 'stuks', 'fles', 'STU', 'FLE', 'ST', 'STK', 'FL', 'ROL', 'Stuks', 'STR'], #Put/add type_verpakking which are singular
        in_paren = ['paar'], #Put/add type_verpakking which are pairs
        steriliteit_toevoegen = False, #Change to 'True' when desired to add sterility bonus
        price_analysis = False, #Change to 'True' when desired to add price analysis (see Troubleshoot: Price Analysis in READ_ME file)
        use_existing_price_median = False) #Change to 'True' when 'prijs_per_stuk_medians.xlsx' has been created (see Troubleshoot: Price Analysis in READ_ME file)