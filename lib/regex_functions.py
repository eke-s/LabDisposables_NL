import re
import pandas as pd
from typing import Tuple

def pick_max_product(dlist):
    """
    Select the item with the highest product quantity and return its packaging type and quantity
    - dlist = list of dictionaries containing product information, including 'Productaantallen' and 'Verpakkingssoort'
    """

    def parse_int(value):
        """
        Convert a value to an integer after removing thousand separators
        - value = value to convert, typically a string or numeric value
        """
        if isinstance(value, str):
            value = value.replace('.', '')  #remove thousands separators

        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    #parse all Productaantallen
    for d in dlist:
        d['Productaantallen'] = parse_int(d.get('Productaantallen'))

    #keep only items with valid product quantities
    valid_items = [d for d in dlist if isinstance(d.get('Productaantallen'), int)]

    if not valid_items:
        return None, None  #return two separate None values

    #find the item with the highest product quantity
    max_pa = max(d['Productaantallen'] for d in valid_items)
    max_dict = next(d for d in valid_items if d['Productaantallen'] == max_pa)

    return max_dict.get('Verpakkingssoort'), max_dict.get('Productaantallen')

#Regex Number of Items
def get_number_of_items(text: str):
    """
    Extract the number of items and packaging type from a product description
    - text = product description to search for item quantities and packaging information
    """

    def find_number_of_items(text: str) -> list:
        """
        Find item quantities and packaging types in a product description using regular expressions
        - text: product description to search for item quantities and packaging information
        """

        results = []

        def _compute_regex(pattern: str, verpakkingssoort: str, productaantallen=None, vermenigvuldiging=False):
            """
            Apply a regular expression and store the matched product quantity and packaging type
            - pattern: regular expression used to find a product quantity
            - verpakkingssoort: packaging type associated with the matched quantity
            - productaantallen: fixed product quantity to use instead of extracting it from the match
            - vermenigvuldiging: whether the product quantity should be calculated by multiplying two values
            """

            match = re.search(pattern, text)

            if match:
                if productaantallen is not None:
                    aantal = productaantallen

                elif vermenigvuldiging:
                    try:
                        per_stuk = int(match.group(3).replace('.', '').replace(',', ''))
                        aantal = int(match.group(2)) * per_stuk
                    except (IndexError, ValueError, AttributeError):
                        aantal = None

                else:
                    try:
                        aantal = int(match.group(2).replace('.', '').replace(',', ''))
                    except (IndexError, ValueError, AttributeError):
                        aantal = None

                if aantal <= 0 or aantal > 99999:
                    aantal = None

                results.append({
                    "Match": match.group(0),
                    "Verpakkingssoort": verpakkingssoort,
                    "Productaantallen": aantal
                })

        #extract fixed quantities from St
        pattern = r"(?i)\b(st)\b"
        _compute_regex(pattern, 'stuks', 1)

        #extract fixed quantities from Stk
        pattern = r"(?i)\b(stk)\b"
        _compute_regex(pattern, 'stuks', 1)

        #extract fixed quantities from stuks
        pattern = r"(?i)(stuks?)\b"
        _compute_regex(pattern, 'stuks', 1)

        #extract fixed quantities from p/st
        pattern = r"(?i)(p\s*/\s*st)"
        _compute_regex(pattern, 'stuks', 1)

        #extract numbers followed by St, Stk, Stuk, or Stuks, with optional spaces or parentheses
        pattern = r"(?i)(\(?((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s?(?:st(?:k)?|stu?ks?)\b\)?,?)"
        _compute_regex(pattern, 'stuks')

        #extract numbers followed by CA
        pattern = r"(?i)(\(?((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*CA\)?\b)"
        _compute_regex(pattern, 'stuks')

        #extract multiplied quantities such as (10x96 ST) or (1 * 5 ST)
        pattern = r"(?i)(\(\s*(\d+)\s*(?:x|\*)\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*(?:st(?:k)?|stu?ks?)\b\))"
        _compute_regex(pattern, 'stuks', vermenigvuldiging=True)

        #extract multiplied quantities followed by item-related terms
        pattern = r"(?i)(\(?\s*(\d+)\s*(?:x|\*)\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*(?:items?|i|tips|pieces|pcs|pce|krt)\)?)"
        _compute_regex(pattern, 'stuks', vermenigvuldiging=True)

        #extract multiplied quantities without an item description
        pattern = r"(?i)(\(\s*(\d+)\s*(?:x|\*)\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*(?:\)|$))"
        _compute_regex(pattern, 'stuks', vermenigvuldiging=True)

        #extract multiplied quantities followed by rolls
        pattern = r"(?i)(\(\s*(\d+)\s*(?:x|\*)\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*roll?s?\))"
        _compute_regex(pattern, 'roll', vermenigvuldiging=True)

        #extract numbers followed by specific item types such as slides, tests, strips, or tubes
        pattern = r"(?i)(\(?((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*(?:slides?|te?sts|testen|strips?|tubes?|buizen|pieces?|pcs|pce|plates?|tips|sheets?)\)?)"
        _compute_regex(pattern, 'stuks')

        #extract quantities specified as items per case
        pattern = r"(?i)(\(\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*/\s*(?:case)s?\s*\))"
        _compute_regex(pattern, 'stuks')

        #extract quantities following Ds or Doos
        pattern = r"(?i)(D(?:oo)?S\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*?(?:ds)?)\b"
        _compute_regex(pattern, "doos")

        #extract quantities followed by box or boxes
        pattern = r"(?i)(((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*boxe?s?)\b"
        _compute_regex(pattern, "doos")

        #extract quantities following Ds or Doos and followed by St or Stuks
        pattern = r"(?i)(D(?:oo)?S\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*(?:st(?:k)?|stuks?))\b"
        _compute_regex(pattern, "stuks")

        #extract multiplied quantities following Ds or Doos
        pattern = r"(?i)(D(?:oo)?S\s*(\d+)\s*(?:x|\*)\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*(?:st(?:k)?|stuks?)?)\b"
        _compute_regex(pattern, "stuks", vermenigvuldiging=True)

        #extract quantities following Ds or Doos with packaging terms such as rolls, packs, or bottles
        pattern = r"(?i)(D(?:oo)?S\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*(?:vel(?:len)?|rol(?:len)?|pak(?:ken)?|zak(?:ken)?|fles(?:sen)?|p(?:aa)?r|m|sets?|kits?|rek(?:ken)?|bus(?:sen)?|pla?at(?:en)?))\b"
        _compute_regex(pattern, "stuks")

        #extract quantities following Pak or Pack and St or Stuks
        pattern = r"(?i)(pa?k\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*(?:st(?:k)?|stuks?))\b"
        _compute_regex(pattern, "stuks")

        #extract quantities following Pak or Pack with other packaging terms
        pattern = r"(?i)(pa?k\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*(?:vel(?:len)?|rol(?:len)?|pak(?:ken)?|zak(?:ken)?|fles(?:sen)?|p(?:aa)?r|m|sets?|kits?|rek(?:ken)?|bus(?:sen)?|pla?at(?:en)?))\b"
        _compute_regex(pattern, "stuks")

        #extract quantities specified per pack or box
        pattern = r"(?i)(((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*/\s*(?:pa?kg?|bo?x))\b"
        _compute_regex(pattern, "stuks")

        #extract quantities specified after pack or box
        pattern = r"(?i)((?:pa?kg?|bo?x)\s*/\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+)))\b"
        _compute_regex(pattern, "stuks")

        #extract quantities specified as pack or case of a given number of items
        pattern = r"(?i)((?:pack|case) of\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*(?:pieces?|rolls?|bags?|bottles?|pairs?|sets?|kits?|racks?|plates?)?)\b"
        _compute_regex(pattern, "stuks")

        #extract multiplied quantities specified as pack or case of multiple items
        pattern = r"(?i)((?:pack|case) of\s*(\d+)\s*(?:x|\*)\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*(?:pieces?|pcs|pce|rolls?|bags?|bottles?|pairs?|sets?|kits?|racks?|plates?)?)\b"
        _compute_regex(pattern, "stuks", vermenigvuldiging=True)

        #extract quantities specified as items per case
        pattern = r"(?i)(\(?((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*per case\)?)"
        _compute_regex(pattern, 'stuks')

        #extract fixed quantities from packaging terms such as pak, doos, and VRP
        pattern = r"(?i)(pak|doos|VRP)\b"
        _compute_regex(pattern, 'verpakking', 1)

        #extract quantities following Verp or Verpa and St or Stuks
        pattern = r"(?i)(v(?:er)?p\s*(?:a|van)?\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*(?:st(?:k)?|stuks?))\b"
        _compute_regex(pattern, "stuks")

        #extract quantities following Verp or Verpa with other packaging terms
        pattern = r"(?i)(v(?:er)?p\s*(?:a|van)?\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*(?:vel(?:len)?|rol(?:len)?|pak(?:ken)?|zak(?:ken)?|fles(?:sen)?|p(?:aa)?r|m|sets?|kits?|rek(?:ken)?|bus(?:sen)?|pla?at(?:en)?))\b"
        _compute_regex(pattern, "stuks")

        #extract multiplied quantities following Verp or Verpa
        pattern = r"(([1-9]+[0-9]*)v(?:er)?p\s*(?:a|van)?\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*(?:st(?:k)?|stuks?))\b"
        _compute_regex(pattern, "stuks", vermenigvuldiging=True)

        #extract quantities specified as each
        pattern = r"(?i)(\(?((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*each\)?)"
        _compute_regex(pattern, "stuks")

        #extract quantities specified as each = number
        pattern = r"(?i)(\(?each\s*=\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\)?)"
        _compute_regex(pattern, "stuks")

        #extract fixed quantities from the term paar
        pattern = r"(?i)(paar)\b"
        _compute_regex(pattern, "paar", 1)

        #extract quantities specified as PA number pr
        pattern = r"(?i)(PA\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*pr)\b"
        _compute_regex(pattern, "paar")

        #extract quantities followed by paar or par
        pattern = r"(?i)(((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*p(?:aa)?r)\b"
        _compute_regex(pattern, "paar")

        #extract quantities specified after roll
        pattern = r"(?i)(ro?ll?\s*(?:a|van)?\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*(?:st(?:k)?|stuks?|pieces?)?)\b"
        _compute_regex(pattern, "stuks")

        #extract quantities specified after pallet
        pattern = r"(?i)(pallet\s*(?:a|van)?\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*(?:st(?:k)?|stuks?|pieces?)?)\b"
        _compute_regex(pattern, "stuks")

        #extract quantities specified after set
        pattern = r"(?i)(set\s*(?:a|van)?\s*((?:\d{1,3}(?:[.,]\d{3})*|\d+))\s*(?:st(?:k)?|stuks?|pieces?)?)\b"
        _compute_regex(pattern, "stuks")

        return results

    #extract all possible item quantities from the description
    Items = find_number_of_items(text)

    #select the item quantity with the highest value
    verpakkingssoort, productaantallen = pick_max_product(Items)

    return verpakkingssoort, productaantallen

