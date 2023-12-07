import pandas as pd
import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import json
nltk.download("stopwords")
nltk.download("punkt")
stopwords = stopwords.words('english')
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input,Output,State
def get_scrape_results():
    return pd.read_excel("scraped_results.xlsx")
def get_inverted_index():
    with open('doc_inverted_index.json') as f:
        invertedindex = json.load(f)
    return invertedindex
def clean_text(text):
    port_stemmer = PorterStemmer()
    lst_tokens = word_tokenize(text)
    text_cleaned = ""
    for word in lst_tokens:
        if word not in stopwords:
            text_cleaned += port_stemmer.stem(word) + " "
    return text_cleaned
def get_document_ids(dct_inverted_index,text_cleaned):    
    lst_docs=[]
    dct_inverted_index_filtered={}
    for wrd in text_cleaned.split():
        if wrd in dct_inverted_index:
            dct_inverted_index_filtered[wrd]=dct_inverted_index[wrd]
    print("Filtered Inverted index:\n")
    print(dct_inverted_index_filtered)
    for wrd,docs in dct_inverted_index_filtered.items():
        for doc in docs:
            if doc not in lst_docs:
                lst_docs.append(doc)      
    print("List of documents which have any of the words from user's search query:\n")
    print(lst_docs)
    return dct_inverted_index_filtered,lst_docs
def get_term_frequency(dct_inverted_index_filtered,df_results):
    dct_word_count={}
    for k,docs in dct_inverted_index_filtered.items():
        for docid in docs:
            abstract=df_results.loc[docid]['abstract']
            abstract=clean_text(abstract)
            if k in abstract:
                count=abstract.count(k)
                if k in dct_word_count:
                    if docid in dct_word_count[k]:
                        dct_word_count[k][docid]+=count
                    else:
                        dct_word_count[k][docid]=count
                else:
                    dct_word_count[k]={}
                    dct_word_count[k][docid]=count  
    return dct_word_count
def get_idf(dct_inverted_index_filtered,total_num_of_docs):
    dct_idf={}
    for k,docs in dct_inverted_index_filtered.items():
        docswithterm=len(docs)
        dct_idf[k]=np.log10(total_num_of_docs/docswithterm)
    return dct_idf
def get_tfidf(dct_inverted_index_filtered,dct_word_count,dct_idf):
    dct_tf_idf={}
    for k,docs in dct_inverted_index_filtered.items():
        for docid in docs:
            if k in dct_tf_idf:
                dct_tf_idf[k][docid]=dct_word_count[k][docid]*dct_idf[k]
            else:
                dct_tf_idf[k]={}   
                dct_tf_idf[k][docid]=dct_word_count[k][docid]*dct_idf[k]
    return dct_tf_idf
def relevance_score(row,text_cleaned,tf_idf):
    relevance=0
    for word in text_cleaned.split(): 
        if row.name in tf_idf[word]:
            relevance+=tf_idf[word][row.name]
    return relevance
def get_doc_relevance_score(df_results,lst_docs,text_cleaned,dct_tf_idf):
    df_results=df_results.iloc[lst_docs]
    df_results=df_results.reset_index(drop=True)
    df_results['relevance_score']=df_results.apply(relevance_score,text_cleaned=text_cleaned,tf_idf=dct_tf_idf,axis=1)
    return df_results
def get_search_results(query):
    try:
        #read scrape results
        df_results=get_scrape_results()
        #read inverted index
        dct_inverted_index=get_inverted_index() 
        #clean user query
        text_cleaned=clean_text(query)
        #get ids of documents where their abstract contains any word from user query 
        dct_inverted_index_filtered,lst_docs=get_document_ids(dct_inverted_index,text_cleaned)  
        #get term frequency for tf.idf
        dct_word_count=get_term_frequency(dct_inverted_index_filtered,df_results)
        #get idf for tf.idf
        total_num_of_docs=len(lst_docs)
        dct_idf=get_idf(dct_inverted_index_filtered,total_num_of_docs)
        #get tf.idf=tf*idf
        dct_tf_idf=get_tfidf(dct_inverted_index_filtered,dct_word_count,dct_idf)
        print("tf.idf results")
        print(dct_tf_idf)
        #get document relevance score
        df_results=get_doc_relevance_score(df_results,lst_docs,text_cleaned,dct_tf_idf)
        #arrange records in order of relevance, descending order
        df_results=df_results.sort_values(['relevance_score'], ascending=False)
        df_results=df_results.reset_index(drop=True)
        return df_results.to_dict('records')
    except:
        return []
app = dash.Dash(__name__,meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}],
                suppress_callback_exceptions=True)
#Define the layout of the app
app.layout = dbc.Container(
    children=[
        html.Div([dbc.Label('Please enter your search query.')],className="col-12"),
        html.Div([dbc.Input(id='input_text', type='text', value='')],className="col-12"),
        html.Div(" "),
         html.Div(
    [
        dbc.Button('Search', id='btn_search',outline=True, color="success",size="lg",)
    ],
    className="col-12 mx-auto",
                    ),
        dbc.ListGroup(id='ul_results',
    flush=True,
    
)
        
    ]
)
#Get result set
@app.callback(
    dash.dependencies.Output('ul_results', 'children'),
    [Input('btn_search', 'n_clicks')],
    [State('input_text', 'value'),
     State('ul_results', 'children')]
)
def get_result_set(n_clicks, input_text, current_list):
    if current_list==None:
        current_list=[]
    if n_clicks is None:
        return current_list
    else:
        if input_text.strip()=="":
            return ["Please enter your search query."]
        else:
            current_list=[]
            dct_results=get_search_results(input_text)
            for records in dct_results:
                current_list.append(dbc.ListGroupItem(" "))
                current_list.append(dbc.ListGroupItem("Publication Year: "+str(records["year"])))
                current_list.append(dbc.ListGroupItem("Title: "+records["title"]))
                current_list.append(dbc.ListGroupItem("Research Link: "+records["linkResearch"],href=records["linkResearch"]))
                current_list.append(dbc.ListGroupItem("Authors: "+records["authors"]))
                lst_profile=eval(records["profile"])
                for prf in lst_profile:
                    current_list.append(dbc.ListGroupItem("Author Profile: "+prf,href=prf))
                current_list.append(dbc.ListGroupItem("Document Link: "+records["documentLink"],href=records["documentLink"]))
            return current_list 
if __name__ == '__main__':
    app.run_server(debug=True)