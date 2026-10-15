import ast
import re
import math
from lib.regex_functions import *
from lib.overig_functions import *

def recategorisation(text, categorie, volume, materiaal, recategorized, proxy_producten_db):
    """
    Recategorize products based on text, volume, material, and proxy product.
    - text = preprocessed product description
    - categorie = current product category
    - volume = product volume
    - materiaal = product material
    - recategorized = indicates whether the category was changed
    - proxy_producten_db = proxy product category from the database
    """
    #exclude specific products from Cell Culture Flasks
    if categorie == 'Cell Culture Flasks':
        rules = [
            r"\bbactec\b",
            r"\bbloedkweek\w\*",
            r"\bmedium\b",
            r"\bfluorocell\b"
        ]

        for pattern in rules:
            if re.search(pattern, text, re.IGNORECASE):
                categorie = "Other"
                recategorized = True
                break

    #recategorize Centrifuge Tubes based on volume or description
    if categorie == 'Centrifuge Tubes':
        if not pd.isna(volume):
            volume = float(volume)

            if volume <= 5:
                categorie = "Microtubes"
                recategorized = True

            if volume > 500:
                categorie = "Other"
                recategorized = True

        rules = [r"\bdop voor\b"]

        for pattern in rules:
            if re.search(pattern, text, re.IGNORECASE):
                categorie = "Caps"
                recategorized = True
                break

    #recategorize Monovette products as Blood Collection Tubes
    if categorie == 'Cuvettes':
        rules = [r"monovette"]

        for pattern in rules:
            if re.search(pattern, text, re.IGNORECASE):
                categorie = "Blood Collection Tubes"
                recategorized = True
                break

    #exclude oversized or non-tube Cryo products
    if categorie == 'Cryo Tubes':
        if not pd.isna(volume):
            volume = float(volume)

            if volume > 20:
                categorie = "Other"
                recategorized = True

        rules = [
            r"\bcryodoos\b",
            r"\bcryo\s?box\b",
            r"\binvriesdoos\b",
            r"\bcryofreeze\b",
            r"\bcryostor\b",
            r"\bcryosure\b",
            r"\bcryo\s?medium\b",
            r"\bcryoprotectant\b"
        ]

        for pattern in rules:
            if re.search(pattern, text, re.IGNORECASE):
                categorie = "Other"
                recategorized = True
                break

    #exclude cotton products from Inoculating Loops
    if categorie == 'Inoculating Loops':
        if "cotton" in materiaal:
            categorie = "Other"
            recategorized = True

    #exclude cotton and PMMA products from Gloves
    if categorie == 'Gloves':
        if "cotton" in materiaal or "polymethyl methacrylate" in materiaal:
            categorie = "Other"
            recategorized = True

    # exclude lids incorrectly categorized as Coverslips
    if categorie == 'Coverslips':
        rules = [r"\bdeksel\b"]

        for pattern in rules:
            if re.search(pattern, text, re.IGNORECASE):
                categorie = "Other"
                recategorized = True
                break

    #coverslipping Tapes are recategorized as Coverslips
    if categorie == 'Coverslipping Tapes':
        categorie = "Coverslips"

    #recategorize Caps based on text and material
    if categorie == 'Caps':
        rules = [r"\b(capmat|capcluster)\b"]

        for pattern in rules:
            if re.search(pattern, text, re.IGNORECASE):
                categorie = "Plate Sealing Mats"
                recategorized = True
                break

        if (
            "silicone" in materiaal
            or "thermoplastic elastomers" in materiaal
            or "rubber" in materiaal
        ):
            categorie = "Other"
            recategorized = True

    #exclude specific products from Volumetric Labware
    if categorie == 'Volumetric Labware':
        rules = [r"\blysercell\b"]

        for pattern in rules:
            if re.search(pattern, text, re.IGNORECASE):
                categorie = "Other"
                recategorized = True
                break

    #exclude Trashbags from Grip and Saftey Bags, and recategorize to Other when not identified as a subtype of Grip and Safety Bags
    if categorie == "Grip and Safety Bags":

        # Identify trash bags based on the description
        if re.search(r"\w*(afval|disposa)\w*", text, re.IGNORECASE):
            categorie = "Trash Bags"
            recategorized = True

        # Otherwise check whether it belongs to a known Grip & Safety subtype
        else:
            has_known_text = any(
                re.search(pattern, text, re.IGNORECASE)
                for pattern in [
                    r"\w*(grip|ziplock|kangoeroe|kangaroo|zipper)\w*",
                    r"\w*(safety|verzendzak|verpakkingszak|zak|chemoprotect)\w*",
                    r"\w*lami\w*",
                ]
            )

            has_known_proxy = proxy_producten_db in {
                "Grip and Safety Bags - Lamigrip Bags",
                "Grip and Safety Bags - Grip Bags",
                "Grip and Safety Bags - Safety Bags",
            }

            # Exclude products that cannot be identified as a known bag type
            if not has_known_text and not has_known_proxy:
                categorie = "Other"
                recategorized = True

    #exclude scissors that were incorrectly categorized as Blades
    if categorie == 'Blades':
        rules = [r"\w*scissors?\w*"]

        for pattern in rules:
            if re.search(pattern, text, re.IGNORECASE):
                categorie = "Other"
                recategorized = True
                break

    #exclude non-capillary products based on material or description
    if categorie == 'Capillaries':
        if "stainless steel" in materiaal:
            categorie = "Other"
            recategorized = True

        rules = [r"\b(pistons?|mengijzer|stirrer)\b"]

        for pattern in rules:
            if re.search(pattern, text, re.IGNORECASE):
                categorie = "Other"
                recategorized = True
                break

    #exclude glass products from Microplate Lids
    if categorie == 'Microplate Lids':
        if "glass" in materiaal:
            categorie = "Other"
            recategorized = True

    #exclude unsuitable materials and oversized products from Bottle Top Filters
    if categorie == 'Bottle Top Filters':
        if "polycarbonate" in materiaal or 'glass' in materiaal:
            categorie = "Other"
            recategorized = True

        if not pd.isna(volume):
            volume = float(volume)

            if volume > 1000:
                categorie = "Other"
                recategorized = True

    #Ez-Squeeze products are recategorized as Pasteur Pipettes
    if categorie == 'Ez-Squeeze':
        categorie = "Pasteur Pipettes"

    #recategorize Lamigrip products as Grip and Safety Bags
    if categorie == 'Sterilization Bags':
        rules = [r"\blamigrip\b"]

        for pattern in rules:
            if re.search(pattern, text, re.IGNORECASE):
                categorie = "Grip and Safety Bags"
                recategorized = True
                break

    #recategorize products containing "optrek" as Needles
    if categorie == 'Blood Collection Needles':
        rules = [r"\boptrek\b"]

        for pattern in rules:
            if re.search(pattern, text, re.IGNORECASE):
                categorie = "Needles"
                recategorized = True
                break

    return categorie, recategorized