#Regex Volume
def get_volume(text: str):
    """
    Extract the largest volume mentioned in a product description and convert it to mL
    - text = product description to search for volume values and units
    """

    to_ml = {
        "ml": 1,
        "cc": 1,
        "cl": 10,
        "dl": 100,
        "lt": 1000,
        "ul": 0.001
    }

    #define the conversion factors for each volume unit
    patterns = [
        #extract volumes specified in mL, cc, cl, dl, ul, µl, or lt
        r"(\d+(?:[.,]\d*)?)\s?(ml|cc|cl|dl|ul|µl|lt)\b",

        #extract volumes specified in liters
        r"(\d+(?:[.,]\d*)?)\s?(L(?:tr|iter)?|LTR|LITER)\b"
    ]

    matches = []

    #find all volume values and units in the product description
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            value, unit = match
            unit = unit.lower()

            #convert liter units to the standard 'lt' unit
            if unit in ['l', 'ltr', 'liter']:
                unit = 'lt'

            #convert microliter units to the standard 'ul' unit
            elif unit in ['µl', 'μl']:
                unit = 'ul'

            #store the volume value and standardized unit
            matches.append((float(value.replace(',', '.')), unit))

    #return None when no volume is found
    if not matches:
        return None, None

    #select the largest volume found
    max_value, max_unit = max(matches, key=lambda x: x[0])

    #convert the largest volume to mL
    return max_value * to_ml[max_unit], matches

