import requests
from bs4 import BeautifulSoup
import time
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import pandas as pd
import json
import schedule
nltk.download("stopwords")
nltk.download("punkt")
stopwords = stopwords.words('english')
def clean_text(text):
    port_stemmer = PorterStemmer()
    lst_tokens = word_tokenize(text)
    text_cleaned = ""
    for word in lst_tokens:
        if word not in stopwords:
            text_cleaned += port_stemmer.stem(word) + " "
    return text_cleaned
def get_year(li):
    year=li.find('div',{'class':'search-result-group'})    
    return year
def get_researchlink(li):
    res_link=li.find('a', {'rel':'ContributionToBookAnthology'})
    if res_link==None:
        res_link=li.find('a', {'rel':'ContributionToJournal'}) 
    if res_link==None:
        res_link=li.find('a', {'rel':'ContributionToConference'}) 
    if res_link==None:
        res_link=li.find('a', {'rel':'BookAnthology'}) 
    if res_link==None:
        res_link=li.find('a', {'rel':'Thesis'}) 
    if res_link==None:
        res_link=li.find('a', {'rel':'OtherContribution'}) 
    return res_link
def csm_research_or_not(soup):
    is_csm_research=False
    research_org=soup.find('ul', {'class': 'relations organisations'})
    for elem in research_org.find_all('li'):
        if elem.text=="Research Centre for Computational Science and Mathematical Modelling":
            is_csm_research=True
            break
    return is_csm_research
def get_abstract(soup):
    return soup.find('div',{'class':'textblock'})
def get_authors_title(soup):
    elem_intro=soup.find('div', {'class': 'introduction'})
    authors=elem_intro.find('p', {'class':'relations persons'})
    title=elem_intro.find('h1').text 
    return title,authors
def get_profiles(authors):
    lst_profiles=[]
    for authr in authors.find_all('a'):
        lst_profiles.append(authr['href'])
    return lst_profiles
def get_doc_link(soup):
    doc=soup.find('div',{'class':'doi'})
    if doc==None:
        return 'None'
    else:
        doc=doc.find('a')
        return doc['href'] 
def create_inverted_index(df_scraped):    
    #get unique list of words 
    lst_words=[]
    df_scraped['abstract_cleaned']=df_scraped['abstract'].apply(clean_text)
    for indx,res in df_scraped.iterrows():
        abstract=res['abstract_cleaned']
        for word in abstract.split():
            if word not in lst_words:
                lst_words.append(word)
    #create inverted index
    dct_inverted_index={}
    for wrd in lst_words:
        for indx,res in df_scraped.iterrows():
            abstract=res['abstract_cleaned']
            if wrd in abstract:
                if wrd in dct_inverted_index:
                    dct_inverted_index[wrd].append(indx)#add index as document id
                else:
                    dct_inverted_index[wrd]=[indx]#add index as document id
    return dct_inverted_index
#if __name__ == '__main__':
def do_crawl():
    pages=5
    num=0
    lst_results=[]
    while num<pages:
        if num==0:
            site="https://pureportal.coventry.ac.uk/en/organisations/research-centre-for-computational-science-and-mathematical-modell/publications/"
        else:            
            site="https://pureportal.coventry.ac.uk/en/organisations/research-centre-for-computational-science-and-mathematical-modell/publications/?page="+str(num)
        print("Fetching url: " + site)
        pagesource = requests.get(site)
        soup = BeautifulSoup(pagesource.text, "html.parser")
        #get all research links
        ul=soup.find('ul', {'class': 'list-results'})
        for li in ul.find_all('li',{'class':'list-result-item'}):
            dct_results={}
            #get year
            year=get_year(li)
            if year!=None:
                pubyear=year.text.strip()
            dct_results['year']=pubyear
            research_link=get_researchlink(li)
            if research_link==None:
                other_links=li.find('a')
                print("Links not scraped:",other_links)
                continue
            dct_results['linkResearch']=research_link['href']            
            #sleep for 5 seconds
            time.sleep(5)
            pagesource = requests.get(dct_results['linkResearch'])
            soup = BeautifulSoup(pagesource.text, "html.parser")  
            #scrape only research links related to CSM
            is_csm_research=csm_research_or_not(soup)
            if is_csm_research==True:
                abstract=get_abstract(soup)                
                if abstract==None:#skip papers with no abstract
                    continue
                dct_results['abstract']=abstract.text                 
                #get title,authors
                title,authors=get_authors_title(soup)
                dct_results['title']=title
                dct_results['authors']=authors.text
                #author profile                
                dct_results['profile']=get_profiles(authors)
                #link to document page
                dct_results['documentLink']=get_doc_link(soup)            
                lst_results.append(dct_results)
        #sleep for 5 seconds
        time.sleep(5)
        num+=1
    #save all scraped results to an excel file 
    df_scraped=pd.DataFrame(lst_results)
    df_scraped.to_excel("scraped_results.xlsx")       
    df_scraped.head()
    ############################### inverted index ##########################
    dct_inverted_index=create_inverted_index(df_scraped)
    #arrange docids in ascending order
    dct_inverted_index_sorted={}
    for word,docids in dct_inverted_index.items():
        dct_inverted_index_sorted[word]=sorted(docids)
    #save inverted index 
    with open('doc_inverted_index.json', 'w') as f:
        json.dump(dct_inverted_index_sorted, f)
    #Number of staff whose publications are crawled (approximately) 
    lst_staff=[]
    for indx,res in df_scraped.iterrows():
        auth=res["authors"].split(',')
        for athr in auth:
            if athr.strip() not in lst_staff:
                lst_staff.append(athr.strip())
    print("Number of staff whose publications are crawled:")
    print(len(lst_staff))
    print("List of all authors who contributed to the publications:")
    print(lst_staff)
    #and the maximum number of publications per staff
    dct_num_pub={}
    for indx,res in df_scraped.iterrows():
        auth=res["authors"].split(',')
        for athr in auth:
            if athr.strip() in dct_num_pub:
                dct_num_pub[athr.strip()]+=1
            else:
                dct_num_pub[athr.strip()]=1
    dct_num_pub = sorted(dct_num_pub.items(), key=lambda kv: kv[1],reverse=True)
    print("Number of publications per staff:")
    for auth in dct_num_pub:
        print(auth)
    #preprocessed words in inverted index
    print(dct_inverted_index_sorted.keys())

schedule.every().thursday.at("20:40").do(do_crawl)
while True:
    schedule.run_pending()
    time.sleep(1)