def proxy_en_materiaalimpact(text, categorie, materiaal, volume, grootte, grootte_eenheid, getallen_gevonden, grootte_afmetingen, proxy_producten_db, artikelnummer, impact, weight_data, milieuimpact_data):
    """
    Recategorize products based on text, volume, material, and size.
    - text = preprocessed product description
    - categorie = current product category
    - materiaal = product material
    - volume = product volume
    - grootte = product size
    - grootte_eenheid = unit of size
    - getallen_gevonden = column with all numbers found with regex and in database columns
    - grootte_afmeting = dimensions of product
    - proxy_producten_db = proxy product category from the database
    - artikelnummer = articlenumber
    - impact = name of column containing the environmental imapact in 'miliueimpact_data' (dataframe)
    - weight_data = dataframe with weight of different proxy-products
    - milieuimpact_data = dataframe with environmental impact of different materials
    """   
    if categorie == 'Cell Culture Flasks':
        proxy_product = None
       
        rules = {r"(?i)\b25(?:\s?cm.*)": "Cell Culture Flasks - T25", r"(?i)\bT-?25.*": "Cell Culture Flasks - T25",
            r"(?i)\b75(?:\s?cm.*)": "Cell Culture Flasks - T75", r"(?i)\bT-?75.*": "Cell Culture Flasks - T75",
            r"(?i)\b80(?:\s?cm.*)": "Cell Culture Flasks - T75", r"(?i)\bT-?80.*": "Cell Culture Flasks - T75",
            r"(?i)\b175(?:\s?cm.*)": "Cell Culture Flasks - T175", r"(?i)\bT-?175.*": "Cell Culture Flasks - T175",
            r"(?i)\b150(?:\s?cm.*)": "Cell Culture Flasks - T175", r"(?i)\bT-?150.*": "Cell Culture Flasks - T175",
            r"(?i)\b225(?:\s?cm.*)": "Cell Culture Flasks - T225", r"(?i)\bT-?225.*": "Cell Culture Flasks - T225",
            r"(?i).*erle.*": "Cell Culture Flasks - Erlenmeyer",
            r"(?i)\bcellstack.*": "Cell Culture Flasks - Cellstack"}

        found = set()

        #match the product description to a specific flask type
        for pattern, label in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(label)

        if len(found) >= 1:
            proxy_product = next(iter(found))
        #use the database proxy product when available as a back-up
        elif pd.notna(proxy_producten_db):
            proxy_product = proxy_producten_db

        #use T175 as the default flask type
        if proxy_product is None:
            proxy_product = "Cell Culture Flasks - T175" 
        
        #get the weight of the flask and cap
        flask_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
        cap_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0],errors="coerce")

        #match the flask material and use polystyrene as the default
        flask_materials = {'polystyrene', 'plastic','polycarbonate', 'polyethylene terephthalate glycol'}
        match_flask = next((v for v in materiaal if v in flask_materials), None)
        flask = match_flask if match_flask is not None else "polystyrene"
        
        #match the cap material and use HDPE as the default
        cap_materials = {'high density polyethylene', 'polyethylene', 'polypropylene'}
        match_cap = next((v for v in materiaal if v in cap_materials), None)
        cap = match_cap if match_cap is not None else "high density polyethylene"
        
        #get the environmental impact per kg for each material
        flask_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == flask, impact].values[0],errors="coerce")
        cap_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == cap, impact].values[0],errors="coerce")


        #calculate the total environmental impact and weight
        milieu_impact = (flask_milieuimpact * (flask_weight/1000)) + (cap_milieuimpact * (cap_weight/1000))
        info = f"{proxy_product}"
        materialen = f"flask: {flask}, cap: {cap}"
        weight = flask_weight + cap_weight
        return milieu_impact, info, weight, materialen
    
    if categorie == 'Centrifuge Tubes':
        #assign the standard Centrifuge Tubes proxy product
        proxy_product = "Centrifuge Tubes"

        #use 50 ml as the default volume
        if pd.isna(volume):
            volume = 50

        #convert the volume to a float
        if not pd.isna(volume):
            volume = float(volume)

        #calculate the tube and cap weight based on the volume
        formula_tube = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        formula_cap = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0]
        if pd.notna(formula_tube):
            tube_weight = eval(formula_tube, {"__builtins__": {}}, {"x": volume})
        if pd.notna(formula_cap):
            cap_weight = eval(formula_cap, {"__builtins__": {}}, {"x": volume})
    
        #match the tube material and use polypropylene as the default
        tube_materials = {'polypropylene', 'polystyrene', 'plastic', 'polyethylene therephthalate'}
        match_tube = next((v for v in materiaal if v in tube_materials), None)
        tube = match_tube if match_tube is not None else "polypropylene"
        
        #match the cap material and use HDPE as the default
        cap_materials = {'high density polyethylene', 'polyethylene'}
        match_cap = next((v for v in materiaal if v in cap_materials), None)
        cap = match_cap if match_cap is not None else "high density polyethylene"
        
        #get the environmental impact per kg for each material
        tube_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == tube, impact].values[0],errors="coerce")
        cap_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == cap, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = (tube_milieuimpact * (tube_weight/1000)) + (cap_milieuimpact * (cap_weight/1000))
        info = f"{proxy_product} - {volume} ml" 
        materialen = f"tube: {tube}, cap: {cap}"
        weight = tube_weight + cap_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Test Tubes':
        proxy_product = None
        
        #select the glass or plastic proxy product based on material
        if any(m in ['glass', 'borosilicate', 'soda-lime glass'] for m in materiaal):
            proxy_product = "Test Tubes - glass"
        else:
            proxy_product = "Test Tubes - plastic"

        #estimate the volume from the product dimensions when necessary
        if pd.isna(volume) and isinstance(grootte_afmetingen, list) and len(grootte_afmetingen)> 1:
            volume = float(volume)
            if len(grootte_afmetingen) == 1: 
                volume = None
            if len(grootte_afmetingen) == 2:
                diameter = min(grootte_afmetingen)
                hight = max(grootte_afmetingen)
                
                #calculate volume from diameter and height
                volume = (3.14159 * (diameter/2)**2 * hight ) / 1.82
                if diameter < 0.1: # in a few cases: notation may result in diameter and wall thickness instead of diameter and height
                    volume = None
            if len(grootte_afmetingen) == 3: #diameter, height and wall thickness
                diameter = sorted(grootte_afmetingen)[1]
                hight = max(grootte_afmetingen)
                
                #calculate volume from diameter and height
                volume = (3.14159 * (diameter/2)**2 * hight) / 1.82
            if len(grootte_afmetingen) > 3:
                volume = None

        #use 4.5 ml as the default volume
        if pd.isna(volume):
            volume = 4.5

        if proxy_product == "Test Tubes - plastic":
            #calculate the tube and cap weight based on the volume
            formula_tubeP = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
            formula_cap = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0]
            if pd.notna(formula_tubeP):
                tubeP_weight = eval(formula_tubeP, {"__builtins__": {}}, {"x": volume})
            if pd.notna(formula_cap):
                cap_weight = eval(formula_cap, {"__builtins__": {}}, {"x": volume})
    
            #match the tube material and use polystyrene as the default
            tubeP_materials = {'polystyrene', 'polypropylene', 'plastic', 'polycarbonate'}
            match_tubeP = next((v for v in materiaal if v in tubeP_materials), None)
            tubeP = match_tubeP if match_tubeP is not None else "polystyrene"
            
            #match the cap material and use polyethylene as the default
            cap_materials = {'polyethylene', 'low density polyethylene'}
            match_cap = next((v for v in materiaal if v in cap_materials), None)
            cap = match_cap if match_cap is not None else "polyethylene"
        
            #get the environmental impact per kg for each material
            tubeP_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == tubeP, impact].values[0],errors="coerce")
            cap_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == cap, impact].values[0],errors="coerce")

            #calculate the total environmental impact and weight
            milieu_impact = (tubeP_milieuimpact * (tubeP_weight/1000)) + (cap_milieuimpact * (cap_weight/1000))
            info = f"{proxy_product} - {volume} ml"
            materialen = f"tube: {tubeP}, cap: {cap}"
            weight = tubeP_weight + cap_weight
            return milieu_impact, info, weight, materialen
    
        if proxy_product == "Test Tubes - glass":
            #calculate the tube weight based on the volume
            formula_tubeG = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
            if pd.notna(formula_tubeG):
                tubeG_weight = eval(formula_tubeG, {"__builtins__": {}}, {"x": volume})
    
            #match the tube material and use glass as the default
            tubeG_materials = {'glass', 'borosilicate', 'soda-lime glass'}
            match_tubeG = next((v for v in materiaal if v in tubeG_materials), None)
            tubeG = match_tubeG if match_tubeG is not None else "glass"

            #get the environmental impact per kg for the tube material
            tubeG_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == tubeG, impact].values[0],errors="coerce")
    
            #calculate the total environmental impact and weight
            milieu_impact = tubeG_milieuimpact * (tubeG_weight/1000)
            info = f"{proxy_product} - {volume} ml"
            materialen = f"tube: {tubeG}"
            weight = tubeG_weight
            return milieu_impact, info, weight, materialen

    if categorie == 'Cuvettes':
        proxy_product = None
        
        #match the product description to a cuvette type
        rules = {
            r"\bmicro.*": "Cuvettes - Micro",
            r"\bhalf-micro.*": "Cuvettes - Half-Micro", r"\bsemi-micro.*": "Cuvettes - Half-Micro",
            r"\bhalf\b": "Cuvettes - Half-Micro", r"\bsemi\b": "Cuvettes - Half-Micro",
            r"\bmacro.*": "Cuvettes - Macro"}
         
        found = set()

        for pattern, label in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(label)

        if len(found) == 1:
            proxy_product = next(iter(found))
        elif len(found) > 1:
            proxy_product = "Cuvettes - Half-Micro" #multiple matches are treated as half-micro
        
        #convert dimensions to volume when the unit is cm³
        if grootte_eenheid == 'cmÂ³':
            volume = grootte

        #use volume to determine the cuvette type when no text match was found
        if proxy_product is None and pd.notna(volume):
            volume = float(volume)
            if volume < 1:
                proxy_product = "Cuvettes - Micro"
            elif volume >= 1 and volume < 2:
                proxy_product = "Cuvettes - Half-Micro"
            elif volume >= 2:
                proxy_product = "Cuvettes - Macro"
        #use the database proxy product when available, as back-up
        if pd.notna(proxy_producten_db):
            proxy_product = proxy_producten_db
        
        #use half-micro as the default cuvette type
        if proxy_product is None:
            proxy_product = "Cuvettes - Half-Micro"

        #get the weight of the cuvette
        cuvette_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
    
        #match the cuvette material and use polystyrene as the default
        cuvette_materials = {'polystyrene', 'polymethyl methacrylate', 'quartz', 'glass'}
        match_cuvette = next((v for v in materiaal if v in cuvette_materials), None)
        cuvette = match_cuvette if match_cuvette is not None else "polystyrene"
        
        #get the environmental impact per kg for the cuvette material
        cuvette_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == cuvette, impact].values[0],errors="coerce")
    
        #calculate the total environmental impact and weight
        milieu_impact = cuvette_milieuimpact * (cuvette_weight/1000)
        info = f"{proxy_product}"
        materialen = f"cuvette: {cuvette}"
        weight = cuvette_weight
        return milieu_impact, info, weight, materialen
    
    if categorie == 'Cryo Tubes':   

        #use 2 ml as the default volume
        if pd.isna(volume):
            volume = 2 #Of aanpassen naar 9ml?

        #match the tube material and use polypropylene as the default
        tube_materials = {'polypropylene', 'polystyrene', 'plastic', 'aluminium'}
        match_tube = next((v for v in materiaal if v in tube_materials), None)
        tube = match_tube if match_tube is not None else "polypropylene"

        if tube in ('aluminium'):
            proxy_product = 'Cryo Tubes - Aluminium'
            cap = 'aluminium'
            insert = 'plastic' #plastic insert inside the cap
        else:
            proxy_product = 'Cryo Tubes - Plastic'

            #match the cap material and use HDPE as the default
            cap_materials = {'high density polyethylene', 'polyethylene', 'low density polyethylene'}
            match_cap = next((v for v in materiaal if v in cap_materials), None)
            cap = match_cap if match_cap is not None else "high density polyethylene"

            #use silicone as the insert material
            insert = "silicone" # Ring

        #calculate the component weights based on the volume
        formula_tube = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        formula_cap = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0]
        formula_insert = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel3"].values[0]
        if pd.notna(formula_tube):
                tube_weight = eval(formula_tube, {"__builtins__": {}}, {"x": volume})
        if pd.notna(formula_cap):
                cap_weight = eval(formula_cap, {"__builtins__": {}}, {"x": volume})
        if pd.notna(formula_insert):
                insert_weight = eval(formula_insert, {"__builtins__": {}}, {"x": volume})

        #get the environmental impact per kg for each material
        tube_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == tube, impact].values[0],errors="coerce")
        cap_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == cap, impact].values[0],errors="coerce")
        insert_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == insert, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = (tube_milieuimpact * (tube_weight/1000)) + (cap_milieuimpact * (cap_weight/1000)) + (insert_milieuimpact * (insert_weight/1000))
        info = f"{proxy_product} - {volume} ml" 
        materialen = f"tube: {tube}, cap: {cap}, insert: {insert}"
        weight = tube_weight + cap_weight + insert_weight
        return milieu_impact, info, weight, materialen
    
    if categorie == 'Inoculating Loops':
        proxy_product = "Inoculating Loops"

        #get the weight of the loop
        loop_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
    
        #match the loop material and use polystyrene as the default
        loop_materials = {'polystyrene', 'cotton'}
        match_loop = next((v for v in materiaal if v in loop_materials), None)
        loop = match_loop if match_loop is not None else "polystyrene"
        
        #get the environmental impact per kg for the loop material
        loop_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == loop, impact].values[0],errors="coerce")
    
        #calculate the total environmental impact and weight
        milieu_impact = loop_milieuimpact * (loop_weight/1000)
        info = f"{proxy_product}"
        materialen = f"loop: {loop}"
        weight = loop_weight
        return milieu_impact, info, weight, materialen
    
    if categorie == "Gloves":
        proxy_product = None

        #match the glove material and use nitrile as the default
        glove_materials = {'nitril', 'neoprene', 'natural rubber', 'synthetic rubber', 'latex'}
        match_glove = next((v for v in materiaal if v in glove_materials), None)
        glove = match_glove if match_glove is not None else "nitril"

        if glove == 'nitril':
            glove = "nitril - glove"
            materiaal = "Nitril"
        if glove == 'synthetic rubber':
            glove = "synthetic rubber - glove"
        if glove == 'neoprene':
            materiaal = "Neopreen"
        if glove in ('natural rubber', 'synthetic rubber', 'latex'):
            materiaal = "Rubber Latex"
        
        #match the product description to a glove size
        rules = {
            r"\b(xs|x-small|m6|mt\s?6|-6)\b": "Extra Small",
            r"\s(s|small|m7|mt\s?7|-7)\b": "Small", #space before the pattern prevents x-small from matching as small
            r"\b(m|medium|m8|mt\s?8|-8)\b": "Medium",
            r"\b(l|large|m9|mt\s?9|-9)\b": "Large",
            r"\b(xl|x-large|m10|mt\s?10|-10)\b": "Extra Large",
            r"\b(xxl|m11|mt\s?11|-11)\b": "Extra Large" #no separate weight is available
            }

        found = set()

        for pattern, label in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(label)

        if len(found) >= 1:
            size = next(iter(found))
            proxy_product = f"Gloves {materiaal} - {size}"
        #use the database proxy product when available, as a back-up
        elif pd.notna(proxy_producten_db):
            proxy_product = proxy_producten_db

        #use medium as the default glove size
        if proxy_product is None:
            proxy_product = f"Gloves {materiaal} - Medium"

        #get the weight of the glove
        glove_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
        
        #get the environmental impact per kg for the glove material
        glove_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == glove, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = glove_milieuimpact * (glove_weight/1000)
        info = f"{proxy_product}"
        materialen = f"glove: {glove}"
        weight = glove_weight
        return milieu_impact, info, weight, materialen

    if categorie == "Coverslips":
        proxy_product = None ; size = None

        #detect coverslipping tape
        if (re.search(r"\w*(film|folie|tape)\w*", text, flags=re.IGNORECASE) 
            or proxy_producten_db == "Coverslips - Coverslipping Tape"):
            proxy_product = 'Coverslips - Coverslipping Tape'

            #get the weight of the tape
            weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

            #get the environmental impact of the tape and frame materials
            tape_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'polypropylene', impact].values[0],errors="coerce")
            frame_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'polystyrene', impact].values[0],errors="coerce")

            #calculate the total environmental impact and weight
            milieu_impact = tape_milieuimpact * ((weight * 0.85) / 1000) + frame_milieuimpact * ((weight * 0.15) / 1000)
            info = f"{proxy_product}"
            materialen = f"tape: polypropylene, frame: polystyrene"
            return milieu_impact, info, weight, materialen
       
        proxy_product = "Coverslips - Standard"

        if proxy_product == 'Coverslips - Standard':
            
            #extract the coverslip size
            if isinstance(grootte_afmetingen, list) and len(grootte_afmetingen) > 0:
                if len(grootte_afmetingen) == 1: 
                    size = 3.14159 * ((grootte_afmetingen[0]/2)**2)
                if len(grootte_afmetingen) == 2:
                    size = grootte_afmetingen[0] * grootte_afmetingen[1]

            #use the standard 24 x 50 mm size when no size is available
            if size == None:
                size = 2.4 * 5.0 #24x50mm is modus

            #calculate the coverslip weight based on size
            formula_slide = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
            if pd.notna(formula_slide):
                slide_weight = eval(formula_slide, {"__builtins__": {}}, {"x": size})

            #match the slide material and use glass as the default
            slide_materials = {'glass', 'borosilicate'}
            match_slide = next((v for v in materiaal if v in slide_materials), None)
            slide = match_slide if match_slide is not None else "glass"
            
            #get the environmental impact per kg for the slide material
            slide_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == slide, impact].values[0],errors="coerce")
    
            #calculate the total environmental impact and weight
            milieu_impact = slide_milieuimpact * (slide_weight/1000)
            info = f"{proxy_product} - {size} cm2"
            materialen = f"slide: {slide}"
            weight = slide_weight
            return milieu_impact, info, weight, materialen

    if categorie == 'Tape':
        proxy_product = "Tape - Standard" ; size = None

        #extract the tape size
        if isinstance(grootte_afmetingen, list) and len(grootte_afmetingen) > 0:
            if len(grootte_afmetingen) == 1:
                if grootte_afmetingen[0] > 100: #dimension is the length
                    size = grootte_afmetingen[0] * 1.8
                else: #dimension is the width
                    size = grootte_afmetingen[0] * 500 
            if len(grootte_afmetingen) == 2: 
                size = grootte_afmetingen[0] * grootte_afmetingen[1]
        if size is None:
            size = 1.8 * 500

        #calculate the tape weight based on size
        formula_tape = weight_data.loc[weight_data['proxy_product'] == "Tape", "onderdeel1"].values[0]
        if pd.notna(formula_tape):
            tape_weight = eval(formula_tape, {"__builtins__": {}}, {"x": size})

        #match the tape material and use paper as the default
        tape_materials = {'paper', 'polyvinyl chloride', 'cotton'}
        match_tape = next((v for v in materiaal if v in tape_materials), None)
        tape = match_tape if match_tape is not None else "paper"
            
        #get the environmental impact per kg for the tape material
        tape_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == tape, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = tape_milieuimpact * (tape_weight/1000)
        info = f"{proxy_product} - {size} cm2"
        materialen = f"tape: {tape}"
        weight = tape_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Syringe Filters':
        proxy_product = "Syringe Filters - Standard"
        size = None

        #extract the filter size
        if isinstance(grootte_afmetingen, list) and len(grootte_afmetingen) == 1:
            if grootte_afmetingen[0] < 0.4: #dimension is the membrane pore size
                size = 3.3
            else: #dimension is the filter size
                size = grootte_afmetingen[0] 
        if size is None:
            size = 3.3

        #calculate the filter weight based on size
        formula_SFilter = weight_data.loc[weight_data['proxy_product'] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula_SFilter):
            SFilter_weight = eval(formula_SFilter, {"__builtins__": {}}, {"x": size})

        #match the frame material and use polypropylene as the default
        frame_materials = {'polypropylene', 'methacrylate-butadiene-styrene', 'polycarbonate'}
        match_frame = next((v for v in materiaal if v in frame_materials), None)
        frame = match_frame if match_frame is not None else "polypropylene"
        
        #match the membrane material and use PTFE as the default
        membrane_materials = {'cellulose nitrate', 'polyethersulfone', 'polytetrafluoroethylene', 'polyvinylideenfluoride', 'surfactant-free cellulose acetate', 'nylon'}
        match_membrane = next((v for v in materiaal if v in membrane_materials), None)
        membrane = match_membrane if match_membrane is not None else "polytetrafluoroethylene"

        #get the environmental impact per kg for each material
        frame_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == frame, impact].values[0],errors="coerce")
        membrane_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == membrane, impact].values[0],errors="coerce")
        
        #calculate the total environmental impact and weight
        milieu_impact = frame_milieuimpact * ((SFilter_weight*0.95)/1000) + membrane_milieuimpact * ((SFilter_weight*0.05)/1000)
        info = f"{proxy_product} - {size} cm2"
        materialen = f"frame: {frame}, membrane: {membrane}"
        weight = SFilter_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Vials':
        proxy_product = "Vials - Standard"

        #use 1.5 ml as the default volume
        if pd.isna(volume):
            volume = 1.5

        #convert the volume to a float
        if not pd.isna(volume):
            volume = float(volume)

        #calculate the vial weight based on volume
        formula_vial = weight_data.loc[weight_data['proxy_product'] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula_vial):
            vial_weight = eval(formula_vial, {"__builtins__": {}}, {"x": volume})

        #calculate the cap weight based on volume
        formula_cap = weight_data.loc[weight_data['proxy_product'] == proxy_product, "onderdeel2"].values[0]
        if pd.notna(formula_cap):
            cap_weight = eval(formula_cap, {"__builtins__": {}}, {"x": volume})

        #calculate the septum weight based on volume
        formula_septum = weight_data.loc[weight_data['proxy_product'] == proxy_product, "onderdeel3"].values[0]
        if pd.notna(formula_septum):
            septum_weight = eval(formula_septum, {"__builtins__": {}}, {"x": volume})

        #match the vial material and use glass as the default
        vial_materials = {'glass', 'borosilicate'}
        match_vial = next((v for v in materiaal if v in vial_materials), None)
        vial = match_vial if match_vial is not None else "glass"

        #match the cap material and use plastic as the default
        cap_materials = {'polypropylene', 'plastic'}
        match_cap = next((v for v in materiaal if v in cap_materials), None)
        cap = match_cap if match_cap is not None else "plastic"

        #match the septum material and use silicone as materials
        septum = "silicone"

        #get the environmental impact per kg
        vial_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == vial, impact].values[0],errors="coerce")
        cap_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == cap, impact].values[0],errors="coerce")
        septum_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == septum, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = vial_milieuimpact * (vial_weight/1000) + cap_milieuimpact * (cap_weight/1000) + septum_milieuimpact * (septum_weight/1000)
        info = f"{proxy_product} - {volume}"
        materialen = f"vial: {vial}, cap: {cap}, septum: silicone"
        weight = vial_weight + cap_weight + septum_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Centrifuge Filters':
        proxy_product = None

        #match the product description to a centrifuge filter type
        rules = {r"\bamicon ultra(?:-|\s)(0.5|2|500).*": "Centrifuge Filters - micro",
                 r"\bamicon centrifugal(?:-|\s)(0.5|2|500).*": "Centrifuge Filters - micro",
                 r"\bvivaspin(?:\u00AE)?\s*(?:turbo)?\s*(0.5|2|500).*": "Centrifuge Filters - micro",
                 r"\bamicon ultra(?:-|\s)(4|6).*": "Centrifuge Filters - 15ml",
                 r"\bamicon centrifugal(?:-|\s)(4|6).*": "Centrifuge Filters - 15ml",
                 r"\bvivaspin(?:\u00AE)?\s*(?:turbo)?\s*(4|6).*": "Centrifuge Filters - 15ml",
                 r"\bamicon ultra(?:-|\s)(15|20).*": "Centrifuge Filters - 50ml",
                 r"\bamicon centrifugal(?:-|\s)(15|20).*": "Centrifuge Filters - 50ml",
                 r"\bvivaspin(?:\u00AE)?\s*(?:turbo)?\s*(15|20).*": "Centrifuge Filters - 50ml"}

        found = set()

        for pattern, label in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(label)

        if len(found) == 1:
            proxy_product = next(iter(found))
        #use volume to determine the centrifuge filter type when no text match was found
        elif proxy_product is None and volume is not None:
            if volume <= 2:
                proxy_product = "Centrifuge Filters - micro"
            if volume > 2 and volume < 14:
                proxy_product = "Centrifuge Filters - 15ml"
            if volume > 14:
                proxy_product = "Centrifuge Filters - 50ml"
        #use the database proxy product when available, as a backup
        elif pd.notna(proxy_producten_db):
            proxy_product = proxy_producten_db
        
        #use micro as the default centrifuge filter type
        if proxy_product is None:
            proxy_product = "Centrifuge Filters - micro"

        #get the weight of the frame (tube + frame), membrane and cap
        frame_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
        membrane_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0],errors="coerce")
        cap_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel3"].values[0],errors="coerce")
     
        #match the frame (tube + frame) material and use polypropylene as the default
        frame_materials = {'polypropylene', 'polystyrene', 'polyethylene'}
        match_frame = next((v for v in materiaal if v in frame_materials), None)
        frame = match_frame if match_frame is not None else "polypropylene"
        
        #match the membrane material and use polyethersulfone as the default
        membrane_materials = {'cellulose', 'cellulose nitrate', 'polyethersulfone', 'polytetrafluoroethylene', 'polyvinylideenfluoride', 'surfactant-free cellulose acetate', 'nylon'}
        match_membrane = next((v for v in materiaal if v in membrane_materials), None)
        membrane = match_membrane if match_membrane is not None else "polyethersulfone"
        
        #match the cap material and use HDPE as the default
        cap_materials = {'high density polyethylene', 'polyethylene'} # No data available, based on centrifuge tubes
        match_cap = next((v for v in materiaal if v in cap_materials), None)
        cap = match_cap if match_cap is not None else "high density polyethylene"

        #get the environmental impact per kg for each material
        frame_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == frame, impact].values[0],errors="coerce")
        membrane_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == membrane, impact].values[0],errors="coerce")
        cap_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == cap, impact].values[0],errors="coerce")
    
        #calculate the total environmental impact and weight
        milieu_impact = frame_milieuimpact * (frame_weight/1000) + membrane_milieuimpact * (membrane_weight/1000) + cap_milieuimpact * (cap_weight/1000)
        info = f"{proxy_product}" 
        materialen = f"frame: {frame}, cap: {cap}, membrane: {membrane}"
        weight = frame_weight + cap_weight + membrane_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Cell Counting Slides':
        proxy_product = "Cell Counting Slides"

        #get the weight of the slide
        slide_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
    
        #match the slide material and use polystyrene as the default
        slide_materials = {'polystyrene', 'glass'}
        slide_loop = next((v for v in materiaal if v in slide_materials), None)
        slide = slide_loop if slide_loop is not None else "polystyrene"

        #get the environmental impact per kg for the slide material
        slide_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == slide, impact].values[0],errors="coerce")
    
        #calculate the total environmental impact and weight
        milieu_impact = slide_milieuimpact * (slide_weight/1000)
        info = f"{proxy_product}"
        materialen = f"slide: {slide}"
        weight = slide_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Glass Inserts':
        proxy_product = "Glass Inserts"

        #use 0.25 ml as the default volume
        if pd.isna(volume):
            volume = 0.25

        #convert the volume to a float
        if not pd.isna(volume):
            volume = float(volume)

        #calculate the insert weight based on volume
        formula_insert = weight_data.loc[weight_data['proxy_product'] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula_insert):
            insert_weight = eval(formula_insert, {"__builtins__": {}}, {"x": volume})

        #match the insert material and use glass as the default
        insert_materials = {'glass', 'borosilicate'}
        match_insert = next((v for v in materiaal if v in insert_materials), None)
        insert = match_insert if match_insert is not None else "glass"

        #get the environmental impact per kg for the insert material
        insert_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == insert, impact].values[0],errors="coerce")
       
        #calculate the total environmental impact and weight
        milieu_impact = insert_milieuimpact * (insert_weight/1000)
        info = f"{proxy_product} - {volume} ml"
        materialen = f"insert: {insert}"
        weight = insert_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Absorbing Paper':
        proxy_product = "Absorbing Paper"

        #use 600 cm² as the default size
        if grootte_eenheid != 'cm²':
            grootte = 600
    
        #calculate the paper weight based on size
        formula_absp = weight_data.loc[weight_data['proxy_product'] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula_absp):
            absp_weight = eval(formula_absp, {"__builtins__": {}}, {"x": grootte})

        #get the environmental impact of the paper and polyethylene layers
        paper_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'paper', impact].values[0],errors="coerce")
        PE_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'polyethylene', impact].values[0],errors="coerce")
       
        #calculate the total environmental impact and weight
        milieu_impact = paper_milieuimpact * ((absp_weight * 0.8)/1000) + PE_milieuimpact * ((absp_weight * 0.2)/1000)
        info = f"{proxy_product} - {grootte} cm2"
        materialen = f"paper, polyethylene"
        weight = absp_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Parafilm':
        proxy_product = "Parafilm"

        if grootte_eenheid == 'cm' and grootte == 10:
            grootte = 38000 #standaard lengte 10cm = 38m
        if grootte_eenheid == 'cm' and grootte == 5:
            grootte = 37500 #standaard lengte 5cm = 75m    
        if pd.isna(grootte):
            grootte = 38000
    
        #calculate the paper and parafilm weight based on the size
        formula_parafilm = weight_data.loc[weight_data['proxy_product'] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula_parafilm):
            parafilm_weight = eval(formula_parafilm, {"__builtins__": {}}, {"x": grootte})
        formula_paper = weight_data.loc[weight_data['proxy_product'] == proxy_product, "onderdeel2"].values[0]
        if pd.notna(formula_paper):
            paper_weight = eval(formula_paper, {"__builtins__": {}}, {"x": grootte})

        #use paper and thermoplastic elastomers as the materials
        thermoplast_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'thermoplastic elastomers', impact].values[0],errors="coerce")
        paper_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'paper', impact].values[0],errors="coerce")
       
        #calculate the total environmental impact and weight
        milieu_impact = paper_milieuimpact * (paper_weight/1000) + thermoplast_milieuimpact * (parafilm_weight/1000)
        info = f"{proxy_product} - {grootte} cm2"
        materialen = f"paper, thermoplastic elastomers"
        weight = paper_weight + parafilm_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Microplate Lids':
        proxy_product = "Microplate Lids"
    
        #get the weight of the lid
        lid_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
        
        #match the lid material and use polystyrene as the default
        lid_materials = {'polystyrene'}
        match_lid = next((v for v in materiaal if v in lid_materials), None)
        lid = match_lid if match_lid is not None else "polystyrene"

        #get the environmental impact per kg for the lid material
        lid_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == lid, impact].values[0],errors="coerce")
       
        #calculate the total environmental impact and weight
        milieu_impact = lid_milieuimpact * (lid_weight/1000)
        info = f"{proxy_product}"
        materialen = f"lid: {lid}"
        weight = lid_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Bottle Top Filters':
        proxy_product = None

        #match the product description to a filter system or filter type
        rules = {r".*sys(?:tem)?.*": "Bottle Top Filters - System",
                 r".*eenheid.*": "Bottle Top Filters - System",
                 r".*unit.*": "Bottle Top Filters - System",
                 r".*receiv(?:er)?.*": "Bottle Top Filters - Bottle"}

        found = set()

        for pattern, label in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(label)

        if len(found) == 1:
            proxy_product = next(iter(found))
        #use the database proxy product when available, as a back-up
        elif pd.notna(proxy_producten_db):
            proxy_product = proxy_producten_db

        if proxy_product == None:
            proxy_product = "Bottle Top Filters - Filter"
        
        if pd.isna(volume):
            volume = 500

        #calculate the component weights based on the volume
        formula_cup = weight_data.loc[weight_data['proxy_product'] == proxy_product, "onderdeel1"].values[0] #cup + lid want geen info over materialen
        if pd.notna(formula_cup):
            cup_weight = eval(formula_cup, {"__builtins__": {}}, {"x": volume})
        formula_membrane = weight_data.loc[weight_data['proxy_product'] == proxy_product, "onderdeel2"].values[0]
        if pd.notna(formula_membrane):
            membrane_weight = eval(formula_membrane, {"__builtins__": {}}, {"x": volume})
        adaptor_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel3"].values[0],errors="coerce")  #Adaptor + filteradaptor + vacuumaansluiting want geen info over materialen; aanname: geen verband met volume fles/cup
        Oring_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel4"].values[0],errors="coerce") #aanname: geen verband met volume fles/cup
        formula_bottle = weight_data.loc[weight_data['proxy_product'] == proxy_product, "onderdeel5"].values[0] #Bottle + cap want geen info over materialen
        if pd.notna(formula_bottle):
            bottle_weight = eval(formula_bottle, {"__builtins__": {}}, {"x": volume})

        #match the cup material and use plastic as the default
        cup_materials = {'polypropylene', 'polystyrene', 'polyethylene'}
        match_cup = next((v for v in materiaal if v in cup_materials), None)
        cup = match_cup if match_cup is not None else "plastic"

        #match the membrane material and use polyethersulfone as the default
        membrane_materials = {'cellulose nitrate', 'polyethersulfone', 'surfactant-free cellulose acetate', 'nylon'}
        match_membrane = next((v for v in materiaal if v in membrane_materials), None)
        membrane = match_membrane if match_membrane is not None else "polyethersulfone"

        #get the environmental impact per kg for each material
        cup_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == cup, impact].values[0],errors="coerce")
        membrane_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == membrane, impact].values[0],errors="coerce")
        adaptor_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'plastic', impact].values[0],errors="coerce")
        Oring_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'silicone', impact].values[0],errors="coerce")
        bottle_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'plastic', impact].values[0],errors="coerce")
    
        #calculate the total environmental impact and weight
        milieu_impact = cup_milieuimpact * (cup_weight/1000) + membrane_milieuimpact * (membrane_weight/1000) + adaptor_milieuimpact * (adaptor_weight/1000) + Oring_milieuimpact * (Oring_weight/1000) + bottle_milieuimpact * (bottle_weight/1000)
        info = f"{proxy_product}"
        materialen = f"cup: {cup}, membrane: {membrane}, adaptor: plastic, Oring: silicone, bottle: plastic"
        weight = cup_weight + membrane_weight + adaptor_weight + Oring_weight + bottle_weight
        return milieu_impact, info, weight, materialen 

    if categorie == 'Shoe Covers':
        proxy_product = "Shoe Covers"

        #get the weight of the shoe cover
        cover_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
    
        #use polyethylene as the material
        cover_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'polyethylene', impact].values[0],errors="coerce")
    
        #calculate the total environmental impact and weight
        milieu_impact = cover_milieuimpact * (cover_weight/1000)
        info = f"{proxy_product}"
        materialen = f"cover: polyethylene"
        weight = cover_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Aluminium Foil Rolls':
        proxy_product  = "Aluminium Foil Rolls"

        #get the weight of the foil roll
        roll_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #use aluminium and cardboard as the materials
        alu_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'aluminium', impact].values[0],errors="coerce")
        cardboard_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'cardboard', impact].values[0],errors="coerce")
        
        #calculate the total environmental impact based on the material split
        milieu_impact = alu_milieuimpact * (roll_weight*0.8/1000) + cardboard_milieuimpact * (roll_weight*0.2/1000)

        #adjust the environmental impact for specific article sizes
        if artikelnummer == "611-9036":
            milieu_impact = milieu_impact * 5 #product is 150m ipv 30m
        if artikelnummer == "3014376":
            milieu_impact = milieu_impact * 3 #product is 90m ipv 30 m

        info = f"{proxy_product}"
        materialen = f"aluminium, cardboard"
        weight = roll_weight
        return milieu_impact, info, weight, materialen
    
    if categorie == 'Capillaries':
        proxy_product = None

        #match holding pipettes based on the description or database proxy
        if (re.search(r"\b(holding|biopsy|angled|hoek|gebogen)\w*", text, flags=re.IGNORECASE)
            or proxy_producten_db == "Capillaries - Holding Pipette"):
            proxy_product = "Capillaries - Holding Pipette"

            #get the weight of the holding pipette
            weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

            #use plastic as the material
            pipet_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'plastic', impact].values[0],errors="coerce")

            #calculate the environmental impact
            milieu_impact = pipet_milieuimpact * (weight / 1000)
            info = f"{proxy_product}"
            materialen = f"capillary: plastic"
            return milieu_impact, info, weight, materialen

        proxy_product = "Capillaries - Capillary"

        if pd.isna(volume):
            volume = 0.1 #100 uL als standaard

        #calculate the capillary weight based on the volume
        formula_capillary = weight_data.loc[weight_data['proxy_product'] == proxy_product, "onderdeel1"].values[0] 
        if pd.notna(formula_capillary):
            capillary_weight = eval(formula_capillary, {"__builtins__": {}}, {"x": volume})

        #match the capillary material and use glass as the default
        capillary_materials = {'glass', 'borosilicate', 'plastic'}
        match_capillary = next((v for v in materiaal if v in capillary_materials), None)
        capillary = match_capillary if match_capillary is not None else "glass"
   
        #get the environmental impact per kg for the capillary material
        capillary_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == capillary, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = capillary_milieuimpact * (capillary_weight/1000) 
        info = f"{proxy_product} - {volume} ml"
        materialen = f"capillary: {capillary}"
        weight = capillary_weight
        return milieu_impact, info, weight, materialen   

    if categorie == 'Cryo Molds':
        proxy_product = "Cryo Molds"

        if grootte_eenheid != 'cmÂ³':
            grootte = 1.125 #intermediate size = 15x15x5mm
        if pd.isna(grootte):
            grootte = 1.125

        #calculate the mold weight based on the size
        formula_mold = weight_data.loc[weight_data['proxy_product'] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula_mold):
            mold_weight = eval(formula_mold, {"__builtins__": {}}, {"x": grootte})

        #match the mold material and use PVC as the default
        mold_materials = {'polyvinyl chloride', 'polyethylene'}
        match_mold = next((v for v in materiaal if v in mold_materials), None)
        mold = match_mold if match_mold is not None else "polyvinyl chloride"
        
        #get the environmental impact per kg for the mold material
        mold_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == mold, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = mold_milieuimpact * (mold_weight/1000)
        info = f"{proxy_product} - {grootte} cm3"
        materialen = f"mold: {mold}"
        weight = mold_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Blood Collection Needles':
        proxy_product  = "Blood Collection Needles"

        #get the weight of the needle, tube, and connector
        needle_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel3"].values[0],errors="coerce")
        tube_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0],errors="coerce")
        connector_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #use plastic, stainless steel, and PVC as the materials
        plastic_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'plastic', impact].values[0],errors="coerce")
        rvs_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'stainless steel', impact].values[0],errors="coerce")
        pvc_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'polyvinyl chloride', impact].values[0],errors="coerce")
        
        #calculate the total environmental impact and weight
        milieu_impact = pvc_milieuimpact * (tube_weight/1000) + plastic_milieuimpact * (needle_weight*0.2/1000 + connector_weight*0.95/1000) + rvs_milieuimpact * (needle_weight*0.8/1000 + connector_weight*0.05/1000)

        info = f"{proxy_product}"
        materialen = f"connector and needle: plastic and stainless steel, tube: polyvinyl chloride"
        weight = needle_weight + tube_weight + connector_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Sterilization Bags':
        proxy_product  = "Sterilization Bags"

        if grootte_eenheid != 'cm²':
            grootte = 166 #het gewogen zakje
    
        #calculate the plastic and paper weight based on the size
        formula_plastic = weight_data.loc[weight_data['proxy_product'] == proxy_product, "onderdeel2"].values[0]
        if pd.notna(formula_plastic):
            plastic_weight = eval(formula_plastic, {"__builtins__": {}}, {"x": grootte})
        formula_paper = weight_data.loc[weight_data['proxy_product'] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula_paper):
            paper_weight = eval(formula_paper, {"__builtins__": {}}, {"x": grootte})
        
        #use PET and paper as the materials
        PET_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'polyethylene therephthalate', impact].values[0],errors="coerce")
        paper_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'paper', impact].values[0],errors="coerce")
        
        #calculate the total environmental impact and weight
        milieu_impact = PET_milieuimpact * (plastic_weight/1000) + paper_milieuimpact * (paper_weight/1000)
        info = f"{proxy_product} - {grootte} cm2"
        materialen = f"PET, paper"
        weight = plastic_weight + paper_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Labels and Stickers':
        proxy_product  = "Labels and Stickers"

        #get the weight of the label roll
        roll_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #match the sticker material and use polyester as the default
        sticker_materials = {'polyvinyl chloride', 'polyethylene', 'polyester', 'polypropylene', 'paper'}
        match_sticker = next((v for v in materiaal if v in sticker_materials), None)
        sticker = match_sticker if match_sticker is not None else "polyester"
        
        #use the sticker material and paper as the materials
        sticker_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == sticker, impact].values[0],errors="coerce")
        paper_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'paper', impact].values[0],errors="coerce")
        
        #calculate the total environmental impact based on the material split
        milieu_impact = sticker_milieuimpact * (0.5*roll_weight/1000) + paper_milieuimpact * (roll_weight*0.95/1000)

        info = f"{proxy_product}"
        materialen = f"paper, {sticker}"
        weight = roll_weight
        return milieu_impact, info, weight

    if categorie == 'Well Inserts':
        #find the number of wells
        numbers = extract_numbers(text)
        numbers_wells = [x for x in numbers if x not in getallen_gevonden]
        VALID_WELLS = {2, 4, 6, 12, 14, 24, 48}

        #map the detected number of wells to a proxy product
        GROUP_MAPPING = {2: 6, 4: 6, 6: 6, 12: 12, 14: 12, 24: 24, 48: 24}
        wells = max((x for x in numbers_wells if x in VALID_WELLS), default=None)

        if pd.isna(wells) & pd.notna(proxy_producten_db):
            proxy_product = proxy_producten_db
        else:
            wells = GROUP_MAPPING.get(wells, 24)
            proxy_product = f'Well Inserts - {wells} wells'

        #get the weight of the frame, membrane, and plate
        frame_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
        membrane_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0],errors="coerce")
        plate_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel3"].values[0],errors="coerce")

        #match the frame and membrane materials and use defaults when needed
        frame_materials = {'plastic', 'polystyrene'} 
        match_frame = next((v for v in materiaal if v in frame_materials), None)
        frame = match_frame if match_frame is not None else "polystyrene"

        membrane_material = {'polyethylene therephthalate',  'polycarbonate'}
        match_membrane = next((v for v in materiaal if v in membrane_material), None)
        membrane = match_membrane if match_membrane is not None else "polyethylene therephthalate"

        #match the plate material and use polystyrene as the default
        plate_materials = {'plastic', 'polycarbonate', 'polyethylene', 'polyethylene therephthalate', 'polypropylene', 'polystyrene', 'polyvinyl chloride'}
        match_plate = next((v for v in materiaal if v in plate_materials), None)
        plate = match_plate if match_plate is not None else "polystyrene"

        #get the environmental impact per kg for each material
        frame_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == frame, impact].values[0],errors="coerce")
        membrane_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == membrane, impact].values[0],errors="coerce")
        plate_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == plate, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = frame_milieuimpact * (frame_weight/1000) + membrane_milieuimpact * (membrane_weight/1000) + plate_milieuimpact * (plate_weight/1000)
        info = f"{proxy_product}"
        materialen= f"frame: {frame}, membrane: {membrane}, plate: {plate}"
        weight = frame_weight + membrane_weight + plate_weight
        return milieu_impact, info, weight, materialen
    
    if categorie == 'N-Filter Pipette Tips':
        #assign the standard N-Filter Pipette Tips proxy product
        proxy_product = "N-Filter Pipette Tips"

        #extract and validate the volume from the description
        if not pd.isna(volume):
            volume = float(volume)
            if volume > 25:
                volume = None

        if pd.isna(volume):
            patterns = [r"\bP(\d+)\b", r"\b[A-Z]{1,3}-(?:L)?(\d+)\b"]

            for pattern in patterns:
                matches = re.findall(pattern, text, flags=re.IGNORECASE)

                for value in matches:
                    v = float(value.replace(",", "."))
                    if v <= 25:
                        volume = v
                        break

        if pd.isna(volume):
            volume = 0.2

        #calculate the pipette tip weight based on the volume
        formula = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula):
            weight = eval(formula, {"__builtins__": {}}, {"x": volume})

        #match the pipette material and use polypropylene as the default
        pipet_materials = {'low density polyethylene', 'plastic', 'polycarbonate', 'polyethylene therephthalate', 'polypropylene', 'polyethylene'}
        match_materials = next((v for v in materiaal if v in pipet_materials), None) 
        pipet = match_materials if match_materials is not None else "polypropylene"

        #get the environmental impact per kg for the pipette material
        pipet_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == pipet, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = pipet_milieuimpact * (weight / 1000)
        info = f"{proxy_product} - {volume} ml"
        materialen = f"pipet: {pipet}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Microtubes':
        #match the product description to a microtube type
        rules = {r"\w*strip\w*": "Microtubes - 8-Strip",
                 r"\b(snap|safe-lock|safelock|safe lock|safeseal|push)\w*": "Microtubes - Snap",
                 r"\w*(screw|schroefdop|schrfd|m.scr.cap|schrdop|schr.dop)\w*": "Microtubes - Screw",
                 r"\b(zonder dop|z/dek|z/stop|z.dop|zonder schroef|zonder stop|z/dop|z.stop|bwithout cap)\w*": "Microtubes - Zonder Dop",
                 r"\b(zond|z.scr.cap)\b": "Microtubes - Zonder Dop"}

        found = set()

        for pattern, label in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(label)

        #extract and validate the volume
        if pd.isna(volume):
            volume = 1.5

        if not pd.isna(volume):
            volume = float(volume)
            if volume > 5:
                volume = 1.5

        if "Microtubes - 8-Strip" in found or proxy_producten_db == "Microtubes - 8-Strip" or proxy_producten_db == "Microtubes - 8-Strip met Caps":
            if re.search(r"\w*cap\w*", text, re.IGNORECASE):
                proxy_product = "Microtubes - 8-Strip met Caps"
            elif proxy_producten_db == "Microtubes - 8-Strip met Caps":
                 proxy_product = "Microtubes - 8-Strip met Caps"               
            else:
                proxy_product = "Microtubes - 8-Strip"

            #get the weight of the 8-strip
            strip_weight = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]

            #match the strip material and use polypropylene as the default
            strip_materials = {'plastic', 'recycled polypropylene', 'polystyrene', 'polypropylene', 'polyethylene'}
            match_materials = next((v for v in materiaal if v in strip_materials), None) 
            strip = match_materials if match_materials is not None else "polypropylene"

            #get the environmental impact per kg for the strip material
            strip_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == strip, impact].values[0],errors="coerce")

            #calculate the total environmental impact and weight
            milieu_impact = strip_milieuimpact * (strip_weight / 1000)
            info = f"{proxy_product}"
            materialen = f"tube strip: {strip}"
            weight = strip_weight
            return milieu_impact, info, weight, materialen         

        elif "Microtubes - Zonder Dop" in found:
            proxy_product = "Microtubes - Zonder Dop"
        elif len(found) >= 1:
            proxy_product = next(iter(found))
        elif pd.notna(proxy_producten_db):
            proxy_product = proxy_producten_db
        else:
            proxy_product = "Microtubes - Snap"

        if proxy_product in ("Microtubes - Zonder Dop", "Microtubes - Snap"):
            #calculate the tube weight based on the volume
            formula = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
            if pd.notna(formula):
                tube_weight = eval(formula, {"__builtins__": {}}, {"x": volume})

            #match the tube material and use polypropylene as the default
            tube_materials = {'plastic', 'recycled polypropylene', 'polystyrene', 'polypropylene', 'polyethylene'}
            match_materials = next((v for v in materiaal if v in tube_materials), None) 
            tube = match_materials if match_materials is not None else "polypropylene"

            #get the environmental impact per kg for the tube material
            tube_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == tube, impact].values[0],errors="coerce")

            #calculate the total environmental impact and weight
            milieu_impact = tube_milieuimpact * (tube_weight / 1000)
            info = f"{proxy_product} - {volume} ml"
            materialen = f"tube: {tube}"
            weight = tube_weight
        else:
            #calculate the tube and cap weight based on the volume
            formula_tube = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
            formula_cap = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0]
            if pd.notna(formula_tube):
                tube_weight = eval(formula_tube, {"__builtins__": {}}, {"x": volume})
            if pd.notna(formula_cap):
                cap_weight = eval(formula_cap, {"__builtins__": {}}, {"x": volume})

            #match the tube material and use polypropylene as the default
            tube_materials = {'plastic', 'recycled polypropylene', 'polystyrene', 'polypropylene', 'polyethylene'}
            match_materials = next((v for v in materiaal if v in tube_materials), None) 
            tube = match_materials if match_materials is not None else "polypropylene"

            #match the cap material and use polypropylene as the default
            cap_materials = {'recycled polypropylene', 'polyethylene', 'polypropylene'}
            match_materials = next((v for v in materiaal if v in cap_materials), None) 
            cap = match_materials if match_materials is not None else "polypropylene"

            #get the environmental impact per kg for each material
            tube_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == tube, impact].values[0],errors="coerce")
            cap_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == cap, impact].values[0],errors="coerce")

            #calculate the total environmental impact and weight
            milieu_impact = tube_milieuimpact * (tube_weight / 1000) + cap_milieuimpact * (cap_weight/1000)
            info = f"{proxy_product} - {volume} ml"
            materialen = f"tube: {tube}, cap: {cap}"
            weight = tube_weight + cap_weight
        return milieu_impact, info, weight, materialen
        
    if categorie == 'Multiwell Plates':
        #find the number of wells
        numbers = extract_numbers(text)
        numbers_wells = [x for x in numbers if x not in getallen_gevonden]
        VALID_WELLS = {6, 12, 14, 24, 48, 96, 384}

        #map the detected number of wells to a proxy product
        GROUP_MAPPING = {6: 6, 12: 12, 14: 12, 24: 24, 48: 48, 96: 96, 384: 384}
        wells = max((x for x in numbers_wells if x in VALID_WELLS), default=None)
        
        if pd.isna(wells) & pd.notna(proxy_producten_db):
            proxy_product = proxy_producten_db
        else:
            wells = GROUP_MAPPING.get(wells, 24)
            proxy_product = f'Multiwell Plates - {wells} wells'

        #match deepwell products based on the description
        rules = {r"\w*(deep|megablock|masterblock|storage)\w*": "Multiwell Plates - Deepwell"}

        found = set()

        for pattern, label in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(label)

        if len(found) == 1:
            proxy_product = next(iter(found))

        #get the weight of the plate
        plate_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #match the plate material and use polystyrene as the default
        plate_materials = {'plastic', 'polycarbonate', 'polyethylene', 'polyethylene therephthalate', 'polypropylene', 'polystyrene', 'polyvinyl chloride'}
        match_plate = next((v for v in materiaal if v in plate_materials), None)
        plate = match_plate if match_plate is not None else "polystyrene"
        
        #get the environmental impact per kg for the plate material
        plate_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == plate, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = plate_milieuimpact * (plate_weight/1000)
        info = f"{proxy_product}"
        materialen = f"plate: {plate}"
        weight = plate_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Petri Dishes':

        if isinstance(grootte_afmetingen, list) and len(grootte_afmetingen) > 0:
            petridish_diameter = max(grootte_afmetingen)
            if petridish_diameter < 3.5:
                petridish_diameter = 9.0
        else:
            petridish_diameter = 9.0

        #match the Petri dish material and use polystyrene as the default
        petridish_materials = {'borosilicate', 'glass', 'soda-lime glass', 'plastic', 'polycarbonate', 'polyethylene therephthalate', 'polystyrene'}
        match_materials = next((v for v in materiaal if v in petridish_materials), None) 
        petridish = match_materials if match_materials is not None else "polystyrene"

        if petridish in ('borosilicate', 'glass', 'soda-lime glass'):
            proxy_product = 'Petri Dishes - Glass'
        else:
            proxy_product = 'Petri Dishes - Plastic'

        #calculate the Petri dish weight based on the diameter
        formula = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula):
            weight = eval(formula, {"__builtins__": {}}, {"x": petridish_diameter})

        #get the environmental impact per kg for the Petri dish material
        petridish_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == petridish, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = petridish_milieuimpact * (weight / 1000)
        info = f"{proxy_product} - {petridish_diameter} diameter"
        materialen = f"petridish: {petridish}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Caps':
        #match the product description to a cap type
        rules = {r"\w*(strip|capband)\w*": "Caps - 8-Strip",

                 r"\w*(microtu|schroef|schrfdop|screw)\w*": "Caps - Microtubes Screw",

                 r"\b(winged|vleugel|grip|lamellen)\w*": "Caps - Reaction Tube",
                 
                 r"\w*(gl\s?45|gl\s?32|gl\s?25|fles|bottle|duran)\w*": "Caps - Bottle"}

        found = set()

        for pattern, label in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(label)
    
        if "Caps - Bottle" in found:
            proxy_product = "Caps - Bottle"
        elif len(found) >= 1:
            proxy_product = next(iter(found))
        elif pd.notna(proxy_producten_db):
            proxy_product = proxy_producten_db
        else:       
            proxy_product = "Caps - Reaction Tube"

        #get the weight of the cap
        cap_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #match the cap material and use polypropylene as the default
        cap_materials = {'low density polyethylene', 'plastic', 'polycarbonate', 'polypropylene', 'polyethylene', 'aluminium', 'high density polyethylene', 'polystyrene'}
        match_cap = next((v for v in materiaal if v in cap_materials), None)
        cap = match_cap if match_cap is not None else "polypropylene"
        
        #get the environmental impact per kg for the cap material
        cap_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == cap, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = cap_milieuimpact * (cap_weight/1000)
        info = f"{proxy_product}"
        materialen = f"cap: {cap}"
        weight = cap_weight
        return milieu_impact, info, weight, materialen  

    if categorie == 'Filter Pipette Tips':
        #assign the standard Filter Pipette Tips proxy product
        proxy_product = "Filter Pipette Tips"

        #extract and validate the volume
        if not pd.isna(volume):
            volume = float(volume)
            if volume > 25:
                volume = None

        if pd.isna(volume):
            patterns = [r"\bP(\d+)\b", r"\b[A-Z]{1,3}-(?:L)?(\d+)\b"]

            for pattern in patterns:
                matches = re.findall(pattern, text, flags=re.IGNORECASE)

                for value in matches:
                    v = float(value.replace(",", "."))
                    if v <= 25:
                        volume = v
                        break

        if pd.isna(volume):
            volume = 0.2

        #calculate the pipette and membrane weight based on the volume
        formula_pipet = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula_pipet):
            weight_pipet = eval(formula_pipet, {"__builtins__": {}}, {"x": volume})

        formula_membrane = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0]
        if pd.notna(formula_membrane):
            weight_membrane = eval(formula_membrane, {"__builtins__": {}}, {"x": volume})

        #match the pipette material and use polypropylene as the default
        pipet_materials = {'low density polyethylene', 'plastic', 'polypropylene', 'polyethylene', 'recycled polypropylene'}
        match_materials = next((v for v in materiaal if v in pipet_materials), None) 
        pipet = match_materials if match_materials is not None else "polypropylene"

        #use polyethylene terephthalate as the membrane material
        membrane = "polyethylene therephthalate"

        #get the environmental impact per kg for each material
        pipet_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == pipet, impact].values[0],errors="coerce")
        membrane_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == membrane, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = pipet_milieuimpact * (weight_pipet / 1000) + membrane_milieuimpact * (weight_membrane / 1000)
        info = f"{proxy_product} - {volume} ml"
        materialen = f"pipet: {pipet}, membrane: {membrane}"
        weight = weight_pipet + weight_membrane
        return milieu_impact, info, weight, materialen

    if categorie == 'Blood Collection Tubes':
        #assign the standard Blood Collection Tubes proxy product
        proxy_product = "Blood Collection Tubes"

        #extract and validate the volume
        if not pd.isna(volume):
            volume = float(volume)
            if (volume > 10) or (volume < 0.1):
                volume = 3.5

        if pd.isna(volume):
            volume = 3.5

        #calculate the tube weight based on the volume
        formula_tube = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula_tube):
            weight_tube = eval(formula_tube, {"__builtins__": {}}, {"x": volume})

        #get the cap and insert weight
        weight_cap = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0],errors="coerce")
        weight_insert = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel3"].values[0],errors="coerce")

        #match the tube material and use PET as the default
        tube_materials = {'glass', 'polyethylene therephthalate', 'plastic'}
        match_materials = next((v for v in materiaal if v in tube_materials), None) 
        tube = match_materials if match_materials is not None else "polyethylene therephthalate"

        #match the cap material and use LDPE as the default
        cap_materials = {'polypropylene', 'low density polyethylene', 'high density polyethylene'}
        match_materials = next((v for v in materiaal if v in cap_materials), None) 
        cap = match_materials if match_materials is not None else "low density polyethylene"

        #match the insert material and use thermoplastic elastomers as the default
        insert_materials = {'rubber', 'thermoplastic elastomers'}
        match_materials = next((v for v in materiaal if v in insert_materials), None) 
        insert = match_materials if match_materials is not None else "thermoplastic elastomers"

        #get the environmental impact per kg for each material
        tube_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == tube, impact].values[0],errors="coerce")
        cap_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == cap, impact].values[0],errors="coerce")
        insert_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == insert, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = tube_milieuimpact * (weight_tube / 1000) + cap_milieuimpact * (weight_cap / 1000) + insert_milieuimpact * (weight_insert / 1000)
        info = f"{proxy_product} - {volume} ml"
        materialen = f"tube: {tube}, cap: {cap}, insert: {insert}"
        weight = weight_tube + weight_cap + weight_insert
        return milieu_impact, info, weight, materialen

    if categorie == 'Serological Pipettes':
        #assign the standard Serological Pipettes proxy product
        proxy_product = "Serological Pipettes"

        #extract and validate the volume
        if not pd.isna(volume):
            volume = float(volume)
            if (volume > 60) or (volume < 1):
                volume = 10

        if pd.isna(volume):
            volume = 10

        #calculate the pipette and membrane weight based on the volume
        formula_pipet = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula_pipet):
            weight_pipet = eval(formula_pipet, {"__builtins__": {}}, {"x": volume})

        formula_membrane = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0]
        if pd.notna(formula_membrane):
            weight_membrane = eval(formula_membrane, {"__builtins__": {}}, {"x": volume})

        #match the pipette material and use polystyrene as the default
        pipet_materials = {'plastic', 'polystyrene'}
        match_materials = next((v for v in materiaal if v in pipet_materials), None) 
        pipet = match_materials if match_materials is not None else "polystyrene"

        #match the membrane material and use polyester as the default
        membrane_materials = {'cotton', 'polyester'}
        match_materials = next((v for v in materiaal if v in membrane_materials), None) 
        membrane = match_materials if match_materials is not None else "polyester"

        #get the environmental impact per kg for each material
        pipet_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == pipet, impact].values[0],errors="coerce")
        membrane_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == membrane, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = pipet_milieuimpact * (weight_pipet / 1000) + membrane_milieuimpact * (weight_membrane / 1000)
        info = f"{proxy_product} - {volume} ml"
        materialen = f"pipette: {pipet}, membrane: {membrane}"
        weight = weight_pipet + weight_membrane
        return milieu_impact, info, weight, materialen

    if categorie == 'Volumetric Labware':
        #match the product description to a volumetric labware type
        rules = {r"\w*(beker|beaker|maatkan)\w*": "Volumetric Labware - Bekerglas",
                 r"\w*(erlen|erlyn)\w*": "Volumetric Labware - Erlenmeyer",
                 r"\w*(cyl|cilinder)\w*": "Volumetric Labware - Maatcylinder",
                 r"\b(kolf|maatkolf)\b": "Volumetric Labware - Kolf"}

        found = set()

        for pattern, label in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(label)

        if len(found) == 1:
            labware_type = next(iter(found))
        else:
            labware_type = "Volumetric Labware - Maatcylinder"

        #match the labware material and use borosilicate as the default
        labware_materials = {'borosilicate', 'glass', 'soda-lime glass', 'plastic', 'polycarbonate', 'polyethylene', 'polypropylene'}
        match_materials = next((v for v in materiaal if v in labware_materials), None) 
        labware = match_materials if match_materials is not None else "borosilicate"

        #classify the labware as glass or plastic
        if labware in ('borosilicate', 'glass', 'soda-lime glass'):
            materiaal = " Glass"
        else:
            materiaal = " Plastic"

        #select the proxy product based on labware type, material, and volume
        if labware_type in ("Volumetric Labware - Bekerglas", "Volumetric Labware - Maatcylinder") and materiaal in (" Plastic"):
            if not pd.isna(volume):
                volume = float(volume)
                if (volume >= 250):
                    proxy_product = labware_type + materiaal + " Groot"
                else:
                    proxy_product = labware_type + materiaal + " Klein"
            else:
                proxy_product = labware_type + materiaal + " Klein"

        if labware_type in ("Volumetric Labware - Bekerglas", "Volumetric Labware - Maatcylinder") and materiaal in (" Glass"):
            if not pd.isna(volume):
                volume = float(volume)
                if (volume > 250):
                    proxy_product = labware_type + materiaal + " Groot"
                else:
                    proxy_product = labware_type + materiaal + " Klein"
            else:
                proxy_product = labware_type + materiaal + " Klein"

        if labware_type in ("Volumetric Labware - Erlenmeyer", "Volumetric Labware - Kolf"):
            if not pd.isna(volume):
                volume = float(volume)
                if (volume >= 100):
                    proxy_product = labware_type + " Glass Groot"
                else:
                    proxy_product = labware_type + " Glass Klein"
            else:
                proxy_product = labware_type + " Glass Klein"
        
        #get the weight of the proxy product
        labware_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #get the environmental impact per kg for the labware material
        labware_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == labware, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = labware_milieuimpact * (labware_weight / 1000)
        info = f"{proxy_product}"
        materialen = f"labware: {labware}"
        weight = labware_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Containers and Cups':
        proxy_product = 'Containers and Cups'

        #extract and validate the volume
        if not pd.isna(volume):
            volume = float(volume)
            if (volume > 500) or (volume < 0.5):
                volume = 120

        if pd.isna(volume):
            volume = 120

        #calculate the cup weight based on the volume
        formula_cup = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula_cup):
            weight = eval(formula_cup, {"__builtins__": {}}, {"x": volume})

        #match the cup material and use polypropylene as the default
        cups_materials = {'high density polyethylene', 'low density polyethylene', 'plastic', 'polycarbonate', 'polyethylene', 'polypropylene', 'polystyrene', 'stainless steel', 'steel'}
        match_frame = next((v for v in materiaal if v in cups_materials), None)
        cups = match_frame if match_frame is not None else "polypropylene"
        
        # get the environmental impact per kg for the cup material
        cups_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == cups, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = cups_milieuimpact * (weight/1000)
        info = f"{proxy_product} - {volume} ml"
        materialen = f"cup: {cups}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Plate Sealing Foils':

        #match the foil material and use aluminium as the default
        foil_materials = {'aluminium', 'polycarbonate', 'polyester', 'plastic', 'polyethylene', 'polypropylene', 'polyvinyl chloride'}
        match_materials = next((v for v in materiaal if v in foil_materials), None) 
        foil = match_materials if match_materials is not None else "aluminium"

        if foil in ('polycarbonate', 'polyester', 'plastic', 'polyethylene', 'polypropylene', 'polyvinyl chloride'):
            proxy_product = 'Plate Sealing Foils - Plastic'
        else:
            proxy_product = 'Plate Sealing Foils - Aluminium'

        #get the foil weight
        weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #get the environmental impact per kg for the foil and adhesive
        foil_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == foil, impact].values[0],errors="coerce")
        adhesive_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'adhesive', impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = foil_milieuimpact * ((weight * 0.9) / 1000) + adhesive_milieuimpact * ((weight * 0.1) / 1000)
        info = f"{proxy_product}"
        materialen = f"foil: {foil}, adhesive"
        return milieu_impact, info, weight, materialen

    if categorie == 'Microscope Slides':
        proxy_product = 'Microscope Slides'

        #get the slide weight
        weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #match the slide material and use glass as the default
        slides_materials = {'glass', 'acrylic', 'plastic', 'polystyrene'}
        match_frame = next((v for v in materiaal if v in slides_materials), None)
        slides = match_frame if match_frame is not None else "glass"
        
        #get the environmental impact per kg for the slide material
        slides_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == slides, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = slides_milieuimpact * (weight/1000)
        info = f"{proxy_product}"
        materialen = f"slide: {slides}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Pasteur Pipettes':
        if (re.search(r"\bez\w*", text, flags=re.IGNORECASE)
            or proxy_producten_db == "Pasteur Pipettes - EZ-squeeze"):
            proxy_product = "Pasteur Pipettes - EZ-squeeze"

            #get the holding pipette weight
            weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

            #use plastic as the pipette material
            pipet_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'plastic', impact].values[0],errors="coerce")

            #calculate the total environmental impact and weight
            milieu_impact = pipet_milieuimpact * (weight / 1000)
            info = f"{proxy_product}"
            materialen = f"pipette: plastic"
            return milieu_impact, info, weight, materialen

        #use 1 ml as the default volume and keep the volume within the expected range
        if not pd.isna(volume):
            volume = float(volume)
            if (volume > 10) or (volume < 1):
                volume = 1
        else:
            volume = 1

        #match the pipette material and use glass as the default
        pipet_materials = {'borosilicate', 'glass', 'soda-lime glass','plastic', 'high density polyethylene', 'low density polyethylene', 'polycarbonate', 'polyethylene', 'polypropylene', 'polystyrene'}
        match_materials = next((v for v in materiaal if v in pipet_materials), None) 
        pipet = match_materials if match_materials is not None else "glass"

        if pipet in ('borosilicate', 'glass', 'soda-lime glass'):
            proxy_product = 'Pasteur Pipettes - Glass'
        else:
            proxy_product = 'Pasteur Pipettes - Plastic'

        #calculate the pipette weight based on the volume
        formula = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula):
            weight = eval(formula, {"__builtins__": {}}, {"x": volume})

        #get the environmental impact per kg for the pipette material
        pipet_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == pipet, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = pipet_milieuimpact * (weight / 1000)
        info = f"{proxy_product} - {volume} ml"
        materialen = f"pipette: {pipet}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Grip and Safety Bags':
        if (re.search(r"\w*lami\w*", text, flags=re.IGNORECASE)
            or proxy_producten_db == "Grip and Safety Bags - Lamigrip Bags"):
            bag_type = 'Grip and Safety Bags - Lamigrip Bags'
            if isinstance(grootte_afmetingen, list) and len(grootte_afmetingen) > 0:
                bag_grootte = max(grootte_afmetingen)
                if bag_grootte > 40:
                    proxy_product = bag_type + " Large" 
                else:
                    proxy_product = bag_type + " Small"
            else:
                proxy_product = bag_type + " Small"

            #get the bag weight
            weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

            #use aluminium and plastic as the bag materials
            bag1_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'aluminium', impact].values[0],errors="coerce")
            bag2_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == 'plastic', impact].values[0],errors="coerce")

            #calculate the total environmental impact and weight
            milieu_impact = bag1_milieuimpact * ((weight * 0.5) / 1000) + bag2_milieuimpact * ((weight * 0.5) / 1000)
            info = f"{proxy_product}"
            materialen = f"bag: aluminium, plastic"
            return milieu_impact, info, weight, materialen
        
        #match the bag type from the product description
        rules = {
            r"\w*(grip|ziplock|kangoeroe|kangaroo|zipper)\w*": "Grip and Safety Bags - Grip Bags",
            r"\w*(safety|verzendzak|verpakkingszak|zak|chemoprotect)\w*": "Grip and Safety Bags - Safety Bags"
            }

        found = set()

        for pattern, label in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(label)

        if len(found) == 1:
            bag_type = next(iter(found))
        elif len(found) > 1:
            bag_type = "Grip and Safety Bags - Safety Bags"    
        elif pd.notna(proxy_producten_db):
            bag_type = proxy_producten_db
        else:
            return 0.0, None, None, None 

        #select the small or large proxy product based on bag type and size
        if bag_type in ("Grip and Safety Bags - Safety Bags"):
            if isinstance(grootte_afmetingen, list) and len(grootte_afmetingen) > 0:
                bag_grootte = max(grootte_afmetingen)
                if bag_grootte > 18:
                    proxy_product = bag_type + " Large" 
                else:
                    proxy_product = bag_type + " Small"
            else:
                proxy_product = bag_type + " Small"
        if bag_type in ("Grip and Safety Bags - Grip Bags"):
            if isinstance(grootte_afmetingen, list) and len(grootte_afmetingen) > 0:
                bag_grootte = max(grootte_afmetingen)
                if bag_grootte > 21:
                    proxy_product = bag_type + " Large" 
                elif bag_grootte < 16:
                    proxy_product = bag_type + " Small"
                else:
                    proxy_product = bag_type + " Medium"
            else:
                proxy_product = bag_type + " Small" 
        
        #match the bag material and use LDPE as the default
        bag_materials = {'low density polyethylene', 'plastic', 'polyethylene', 'polypropylene'}
        match_materials = next((v for v in materiaal if v in bag_materials), None) 
        bag = match_materials if match_materials is not None else "low density polyethylene"

        #get the bag weight
        bag_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #get the environmental impact per kg for the bag material
        bag_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == bag, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = bag_milieuimpact * (bag_weight / 1000)
        info = f"{proxy_product}"
        materialen = f"bag: {bag}"
        weight = bag_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Dispenser Tips':
        proxy_product = 'Dispenser Tips'

        #use 5 ml as the default volume and keep the volume within the expected range
        if not pd.isna(volume):
            volume = float(volume)
            if (volume > 50) or (volume < 0.05):
                volume = 5
        else:
            volume = 5

        #match the dispenser material and use polypropylene as the default
        dispenser_materials = {'polyethylene', 'polypropylene', 'plastic'}
        match_materials = next((v for v in materiaal if v in dispenser_materials), None) 
        dispenser = match_materials if match_materials is not None else "polypropylene"

        #calculate the dispenser tip weight based on the volume
        formula = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula):
            weight = eval(formula, {"__builtins__": {}}, {"x": volume})

        #get the environmental impact per kg for the dispenser material
        dispenser_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == dispenser, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = dispenser_milieuimpact * (weight / 1000)
        info = f"{proxy_product} - {volume} ml"
        materialen = f"dispenser tips: {dispenser}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Forceps (Reusable)':
        proxy_product = 'Forceps (Reusable)'

        #use 12 cm as the default size and keep the size within the expected range
        if isinstance(grootte_afmetingen, list) and len(grootte_afmetingen) > 0:
            forceps_grootte = max(grootte_afmetingen)
            if (forceps_grootte < 10) or (forceps_grootte > 35):
                forceps_grootte = 12
        else:
            forceps_grootte = 12

        #use stainless steel as the forceps material
        forceps = "stainless steel"

        #calculate the forceps weight based on the size
        formula = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula):
            weight = eval(formula, {"__builtins__": {}}, {"x": forceps_grootte})

        #get the environmental impact per kg for the forceps material
        forceps_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == forceps, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = forceps_milieuimpact * (weight / 1000)
        info = f"{proxy_product} - {forceps_grootte} cm"
        materialen = f"forceps: {forceps}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Forceps (Disposable)':
        proxy_product = 'Forceps (Disposable)'

        #use polystyrene as the forceps material
        forceps = "polystyrene"

        #get the forceps weight
        weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #get the environmental impact per kg for the forceps material
        forceps_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == forceps, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = forceps_milieuimpact * (weight / 1000)
        info = f"{proxy_product}"
        materialen = f"forceps: {forceps}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Bottles':

        #match the bottle and cap materials and use LDPE and polypropylene as defaults
        bottle_materials = {'borosilicate', 'glass', 'soda-lime glass', 'high density polyethylene', 'low density polyethylene', 'plastic', 'polycarbonate', 'polystyrene', 'polyethylene therephthalate', 'polypropylene', 'polyethylene therephthalate glycol'}
        match_materials = next((v for v in materiaal if v in bottle_materials), None) 
        bottle = match_materials if match_materials is not None else "low density polyethylene"

        cap_materials = {'polypropylene', 'aluminium'}
        match_materials = next((v for v in materiaal if v in cap_materials), None) 
        cap = match_materials if match_materials is not None else "polypropylene"

        #select the glass or plastic proxy product based on the bottle material or description
        if bottle in ('borosilicate', 'glass', 'soda-lime glass'):
            proxy_product = 'Bottles - Glass'
        elif re.search(r"\w*(gl\s?45|gl\s?32|gl\s?25|duran|glazen)\w*", text, re.IGNORECASE):
            proxy_product = "Bottles - Glass" 
        else:
            proxy_product = 'Bottles - Plastic'

        #calculate the bottle volume from the dimensions when no volume is available
        if pd.isna(volume) and isinstance(grootte_afmetingen, list) and len(grootte_afmetingen)> 1:
            volume = float(volume)
            if len(grootte_afmetingen) == 1: 
                volume = None
            if len(grootte_afmetingen) == 2:
                diameter = min(grootte_afmetingen)
                hight = max(grootte_afmetingen)
                #calculate volume from diameter and height and adjust for the usable capacity
                volume = (3.14159 * (diameter/2)**2 * hight ) / 1.82
                if diameter < 0.1:
                    volume = None
            if len(grootte_afmetingen) == 3: #diameter * hoogte * wanddikte
                diameter = sorted(grootte_afmetingen)[1]
                hight = max(grootte_afmetingen)
                #calculate volume from diameter and height and adjust for the usable capacity
                volume = (3.14159 * (diameter/2)**2 * hight) / 1.82
            if len(grootte_afmetingen) > 3:
                volume = None

        #use the default volume and keep the volume within the expected range
        if not pd.isna(volume):
            volume = float(volume)
            if (volume > 25000) or (volume < 4):
                volume = 14.965706208791211

        if pd.isna(volume):
            volume = 14.965706208791211

        #calculate the bottle and cap weight based on the volume
        formula_bottle = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula_bottle):
            weight_bottle = eval(formula_bottle, {"__builtins__": {}}, {"x": volume})

        formula_cap = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0]
        if pd.notna(formula_cap):
            weight_cap = eval(formula_cap, {"__builtins__": {}}, {"x": volume})

        #get the environmental impact per kg for the bottle and cap materials
        bottle_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == bottle, impact].values[0],errors="coerce")
        cap_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == cap, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = bottle_milieuimpact * (weight_bottle / 1000) + cap_milieuimpact * (weight_cap / 1000)
        info = f"{proxy_product} - {volume} ml"
        materialen = f"bottle: {bottle}, cap: {cap}"
        weight = weight_bottle + weight_cap
        return milieu_impact, info, weight, materialen

    if categorie == 'Cell Strainers':
        proxy_product = f'Cell Strainers'

        #get the frame and membrane weight
        frame_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
        membrane_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0],errors="coerce")

        #match the frame and membrane materials and use polypropylene and nylon as defaults
        frame_materials = {'plastic', 'polypropylene', "polystyrene"}
        membrane_materials = {'polyester',  'nylon', 'polyethylene therephthalate', 'polycarbonate'}

        match_frame = next((v for v in materiaal if v in frame_materials), None)
        frame = match_frame if match_frame is not None else "polypropylene"

        match_membrane = next((v for v in materiaal if v in membrane_materials), None)
        membrane = match_membrane if match_membrane is not None else "nylon"
        
        #get the environmental impact per kg for the frame and membrane materials
        frame_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == frame, impact].values[0],errors="coerce")
        membrane_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == membrane, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = frame_milieuimpact * (frame_weight/1000) + membrane_milieuimpact * (membrane_weight/1000)
        info = f"{proxy_product}"
        materialen = f"frame: {frame}, membrane: {membrane}"
        weight = frame_weight + membrane_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Reagent Reservoirs':
        #select the small or large proxy product based on volume
        if not pd.isna(volume):
            volume = float(volume)
            if (volume >= 35):
                proxy_product = 'Reagent Reservoirs - Large'
            else:
                proxy_product = 'Reagent Reservoirs - Small'
        else:
            proxy_product = 'Reagent Reservoirs - Small'

        #match the reservoir material and use polystyrene as the default
        reservoir_materials = {'polycarbonate', 'polypropylene', 'polystyrene', 'polyvinyl chloride'}
        match_materials = next((v for v in materiaal if v in reservoir_materials), None) 
        reservoir = match_materials if match_materials is not None else "polystyrene"

        #get the reservoir weight
        weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #get the environmental impact per kg for the reservoir material
        reservoir_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == reservoir, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = reservoir_milieuimpact * (weight / 1000)
        info = f"{proxy_product}"
        materialen = f"reservoir: {reservoir}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Needles':
        #assign the standard Needles proxy product
        proxy_product = "Needles"

        #use 4 cm as the default needle size and keep the size within the expected range
        if isinstance(grootte_afmetingen, list) and len(grootte_afmetingen) > 0:
            needle_grootte = max(grootte_afmetingen)
            if (needle_grootte < 1.2) or (needle_grootte > 10) :
                needle_grootte = 4.0
        else:
            needle_grootte = 4.0

        #calculate the needle and adapter weight based on the size
        formula_needle = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0]
        if pd.notna(formula_needle):
            weight_needle = eval(formula_needle, {"__builtins__": {}}, {"x": needle_grootte})

        formula_adapter = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula_adapter):
            weight_adapter = eval(formula_adapter, {"__builtins__": {}}, {"x": needle_grootte})

        #use stainless steel for the needle and plastic for the adapter
        needle = "stainless steel"
        adapter = "plastic" 

        #get the environmental impact per kg for the needle and adapter materials
        needle_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == needle, impact].values[0],errors="coerce")
        adapter_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == adapter, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = needle_milieuimpact * (weight_needle / 1000) + adapter_milieuimpact * (weight_adapter / 1000)
        info = f"{proxy_product} - {needle_grootte} cm"
        materialen = f"needle {needle}, adapter: {adapter}"
        weight = weight_needle + weight_adapter
        return milieu_impact, info, weight, materialen

    if categorie == 'Trash Bags':
        #match the bag type from the product description
        rules = {r"\b(autoclaaf|autoclave|autoclavable|autoclaafzak|autoclaafzakken|autocl)\b": "Trash Bags - Autoclaafzak",
                 r"\b(vuilniszak|vuilniszakken|vuilnis|waste|disposable|afvalzak|afvalzakken|afval|disposal|vernietigingszak|vernietigingszakken)\b": "Trash Bags - Vuilniszak"}

        found = set()

        for pattern, label in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(label)

        if len(found) == 1:
            bag_type = next(iter(found))
        elif len(found) > 1:
            bag_type = "Trash Bags - Autoclaafzak"        
        elif pd.notna(proxy_producten_db):
            bag_type = proxy_producten_db
        else:
            bag_type = "Trash Bags - Vuilniszak"

        #match the bag material and use polypropylene as the default
        bag_materials = {'high density polyethylene', 'low density polyethylene', 'plastic', 'polypropylene'}
        match_materials = next((v for v in materiaal if v in bag_materials), None) 
        bag = match_materials if match_materials is not None else "polypropylene"

        #select the small or large proxy product based on volume or size
        if not pd.isna(volume):
            volume = float(volume)
            if (volume > 30000):
                proxy_product = bag_type + " Large"
            else:
                proxy_product = bag_type + " Small"
        elif isinstance(grootte_afmetingen, list) and len(grootte_afmetingen) > 0:
            bag_grootte = max(grootte_afmetingen)
            if (bag_grootte > 60):
                proxy_product = bag_type + " Large"
            else:
                proxy_product = bag_type + " Small"                

        else:
            proxy_product = bag_type + " Small"  
        
        #get the bag weight
        bag_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #get the environmental impact per kg for the bag material
        bag_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == bag, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = bag_milieuimpact * (bag_weight / 1000)
        info = f"{proxy_product}"
        materialen = f"bag: {bag}"
        weight = bag_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Filter Paper':
        proxy_product = 'Filter Paper'

        #match the paper material and use paper as the default
        paper_materials = {'polyethylene', 'polyester', 'cotton', 'paper'}
        match_materials = next((v for v in materiaal if v in paper_materials), None) 
        paper = match_materials if match_materials is not None else "paper"

        #determine the filter paper area from the dimensions
        if isinstance(grootte_afmetingen, list) and len(grootte_afmetingen) > 1:
            grootte = float(grootte)
            if len(grootte_afmetingen) == 1:
                grootte = (math.pi / 4) * (grootte ** 2)
            elif len(grootte_afmetingen) == 2:
                grootte = grootte
            else:
                grootte = 2622
        else:
            grootte = 2622 
        
        #calculate the filter paper weight based on the area
        formula = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula):
            weight = eval(formula, {"__builtins__": {}}, {"x": grootte})

        #get the environmental impact per kg for the paper material
        paper_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == paper, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = paper_milieuimpact * (weight / 1000)
        info = f"{proxy_product} - {grootte} cm2"
        materialen = f"paper: {paper}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Blades':
        #match the blade type from the product description
        rules = {r"\b(scalp|autopsie)\b": "Blades - Scalpel",
            r"\w*(scalpel|bistouri)\w*": "Blades - Scalpel",
            r"\b(razor|scheermes)\w*": "Blades - Razorblade",
            r"\w*(stanley|stenley)\w*": "Blades - Razorblade",
            r"\btrimming\w*": "Blades - Trimming Blade"}

        found = set()

        for pattern, label in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(label)

        if "Blades - Scalpel" in found:
            if re.search(r"\w*(handle|handel|houder)\w*", text, re.IGNORECASE):
                found.remove("Blades - Scalpel")
                found.add("Blades - Scalpel with Handle")  
        
        if len(found) == 1:
            proxy_product = next(iter(found))
        elif pd.notna(proxy_producten_db):
            proxy_product = proxy_producten_db
        else:
            proxy_product = "Blades - Scalpel"

        if proxy_product in ("Blades - Scalpel", "Blades - Razorblade", "Blades - Trimming Blade"):
            # Match the blade material and use carbon steel as the default
            blade_materials = {'stainless steel', 'carbon steel', 'steel'}
            match_materials = next((v for v in materiaal if v in blade_materials), None) 
            blade = match_materials if match_materials is not None else "carbon steel"

            # Get the blade weight
            weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

            # Get the environmental impact per kg for the blade material
            blade_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == blade, impact].values[0],errors="coerce")

            # Calculate the total environmental impact and weight
            milieu_impact = blade_milieuimpact * (weight / 1000)
            info = f"{proxy_product}"
            materialen = f"blade: {blade}"
            return milieu_impact, info, weight, materialen

        else:
            # Match the blade material and use stainless steel as the default
            blade_materials = {'stainless steel', 'carbon steel', 'steel'}
            match_materials = next((v for v in materiaal if v in blade_materials), None) 
            blade = match_materials if match_materials is not None else "stainless steel"

            # Match the handle material and use plastic as the default
            handle_materials = {'plastic'}
            match_materials = next((v for v in materiaal if v in handle_materials), None) 
            handle = match_materials if match_materials is not None else "plastic"

            # Get the blade and handle weight
            blade_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
            handle_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0],errors="coerce")

            # Get the environmental impact per kg for the blade and handle materials
            blade_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == blade, impact].values[0],errors="coerce")
            handle_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == handle, impact].values[0],errors="coerce")

            # Calculate the total environmental impact and weight
            milieu_impact = blade_milieuimpact * (blade_weight / 1000) + handle_milieuimpact * (handle_weight / 1000)
            info = f"{proxy_product}"
            materialen = f"blade: {blade}, handle: {handle}"
            weight = blade_weight + handle_weight
            return milieu_impact, info, weight, materialen          

    if categorie == 'Cell Scrapers':
        proxy_product = 'Cell Scrapers'

        #use 28 cm as the default scraper size and keep the size within the expected range
        if isinstance(grootte_afmetingen, list) and len(grootte_afmetingen) > 0:
            scraper_grootte = max(grootte_afmetingen)
            if (scraper_grootte < 3):
                scraper_grootte = 28
        else:
            scraper_grootte = 28

        #match the scraper material and use polystyrene as the default
        scraper_materials = {'low density polyethylene', 'polycarbonate', 'polystyrene'}
        match_materials = next((v for v in materiaal if v in scraper_materials), None) 
        scraper = match_materials if match_materials is not None else "polystyrene"

        #calculate the scraper weight based on the size
        formula = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula):
            weight = eval(formula, {"__builtins__": {}}, {"x": scraper_grootte})

        #get the environmental impact per kg for the scraper material
        scraper_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == scraper, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = scraper_milieuimpact * (weight / 1000)
        info = f"{proxy_product} - {scraper_grootte} cm"
        materialen = f"scraper: {scraper}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Weighing Boats':
        #match the boat material and use polystyrene as the default
        boat_materials = {'aluminium', 'plastic', 'polystyrene', 'polyvinyl chloride'}
        match_materials = next((v for v in materiaal if v in boat_materials), None) 
        boat = match_materials if match_materials is not None else "polystyrene"

        #select the aluminium or plastic proxy product based on size or volume
        if boat in ('aluminium'):
            if isinstance(grootte_afmetingen, list) and len(grootte_afmetingen) > 0:
                boat_grootte = max(grootte_afmetingen)
                if (boat_grootte >= 15):
                    proxy_product = "Weighing Boats - Aluminium Large"
                else:
                    proxy_product = "Weighing Boats - Aluminium Small"  
            else:
                proxy_product = "Weighing Boats - Aluminium Small" 
        else:
            if not pd.isna(volume):
                volume = float(volume)
                if (volume >= 50):
                    proxy_product = "Weighing Boats - Plastic Large"
                else:
                    proxy_product = "Weighing Boats - Plastic Small"
            elif isinstance(grootte_afmetingen, list) and len(grootte_afmetingen) > 0:
                boat_grootte = max(grootte_afmetingen)
                if (boat_grootte >= 8):
                    proxy_product = "Weighing Boats - Plastic Large"
                else:
                    proxy_product = "Weighing Boats - Plastic Small" 
            else:
                proxy_product = "Weighing Boats - Plastic Small"              
        
        #get the boat weight
        weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #get the environmental impact per kg for the boat material
        boat_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == boat, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = boat_milieuimpact * (weight / 1000)
        info = f"{proxy_product}"
        materialen = f"boat: {boat}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Embedding Cassettes':
        #match the cassette type from the product description
        rules = {r"\w*(mega|maxi)\w*": "Embedding Cassettes - Mega"}

        found = set()

        for pattern, label in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(label)

        if len(found) == 1:
            proxy_product = next(iter(found))
        elif pd.notna(proxy_producten_db):
            proxy_product = proxy_producten_db
        else:
            proxy_product = "Embedding Cassettes"

        #use polyoxymethylene as the cassette material
        cassettes = "polyoxymethylene"

        #get the cassette weight
        weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #get the environmental impact per kg for the cassette material
        cassettes_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == cassettes, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = cassettes_milieuimpact * (weight / 1000)
        info = f"{proxy_product}"
        materialen = f"cassettes: {cassettes}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Swabs':
        #match the tip and stem materials and use polyester and plastic as defaults
        tip_materials = {'cotton', 'nylon', 'polyester'}
        stem_materials = {'wood', 'plastic'}

        match_tip = next((v for v in materiaal if v in tip_materials), None)
        tip = match_tip if match_tip is not None else "polyester"

        match_stem = next((v for v in materiaal if v in stem_materials), None)
        stem = match_stem if match_stem  is not None else "plastic"

        if stem in ('wood'):
            proxy_product = "Swabs - Wood"
        else:
            proxy_product = "Swabs - Plastic"

        #get the tip and stem weight
        tip_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0],errors="coerce")
        stem_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
        
        #get the environmental impact per kg for the tip and stem materials
        tip_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == tip, impact].values[0],errors="coerce")
        stem_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == stem, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = tip_milieuimpact * (tip_weight/1000) + stem_milieuimpact * (stem_weight/1000)
        info = f"{proxy_product}"
        materialen = f"tip: {tip}, stem: {stem}"
        weight = tip_weight + stem_weight
        return milieu_impact, info, weight, materialen

    if categorie == 'Safe-Cone Filters':
        proxy_product = "Safe-Cone Filters"

        #use polyethylene as the filter material
        filters = "polyethylene"

        #get the filter weight
        weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #get the environmental impact per kg for the filter material
        filters_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == filters, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = filters_milieuimpact * (weight / 1000)
        info = f"{proxy_product}"
        materialen = f"filter: {filters}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Strawpipettes':
        proxy_product = "Strawpipettes"

        #use polypropylene as the pipette material
        pipet = "polypropylene"

        #get the pipette weight
        weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #get the environmental impact per kg for the pipette material
        pipet_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == pipet, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = pipet_milieuimpact * (weight / 1000)
        info = f"proxy: {proxy_product}"
        materialen = f"pipette: {pipet}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Spatulas (Reusable)':
        proxy_product = 'Spatulas (Reusable)'

        #use 18 cm as the default spatula size and keep the size within the expected range
        if isinstance(grootte_afmetingen, list) and len(grootte_afmetingen) > 0:
            spatulas_grootte = max(grootte_afmetingen)
            if (spatulas_grootte < 5) or (spatulas_grootte > 35):
                spatulas_grootte = 18
        else:
            spatulas_grootte = 18

        #match the spatula material and use stainless steel as the default
        spatulas_materials = {'steel', 'stainless steel'}
        match_materials = next((v for v in materiaal if v in spatulas_materials), None) 
        spatulas = match_materials if match_materials is not None else "stainless steel"

        #calculate the spatula weight based on the size
        formula = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula):
            weight = eval(formula, {"__builtins__": {}}, {"x": spatulas_grootte})

        #get the environmental impact per kg for the spatula material
        spatulas_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == spatulas, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = spatulas_milieuimpact * (weight / 1000)
        info = f"{proxy_product} - {spatulas_grootte} cm"
        materialen = f"spatula: {spatulas}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Spatulas (Disposable)':
        proxy_product = 'Spatulas (Disposable)'

        #use 21 cm as the default spatula size and keep the size within the expected range
        if isinstance(grootte_afmetingen, list) and len(grootte_afmetingen) > 0:
            spatulas_grootte = max(grootte_afmetingen)
            if (spatulas_grootte < 5) or (spatulas_grootte > 35):
                spatulas_grootte = 21
        else:
            spatulas_grootte = 21

        #match the spatula material and use polypropylene as the default
        spatulas_materials = {'high density polyethylene', 'polyethylene', 'polypropylene', 'polystyrene'}
        match_materials = next((v for v in materiaal if v in spatulas_materials), None) 
        spatulas = match_materials if match_materials is not None else "polypropylene"

        #calculate the spatula weight based on the size
        formula = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula):
            weight = eval(formula, {"__builtins__": {}}, {"x": spatulas_grootte})

        #get the environmental impact per kg for the spatula material
        spatulas_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == spatulas, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = spatulas_milieuimpact * (weight / 1000)
        info = f"{proxy_product} - {spatulas_grootte}"
        materialen = f"spatula: {spatulas}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Lens Cleaning Tissues':
        proxy_product = 'Lens Cleaning Tissues'

        #use paper as the tissue material
        paper = "paper"

        #get the tissue weight
        weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #get the environmental impact per kg for the paper material
        paper_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == paper, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = paper_milieuimpact * (weight / 1000)
        info = f"{proxy_product}"
        materialen = f"paper: {paper}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Plate Sealing Mats':
        proxy_product = 'Plate Sealing Mats'

        #match the mat material and use thermoplastic elastomers as the default
        mats_materials = {'polypropylene', 'silicone', 'thermoplastic elastomers'}
        match_materials = next((v for v in materiaal if v in mats_materials), None) 
        mats = match_materials if match_materials is not None else "thermoplastic elastomers"

        #get the mat weight
        weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #get the environmental impact per kg for the mat material
        mats_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == mats, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = mats_milieuimpact * (weight / 1000)
        info = f"{proxy_product}"
        materialen = f"mats: {mats}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Spreaders':
        proxy_product = 'Spreaders'

        #match the spreader material and use polystyrene as the default
        spreader_materials = {'polypropylene', 'polycarbonate', 'polystyrene'}
        match_materials = next((v for v in materiaal if v in spreader_materials), None) 
        spreader = match_materials if match_materials is not None else "polystyrene"

        #get the spreader weight
        weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #get the environmental impact per kg for the spreader material
        spreader_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == spreader, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = spreader_milieuimpact * (weight / 1000)
        info = f"{proxy_product}"
        materialen = f"spreader: {spreader}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Sealing Film':
        proxy_product = 'Sealing Film'

        foil = "polyvinyl chloride"
        rol = "cardboard"

        #get the film and roll weight
        weight_foil = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
        weight_rol = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0],errors="coerce")

        #get the environmental impact per kg for the film and roll materials
        foil_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == foil, impact].values[0],errors="coerce")
        rol_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == rol, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = foil_milieuimpact * (weight_foil / 1000) + rol_milieuimpact * (weight_rol / 1000)
        info = f"{proxy_product}"
        materialen = f"foil: {foil}, rol: {rol}"
        weight = weight_foil + weight_rol
        return milieu_impact, info, weight, materialen

    if categorie == 'Microtome Blades':
        proxy_product = 'Microtome Blades'

        #match the blade material and use steel as the default
        blade_materials = {'stainless steel', 'carbon steel', 'steel'}
        match_materials = next((v for v in materiaal if v in blade_materials), None) 
        blade = match_materials if match_materials is not None else "steel"

        #get the blade weight
        weight_blade = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #get the environmental impact per kg for the blade material
        blade_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == blade, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = blade_milieuimpact * (weight_blade / 1000)
        info = f"{proxy_product}"
        materialen = f"blade: {blade}"
        weight = weight_blade
        return milieu_impact, info, weight, materialen

    if categorie == 'Grinding Chambers':
        #select the small or large proxy product based on volume
        if not pd.isna(volume):
            volume = float(volume)
            if (volume == 40):
                proxy_product = 'Grinding Chambers - Small'
            elif (volume == 100):
                proxy_product = 'Grinding Chambers - Large'                
            else:
                proxy_product = 'Grinding Chambers - Small'
        else:
            proxy_product = 'Grinding Chambers - Small'

        #use polypropylene for the chamber and cap, and match the blade material
        chamber = 'polypropylene'
        chassis_and_coupling_piece = 'polypropylene' #translation: onderstel en koppelstuk
        blade_materials = {'stainless steel', 'carbon steel', 'steel'}
        match_materials = next((v for v in materiaal if v in blade_materials), None) 
        blade = match_materials if match_materials is not None else "steel"

        #get the weight of the chamber, cap, and blade
        weight_chamber = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
        weight_chassis_and_coupling_piece = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0],errors="coerce")
        weight_blade = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel3"].values[0],errors="coerce")

        #get the environmental impact per kg for each material
        chamber_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == chamber, impact].values[0],errors="coerce")
        chassis_and_coupling_piece_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == chassis_and_coupling_piece, impact].values[0],errors="coerce")
        blade_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == blade, impact].values[0],errors="coerce")
        
        #calculate the total environmental impact and weight
        milieu_impact = chamber_milieuimpact * (weight_chamber / 1000) + chassis_and_coupling_piece_milieuimpact * (weight_chassis_and_coupling_piece / 1000) + blade_milieuimpact * (weight_blade / 1000)
        info = f"{proxy_product}"
        materialen = f"chamber: {chamber}, chassis and coupling piece: {chassis_and_coupling_piece}, blade: {blade}"
        weight = weight_chamber + weight_chassis_and_coupling_piece + weight_blade
        return milieu_impact, info, weight, materialen

    if categorie == 'Cleaning Tissues':
        proxy_product = 'Cleaning Tissues'

        #use paper as the material
        paper = "paper"

        #get the tissue weight
        weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #get the environmental impact per kg for the paper material
        paper_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == paper, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = paper_milieuimpact * (weight / 1000)
        info = f"{proxy_product}"
        materialen = f"paper: {paper}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Weighing Paper':
        proxy_product = 'Weighing Paper'

        #use paper as the material
        paper = "paper"

        #determine the paper size from the dimensions
        if isinstance(grootte_afmetingen, list) and len(grootte_afmetingen) == 2:
            paper_size = float(grootte)
        else:
            paper_size = 100
            
        #calculate the paper weight based on the size
        formula = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula):
            weight = eval(formula, {"__builtins__": {}}, {"x": paper_size})

        #get the environmental impact per kg for the paper material
        paper_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == paper, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = paper_milieuimpact * (weight / 1000)
        info = f"{proxy_product} - {paper_size} cm2"
        materialen = f"paper: {paper}"
        return milieu_impact, info, weight, materialen

    if categorie == 'TORK Paper Roll':
        proxy_product = 'TORK Paper Roll'

        #use paper and cardboard as the roll materials
        paper = "paper"
        roll = 'cardboard'

        #get the paper and roll weight
        weight_paper = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
        weight_roll = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0],errors="coerce")

        #get the environmental impact per kg for each material
        paper_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == paper, impact].values[0],errors="coerce")
        roll_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == roll, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = paper_milieuimpact * (weight_paper / 1000) + roll_milieuimpact * (weight_roll / 1000)
        info = f"{proxy_product}"
        materialen = f"paper: {paper}, roll: {roll}"
        weight = weight_paper + weight_roll
        return milieu_impact, info, weight, materialen

    if categorie == 'Syringes':

        #match the syringe type from the product description
        rules = {r"\w*(2-delig|2-piece)\w*": "Syringes - 2-delig",
                 r"\w*(3-delig|3-piece)\w*": "Syringes - 3-delig"}

        found = set()

        for pattern, label in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(label)

        if len(found) == 1:
            proxy_product = next(iter(found))
        elif len(found) > 1:
            proxy_product = "Syringes - 3-delig"        
        elif pd.notna(proxy_producten_db):
            proxy_product = proxy_producten_db
        else:
            proxy_product = "Syringes - 3-delig"


        #extract the volume and keep it within the expected range
        if not pd.isna(volume):
            volume = float(volume)
            if (volume > 60) or (volume < 0.01):
                volume = 3

        if pd.isna(volume):
            volume = 3

        #match the syringe and plunger materials
        syringe_materials = {'plastic', 'polypropylene'}
        match_materials = next((v for v in materiaal if v in syringe_materials), None) 
        syringe = match_materials if match_materials is not None else "polypropylene"

        plunger_materials = {'polystyrene', 'polypropylene', 'polyethylene'}
        match_materials = next((v for v in materiaal if v in plunger_materials), None) 
        plunger = match_materials if match_materials is not None else "polypropylene"

        #calculate the syringe and plunger weight based on the volume
        formula_syringe = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0]
        if pd.notna(formula_syringe):
            weight_syringe = eval(formula_syringe, {"__builtins__": {}}, {"x": volume})

        formula_plunger = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0]
        if pd.notna(formula_plunger):
            weight_plunger = eval(formula_plunger, {"__builtins__": {}}, {"x": volume})

        #get the environmental impact per kg for the syringe and plunger materials
        syringe_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == syringe, impact].values[0],errors="coerce")
        plunger_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == plunger, impact].values[0],errors="coerce")

        if proxy_product == "Syringes - 2-delig":
            #calculate the total environmental impact and weight
            milieu_impact = syringe_milieuimpact * (weight_syringe / 1000) + plunger_milieuimpact * (weight_plunger / 1000)
            info = f"{proxy_product} - {volume} ml"
            materialen = f"syringe: {syringe}, plunger: {plunger}"
            weight = weight_syringe + weight_plunger
        else:
            #use rubber as the stopper material
            stopper = 'rubber'

            #calculate the stopper weight based on the volume
            formula_stopper = weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel3"].values[0]
            if pd.notna(formula_stopper):
                weight_stopper = eval(formula_stopper, {"__builtins__": {}}, {"x": volume})

            #get the environmental impact per kg for the stopper material
            stopper_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == stopper, impact].values[0],errors="coerce")

            #calculate the total environmental impact and weight
            milieu_impact = syringe_milieuimpact * (weight_syringe / 1000) + plunger_milieuimpact * (weight_plunger / 1000) + stopper_milieuimpact * (weight_stopper / 1000)
            info = f"{proxy_product} - {volume} ml"
            materialen = f"syringe: {syringe}, plunger: {plunger}, stopper: {stopper}"
            weight = weight_syringe + weight_plunger + weight_stopper
        return milieu_impact, info, weight, materialen

    if categorie == 'Sleeve Protectors':
        proxy_product = 'Sleeve Protectors'

        #use high density polyethylene as the sleeve material
        sleeve = "high density polyethylene"

        #get the sleeve weight
        weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #get the environmental impact per kg for the sleeve material
        sleeve_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == sleeve, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = sleeve_milieuimpact * (weight / 1000)
        info = f"{proxy_product}"
        materialen = f"sleeve: {sleeve}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Sample Collection Tubes':
        #match the sample collection tube type from the product description
        rules = {
             r"\b(eswab|copan|flocked)\b": "Sample Collection Tubes - Eswab",
             r"\b(faeces|lepelbuis)\w*": "Sample Collection Tubes - Lepelbuis",
             r"\bsalivette\w*": "Sample Collection Tubes - Salivette"}
        
        found = set()

        for pattern, label in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(label)

        if len(found) == 1:
            proxy_product = next(iter(found))
        elif len(found) > 1:
            proxy_product = "Sample Collection Tubes - Eswab"
        elif pd.notna(proxy_producten_db):
            proxy_product = proxy_producten_db
        else:
            proxy_product = "Sample Collection Tubes - Eswab"

        #get the tube and cap weight
        tube_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
        cap_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0],errors="coerce")

        #match the tube and cap materials
        tube_materials = {'plastic', 'polypropylene'}
        match_tube = next((v for v in materiaal if v in tube_materials), None)
        tube = match_tube if match_tube is not None else "polypropylene"

        cap_materials = {'plastic', 'polypropylene', 'high density polyethylene', 'high density polyethylene'}
        match_cap = next((v for v in materiaal if v in cap_materials), None)
        cap = match_cap if match_cap is not None else "polypropylene"

        #get the environmental impact per kg for the tube and cap materials
        tube_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == tube, impact].values[0],errors="coerce")
        cap_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == cap, impact].values[0],errors="coerce")

        if proxy_product == "Sample Collection Tubes - Salivette":
            #get the inner tube and cotton weight
            innertube_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel4"].values[0],errors="coerce")
            cotton_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel3"].values[0],errors="coerce")

            #match the inner tube and cotton materials
            innertube_materials = {'plastic', 'polypropylene'}
            match_tube = next((v for v in materiaal if v in innertube_materials), None)
            innertube = match_tube if match_tube is not None else "polypropylene"

            cotton_materials = {'cotton', 'nylon', 'polyester'}
            match_cotton = next((v for v in materiaal if v in cotton_materials), None)
            cotton = match_cotton if match_cotton is not None else "polyester"

            #get the environmental impact per kg for the inner tube and cotton materials
            innertube_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == innertube, impact].values[0],errors="coerce")
            cotton_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == cotton, impact].values[0],errors="coerce")

            #calculate the total environmental impact and weight
            milieu_impact = tube_milieuimpact * (tube_weight / 1000) + cap_milieuimpact * (cap_weight / 1000) + innertube_milieuimpact * (innertube_weight / 1000) + cotton_milieuimpact * (cotton_weight / 1000)
            info = f"{proxy_product}"
            materialen = f"tube:{tube}, cap: {cap}, innertube: {innertube}, cotton: {cotton}"
            weight = tube_weight + cap_weight + innertube_weight + cotton_weight
            return milieu_impact, info, weight, materialen

        elif proxy_product == "Sample Collection Tubes - Lepelbuis":
            #get the spoon weight
            lepel_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel3"].values[0],errors="coerce")

            #match the spoon material and use polystyrene as the default
            lepel_materials = {'plastic', 'polystyrene'}
            match_lepel = next((v for v in materiaal if v in lepel_materials), None)
            lepel = match_lepel if match_lepel is not None else "polystyrene"

            #get the environmental impact per kg for the spoon material
            lepel_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == lepel, impact].values[0],errors="coerce")

            #calculate the total environmental impact and weight
            milieu_impact = tube_milieuimpact * (tube_weight / 1000) + cap_milieuimpact * (cap_weight / 1000) + lepel_milieuimpact * (lepel_weight / 1000)
            info = f"{proxy_product}"
            materialen = f"tube: {tube}, cap: {cap}, lepel: {lepel}"
            weight = tube_weight + cap_weight + lepel_weight
            return milieu_impact, info, weight, materialen


        else: # proxy_product == "Sample Collection Tubes - Eswab"
            #get the swab and cotton weight
            swab_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel4"].values[0],errors="coerce")
            cotton_weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel3"].values[0],errors="coerce")

            #match the swab material and use polypropylene as the default
            swab_materials = {'plastic', 'polypropylene', 'polystyrene'}
            match_swab = next((v for v in materiaal if v in swab_materials), None)
            swab = match_tube if match_swab is not None else "polypropylene"

            #match the cotton material and use nylon as the default
            cotton_materials = {'cotton', 'nylon', 'polyester'}
            match_cotton = next((v for v in materiaal if v in cotton_materials), None)
            cotton = match_cotton if match_cotton is not None else "nylon"

            #get the environmental impact per kg for the swab and cotton materials
            swab_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == swab, impact].values[0],errors="coerce")
            cotton_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == cotton, impact].values[0],errors="coerce")

            #calculate the total environmental impact and weight
            milieu_impact = tube_milieuimpact * (tube_weight / 1000) + cap_milieuimpact * (cap_weight / 1000) + swab_milieuimpact * (swab_weight / 1000) + cotton_milieuimpact * (cotton_weight / 1000)
            info = f"{proxy_product}"
            materialen = f"tube: {tube}, cap: {cap}, swab: {swab}, cotton: {cotton}"
            weight = tube_weight + cap_weight + swab_weight + cotton_weight
            return milieu_impact, info, weight, materialen

    if categorie == 'Chambered Slides':
        proxy_product = 'Chambered Slides'

        #get the slide weight
        weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #use polystyrene as the slide material
        slide_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == "polystyrene", impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = slide_milieuimpact * (weight / 1000)
        info = f"{proxy_product}"
        materialen = f"slide: polystyrene"
        return milieu_impact, info, weight, materialen

    if categorie == 'Labcoats':
        proxy_product = 'Labcoats'

        #use polypropylene, polyethylene, plastic, and rubber for the coat components
        coat = 'polypropylene'
        coat_coating = 'polyethylene'
        buttons = "plastic"
        elastiek = 'rubber'

        #get the weight of the coat, buttons, and elastic
        weight_coat = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
        weight_buttons = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0],errors="coerce")
        weight_elastiek = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel3"].values[0],errors="coerce")

        #get the environmental impact per kg for each material
        coat_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == coat, impact].values[0],errors="coerce")
        coating_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == coat_coating, impact].values[0],errors="coerce")
        buttons_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == buttons, impact].values[0],errors="coerce")
        elastiek_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == elastiek, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = coat_milieuimpact * ((weight_coat * 0.9) / 1000) + coating_milieuimpact * ((weight_coat * 0.1) / 1000) + buttons_milieuimpact * (weight_buttons / 1000) + elastiek_milieuimpact * (weight_elastiek / 1000)
        info = f"{proxy_product}"
        materialen = f"coat: {coat}, coat coating: {coat_coating}, buttons: {buttons}, elastic: {elastiek}"
        weight = weight_coat + weight_buttons + weight_elastiek
        return milieu_impact, info, weight, materialen

    if categorie == 'Fingerprick Lancet':
        proxy_product = 'Fingerprick Lancet'

        #use polypropylene for the case and stainless steel for the needle and spring
        case = "polypropylene"
        needle_spring = 'stainless steel'

        #get the weight of the case, needle, and spring
        weight_case = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
        weight_needle_spring = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel2"].values[0],errors="coerce")

        #get the environmental impact per kg for each material
        case_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == case, impact].values[0],errors="coerce")
        needle_spring_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == needle_spring, impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = case_milieuimpact * (weight_case / 1000) + needle_spring_milieuimpact * (weight_needle_spring / 1000)
        info = f"{proxy_product}"
        materialen = f"case: {case}, needle and spring: {needle_spring}"
        weight = weight_case + weight_needle_spring
        return milieu_impact, info, weight, materialen

    if categorie == 'Printer Paper':
        proxy_product = 'Printer Paper'

        #get the paper weight
        weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #use paper as the material
        paper_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == "paper", impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = paper_milieuimpact * (weight / 1000)
        info = f"{proxy_product}"
        materialen = f"paper: paper"
        return milieu_impact, info, weight, materialen

    if categorie == 'Teststrips':
        proxy_product = 'Teststrips'

        #get the test strip weight
        weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")

        #use paper as the test strip material
        paper_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == "paper", impact].values[0],errors="coerce")

        #calculate the total environmental impact and weight
        milieu_impact = paper_milieuimpact * (weight / 1000)
        info = f"{proxy_product}"
        materialen = f"teststrip: paper"
        return milieu_impact, info, weight, materialen

    if categorie == 'Vitrification Devices':
        proxy_product = "Inoculating Loops" #used as the replacement weight

        #get the weight of the proxy product
        weight = pd.to_numeric(weight_data.loc[weight_data["proxy_product"] == proxy_product, "onderdeel1"].values[0],errors="coerce")
    
        #use plastic as the material
        loop = 'plastic'
        
        #get the environmental impact per kg for the plastic material
        loop_milieuimpact = pd.to_numeric(milieuimpact_data.loc[milieuimpact_data["materiaal"] == loop, impact].values[0],errors="coerce")
    
        #calculate the total environmental impact and weight
        milieu_impact = loop_milieuimpact * (weight/1000)
        info = f"{proxy_product}"
        materialen = f"vitrification device: {loop}"
        return milieu_impact, info, weight, materialen

    if categorie == 'Masks':
        proxy_product = None

        #match the mask type from the product description
        rules = {r".*IIR.*": "Masks - IIR",
                 r".*FFP.*": "Masks - FFP",
                 r".*(?<!z.)vent(iel)?.*": "Masks - FFP vented",
                 r".*(?<!non\s)vented.*": "Masks - FFP vented",
                 r".*non\s+vented.*": "Masks - FFP",
                 r".*z.\s*vent(iel)?.*": "Masks - FFP"}

        found = set()

        for pattern, label in rules.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(label)
        
        if len(found) == 1:
            proxy_product = next(iter(found))
        else:
            if "Masks - FFP vented" in found: #give vented masks priority over non-vented masks
                proxy_product = "Masks - FFP vented"
            else:
                proxy_product = "Masks - FFP"

        #use the database proxy product when available
        if pd.notna(proxy_producten_db):
            proxy_product = proxy_producten_db
        
        if proxy_product is None:
            proxy_product = "Masks - IIR"

        if proxy_product == "Masks - IIR":
            milieu_impact = 0.013
            weight = 2.985
        if proxy_product == "Masks - FFP":
            milieu_impact = 0.076
            weight = 8.785
        if proxy_product == "Masks - FFP vented":
            milieu_impact = 0.125
            weight = 8.785
        
        info = f"{proxy_product}"
        materialen = "Unavailable"
        return milieu_impact, info, weight, materialen

    return None, None, None