#Regex Size
TO_CM = {
    "cm": 1.0,
    "mm": 0.1,
    "um": 1e-4,
    "m": 100.0
}

def normalize_unit(unit: str):
    """
    Normalize micro symbols and convert units to a standard format
    - unit = length unit to normalize
    """

    return (
        unit.lower()
        .replace("µm", "um")
        .replace("μm", "um")
    )

def get_size(text: str):
    """
    Extract the size mentioned in a product description and convert it to cm, cm², or cm³
    - text = product description to search for size and dimension information
    """

    #extract three-dimensional measurements and calculate the volume in cm³
    pattern_3d = r"(\d+(?:[.,]\d*)?)\s*x\s*(\d+(?:[.,]\d*)?)\s*x\s*(\d+(?:[.,]\d*)?)\s*(mm|cm|µm|μm|um)\b"
    match = re.search(pattern_3d, text, flags=re.IGNORECASE)

    if match:
        d1, d2, d3, unit = match.groups()
        d1, d2, d3 = [float(x.replace(",", ".")) for x in (d1, d2, d3)]
        unit = normalize_unit(unit)
        factor = TO_CM[unit]

        volume_cm3 = (d1 * factor) * (d2 * factor) * (d3 * factor)

        return volume_cm3, "cm³", [d1, d2, d3], [d1 * factor, d2 * factor, d3 * factor]

    #extract two-dimensional measurements and calculate the area in cm²
    pattern_2d = r"(\d+(?:[.,]\d*)?)\s*[x/]\s*(\d+(?:[.,]\d*)?)\s*(mm|cm|µm|μm|um)\b"
    match = re.search(pattern_2d, text, flags=re.IGNORECASE)

    if match:
        d1, d2, unit = match.groups()
        d1, d2 = [float(x.replace(",", ".")) for x in (d1, d2)]
        unit = normalize_unit(unit)
        factor = TO_CM[unit]

        area_cm2 = (d1 * factor) * (d2 * factor)

        return area_cm2, "cm²", [d1, d2], [d1 * factor, d2 * factor]

    #extract roll or strip dimensions with separate units and calculate the area in cm²
    pattern_roll = r"(\d+(?:[.,]\d*)?)\s*(mm|cm|µm|μm|um|m)\s*x\s*(\d+(?:[.,]\d*)?)\s*(mm|cm|µm|μm|um|m)\b"
    match = re.search(pattern_roll, text, flags=re.IGNORECASE)

    if match:
        v1, u1, v2, u2 = match.groups()
        v1, v2 = [float(x.replace(",", ".")) for x in (v1, v2)]
        u1, u2 = normalize_unit(u1), normalize_unit(u2)

        length1_cm = v1 * TO_CM[u1]
        length2_cm = v2 * TO_CM[u2]
        area_cm2 = length1_cm * length2_cm

        return area_cm2, "cm²", [v1, v2], [v1 * TO_CM[u1], v2 * TO_CM[u2]]

    #extract one-dimensional measurements and convert the length to cm
    pattern_1d = r"(\d+(?:[.,]\d*)?)\s?(mm|cm|µm|μm|um)\b"
    match = re.search(pattern_1d, text, flags=re.IGNORECASE)

    if match:
        value, unit = match.groups()
        value = float(value.replace(",", "."))
        unit = normalize_unit(unit)

        length_cm = value * TO_CM[unit]

        return length_cm, "cm", [value], [value * TO_CM[unit]]

    #return None when no size is found
    return None, None, None, None

