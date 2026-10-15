import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
#os.environ["HF_HUB_OFFLINE"] = "1" #For local loading of the sentence transformers model
#os.environ["TRANSFORMERS_OFFLINE"] = "1" #For local loading of the sentence transformers model
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from keras.models import load_model
import pickle

def preprocess_artikelomschrijving(df: pd.DataFrame, omschrijving_col: str, stopwords: set) -> pd.DataFrame:
    """
    preprocess the 'artikelomschrijving' to be suitable for vectorization
    - df = dataframe which contains the 'artikelomschrijving'
    - omschrijving_col = column in df which contains the 'artikelomschrijving'
    - stopwords = list of words which are the most frequently occuring words in 'artikelomschrijving' without semantic meaning, 
      these are removed to help the neural network focus on important keywords and reduce noise
    """
    df = df.copy()

    df['omschrijving_preprocessed'] = df[omschrijving_col] #create a preprocessed copy of the description column
    df['omschrijving_preprocessed'] = df['omschrijving_preprocessed'].apply( lambda x: x.lower() if isinstance(x, str) else x) #convert text to lowercase
    df['omschrijving_preprocessed'] = df['omschrijving_preprocessed'].replace(to_replace=r'[^\w\s]', value=' ', regex=True) #replace punctuation and special characters with spaces
    df['omschrijving_preprocessed'] = df['omschrijving_preprocessed'].replace(to_replace=r'\d', value=' ', regex=True) #remove numbers

    #remove stopwords from the text
    df['omschrijving_preprocessed'] = df['omschrijving_preprocessed'].apply(
        lambda x: ' '.join([
            word for word in x.split()
            if word.lower() not in stopwords
        ]) if isinstance(x, str) else x
    )

    return df

#stopwoorden:
stopwords = {
    'ml', 'x', 'mm', 'st', 'ea', 'ul', 's', 'ps', 'pp', 'w', 'm', 'pk',
    'ds', 'r', 'cm', 'eh', 'p', 'l', 'f', 'each', 'met', 'of', 'voor',
    'u', 'v', 'en', 'um', 'd', 'b', 'for', 'nr', 'with', 'i', 'a'
}

def encode_sentence_transformer(df, text_column='omschrijving_preprocessed', column_name='emb_st', model_name='all-MiniLM-L6-v2'):
    """
    Apply Sentence Transformer to article description
    - df = dataframe
    - text_column = name of column with preprocessed article description
    - column_name = name of (to be created) column for vectorizations
    - model_name = type of sentence embedding model
    """
    model = SentenceTransformer(model_name) #load the sentence transformer model
    #model = SentenceTransformer('C:/Add/filepath/here!', local_files_only = True) # #For local loading of the sentence transformers model, TODO: add the file path to Sentence Transformer model
    df = df[(df[text_column].notna()) & (df[text_column].str.strip() != '')].copy() #keep only rows with a non-empty text value
    embeddings = model.encode(df[text_column].tolist(), convert_to_numpy=True) #convert the text values into numerical embeddings
    df[column_name] = list(embeddings) #store each embedding in the dataframe
    X = np.vstack(df[column_name]) #combine the embeddings into a single numpy array

    return df, X

def is_valid_embedding(x):
    """
    Opschonen van embeddings
    - x = embedding
    """
    return isinstance(x, np.ndarray) and x.size > 0 and not np.isnan(x).any()

def predict_category(df, embedding_column, keras_model, label_encoder_link, threshold):
    """
    Predict the category of rows not found in the database using embeddings
    - df = dataframe containing the products to categorize
    - embedding_column = column containing the text embeddings
    - keras_model = trained model used for category prediction
    - label_encoder_link = path to the saved label encoder
    - threshold = minimum confidence required for a category prediction
    """

    #split data into rows found in the database and rows that need prediction
    database_df = df[df['found_in_database'] == True]
    no_database_df = df[df['found_in_database'] != True]

    #identify rows with valid embeddings and valid descriptions
    valid_embedding_mask = no_database_df['emb_st'].apply(is_valid_embedding)

    omschrijving_invalid_mask = (
        no_database_df['omschrijving_preprocessed'].isna() |
        (no_database_df['omschrijving_preprocessed'].str.strip() == "") |
        (no_database_df['omschrijving_preprocessed'].str.lower().str.strip() == "waarde onbekend")
    )

    #separate rows that can and cannot be used for prediction
    invalid_df = no_database_df[~valid_embedding_mask | omschrijving_invalid_mask].copy()
    new_df = no_database_df[valid_embedding_mask & ~omschrijving_invalid_mask].copy()

    #convert embeddings to a numpy array and predict category probabilities
    X_new = np.vstack(new_df[embedding_column])
    y_probs_new = keras_model.predict(X_new)

    #select the category with the highest predicted probability
    y_pred_new = np.argmax(y_probs_new, axis=1)

    #load the label encoder and convert predicted indices back to category names
    with open(label_encoder_link, 'rb') as f:
        label_encoder = pickle.load(f)

    predicted_labels_new = label_encoder.inverse_transform(y_pred_new)

    #get the confidence score for the predicted category
    predicted_confidences_new = y_probs_new[
        np.arange(len(y_probs_new)),
        y_pred_new
    ]

    new_df['predicted_label'] = predicted_labels_new
    new_df['predicted_confidence'] = predicted_confidences_new

    #replace low-confidence predictions with 'Other'
    new_df['categorie'] = new_df['predicted_label']
    new_df.loc[
        new_df['predicted_confidence'] < threshold,
        'categorie'
    ] = 'Other'

    #include all valid predictions by default
    new_df['is_included'] = True

    #exclude categories that should not be included in further analysis
    exclude_categories = ['Mechanical Pipettes','Cryo Boxes','Racks','Sample Bags','Emmers','Wash Bottles','Gloves (Reusable)','Scissors',
        'Storage Boxes','Slide Boxes','Needle Containers','Transport Boxes','Naaldelektrode','Weighing Scale','Biopsy Bags','Cryo Bags',
        'Face Protectors','Funnels (Disposable)','Funnels (Reusable)','Other','Reagent Reservoirs (Reusable)','Reusabele Cell Counting Slides',
        'Wrist Seals','Biopsy Needles']
    new_df.loc[new_df['categorie'].isin(exclude_categories), 'is_included'] = False

    #rows without valid predictions are classified as 'Other' and excluded
    invalid_df['categorie'] = 'Other'
    invalid_df['is_included'] = False

    #combine database rows, predicted rows, and invalid rows
    merged_df = pd.concat([database_df, new_df, invalid_df],ignore_index=True,sort=False)

    return merged_df