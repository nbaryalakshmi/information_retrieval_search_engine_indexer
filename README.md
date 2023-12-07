# information_retrieval_search_engine_indexer
Information retrieval, Search Engine, Crawler, Indexer

Crawler
-------
The crawler developed in this project crawls all research links listed in the Research Centre for Computational Science and Mathematical Modelling (CSM) at Coventry University. The link for the same is https://pureportal.coventry.ac.uk/en/organisations/research-centre-for-computational-science-and-mathematical-modell/publications/. There are five pages in the site, in which all are crawled. The research links which are not related to CSM are skipped. Some research links which has no abstract provided are also skipped. The  information collected from the scraped publications are year of publication, research link, abstract, title, author names, author profile link and research document links. After each page is scraped, five seconds delay is provided for the next scrape because the site has mentioned crawl-delay:5 in its robots.txt document. After scraping all relevant pages, the information collected are saved as an excel file. The crawler is scheduled to run weekly  on every thursday at 08.40 pm. 

Indexer
---------------------------------
After scraping all relevant pages, the information collected are saved as an excel file. Then inverted index is created from the scraped results ‘abstract’ field. For the inverted index, the abstract for each document is cleaned using nltk text pre-processing steps, such as stop-word removal, stemming etc. Then a list of unique words from all abstract text is created. Then a dictionary is created where keys are the unique words and values are the document ids which contain the unique words. Then the document ids are sorted in ascending order. The final inverted index dictionary is saved as a json file. When a user inputs a query, the query is pre-processed using nltk preprocessing tasks and and the document ids which contain the user query words are found from the inverted index.
 
Query processor
------------------------------------
The frontend for search engine is developed using Dash-python. User enters a search query. Search query is pre-processed with nltk pre-processing libraries. After the documents containing the keywords are found from the inverted index, tf.idf is implemented to find the ranking of the documents and ranked documents with its details and clickable links are displayed on the frontend based on the ranks.

![image](https://github.com/nbaryalakshmi/information_retrieval_search_engine_indexer/assets/127498506/e449ae4e-125a-479d-8b5f-4dba516aeb4c)

The above screenshot is the output for user search query “Data science and computational intelligence” and it displays all relevant documents.