def get_size_backup(text: str):
    """
    Extract the size mentioned in a product description using the backup size extraction method
    - text = product description to search for size and dimension information
    """

    #extract three-dimensional measurements and calculate the volume in cm³
    pattern_3d = r"(\d+(?:[.,]\d*)?)\s*x\s*(\d+(?:[.,]\d*)?)\s*x\s*(\d+(?:[.,]\d*)?)\s*(mm|cm|µm|μm|um)\b"
    match = re.search(pattern_3d, text, flags=re.IGNORECASE)

    if match:
        d1, d2, d3, unit = match.groups()
        d1, d2, d3 = [float(x.replace(",", ".")) for x in (d1, d2, d3)]
        unit = normalize_unit(unit)
        factor = TO_CM[unit]

        volume_cm3 = (d1 * factor) * (d2 * factor) * (d3 * factor)

        return volume_cm3, "cm³", [d1, d2, d3], [d1 * factor, d2 * factor, d3 * factor]

    #extract two-dimensional measurements and calculate the area in cm²
    pattern_2d = r"(\d+(?:[.,]\d*)?)\s*[x/]\s*(\d+(?:[.,]\d*)?)\s*(mm|cm|µm|μm|um)\b"
    match = re.search(pattern_2d, text, flags=re.IGNORECASE)

    if match:
        d1, d2, unit = match.groups()
        d1, d2 = [float(x.replace(",", ".")) for x in (d1, d2)]
        unit = normalize_unit(unit)
        factor = TO_CM[unit]

        area_cm2 = (d1 * factor) * (d2 * factor)

        return area_cm2, "cm²", [d1, d2], [d1 * factor, d2 * factor]

    #extract roll or strip dimensions with separate units and calculate the area in cm²
    pattern_roll = r"(\d+(?:[.,]\d*)?)\s*(mm|cm|µm|μm|um|m)\s*x\s*(\d+(?:[.,]\d*)?)\s*(mm|cm|µm|μm|um|m)\b"
    match = re.search(pattern_roll, text, flags=re.IGNORECASE)

    if match:
        v1, u1, v2, u2 = match.groups()
        v1, v2 = [float(x.replace(",", ".")) for x in (v1, v2)]
        u1, u2 = normalize_unit(u1), normalize_unit(u2)

        length1_cm = v1 * TO_CM[u1]
        length2_cm = v2 * TO_CM[u2]
        area_cm2 = length1_cm * length2_cm

        return area_cm2, "cm²", [v1, v2], [v1 * TO_CM[u1], v2 * TO_CM[u2]]

    #extract one-dimensional measurements and convert the length to cm
    pattern_1d = r"(\d+(?:[.,]\d*)?)\s?(mm|cm|µm|μm|um)\b"
    match = re.search(pattern_1d, text, flags=re.IGNORECASE)

    if match:
        value, unit = match.groups()
        value = float(value.replace(",", "."))
        unit = normalize_unit(unit)

        length_cm = value * TO_CM[unit]

        return length_cm, "cm", [value], [value * TO_CM[unit]]

    #return None when no size is found
    return None, None, None, None

#Regex Materials:
def extract_materials(text, materialen):
    """
    Extract materials from text and map synonyms to their main material terms
    - text = product description to search for material names and synonyms
    - materialen = dataframe containing main material terms and their synonyms
    """

    #map each synonym to its main material term
    synoniem_map = {}
    for _, row in materialen.iterrows():
        hoofdterm = str(row.iloc[0]).strip().lower()

        for syn in row.dropna().astype(str):
            synoniem = syn.strip().lower()
            synoniem_map[synoniem] = hoofdterm

    #build a regular expression to find all material synonyms
    pattern = r'\b(' + '|'.join(re.escape(s) for s in synoniem_map.keys()) + r')\b'

    #return an empty list when the text is missing
    if pd.isna(text):
        return []

    #find all material synonyms in the text
    matches = re.findall(pattern, text.lower())

    #convert matched synonyms to their main material terms
    hoofdtermen = [synoniem_map[m] for m in matches]

    #keep only unique material terms while preserving their order
    return list(dict.fromkeys(hoofdtermen))

#Regex Sterility:
def flag_regex_words(df, column, df_steriliteit, categorie_col="categorie", artikel_col="artikelnummer_cleaned"):
    """
    Flag products as sterile based on keywords, negations, category settings, and product number propagation
    - df = dataframe containing product information
    - column = column containing the product descriptions to search
    - df_steriliteit = dataframe containing standard sterility settings by category
    - categorie_col = column containing the product category
    - artikel_col = column containing the cleaned product number
    """

    #define keywords indicating sterility
    keywords_steriliteit = ['gammasteriel', 'str', 'gammastr', 'gamma', 'steriel', 'ster', 'sterie', 'steril', 'steri', 'sterile', 'sterilisation']

    #define words indicating that a sterility keyword is negated
    negators = ['n', 'non', 'niet']

    #build a regular expression to find sterility keywords
    keyword_pattern = r'\b(?:' + '|'.join(map(re.escape, keywords_steriliteit)) + r')\b'

    #build a regular expression to find negated sterility keywords
    negated_pattern = (r'\b(?:' + '|'.join(map(re.escape, negators)) + r')\s+(?:' +'|'.join(map(re.escape, keywords_steriliteit)) + r')\b')

    #check which rows contain sterility keywords
    has_keyword = df[column].str.contains(keyword_pattern, case=False, na=False)

    #check which rows contain negated sterility keywords
    has_negation = df[column].str.contains(negated_pattern, case=False, na=False)

    #keep only positive sterility matches and exclude negated matches
    valid_positive = has_keyword & ~has_negation

    #identify valid product numbers for propagation
    valid_artikel = df[artikel_col].astype(str).str.len() > 3

    #create a combined key from product number and category
    key_series = (df[artikel_col].astype(str) + '||' + df[categorie_col].astype(str))

    #store product-category keys with positive sterility matches
    positive_keys = set(key_series[valid_positive & valid_artikel])

    #store product-category keys with negative sterility matches
    negative_keys = set(key_series[has_negation & valid_artikel])

    #propagate positive sterility flags across matching product-category keys
    propagated_positive = key_series.isin(positive_keys)

    #propagate negative sterility flags across matching product-category keys
    propagated_negative = key_series.isin(negative_keys)

    #merge the standard sterility setting for each category
    df = df.merge(
        df_steriliteit[[categorie_col, 'steriliteit']],
        on=categorie_col,
        how='left'
    )

    #correct the standard sterility setting for specific proxy products
    df.loc[
        (df['proxy_product'].str.contains('Deepwell', na=False)) &
        (df['categorie'] == 'Multiwell Plates'),
        'steriliteit'
    ] = False

    df.loc[
        (df['proxy_product'].str.contains('384 wells', na=False)) &
        (df['categorie'] == 'Multiwell Plates'),
        'steriliteit'
    ] = False

    df.loc[
        (df['proxy_product'].str.contains('96 wells', na=False)) &
        (df['categorie'] == 'Multiwell Plates'),
        'steriliteit'
    ] = False

    df.loc[
        (df['proxy_product'].str.contains('Eswab', na=False)) &
        (df['categorie'] == 'Sample Collection Tubes'),
        'steriliteit'
    ] = True

    df.loc[
        (df['proxy_product'].str.contains('Lepelbuis', na=False)) &
        (df['categorie'] == 'Sample Collection Tubes'),
        'steriliteit'
    ] = True

    #fill missing sterility settings with False
    df['steriliteit'] = df['steriliteit'].fillna(False).astype(bool)

    #combine standard settings, direct matches, and propagated positive matches
    df['steriliteit_final'] = (
        df['steriliteit']
        | valid_positive
        | propagated_positive
    )

    #let explicit negative sterility matches override positive matches
    df.loc[
        has_negation | propagated_negative,
        'steriliteit_final'
    ] = False

    return df