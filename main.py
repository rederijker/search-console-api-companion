import streamlit as st
import httplib2
import pandas as pd
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go  # Importa il modulo go da Plotly
import time
from streamlit_extras.metric_cards import style_metric_cards 

st.set_page_config(
    page_title="Search Console API Companion",
    page_icon="🔍",
    layout="wide"
)

# RICORDARSI DI FARE L'AUTENTICAZIONE ENTRO 40 SEC

# Inizializza le variabili di sessione per la gestione dei dati utente
if 'credentials' not in st.session_state:
    st.session_state.credentials = None

if 'selected_site' not in st.session_state:
    st.session_state.selected_site = None

if 'available_sites' not in st.session_state:
    st.session_state.available_sites = []

if 'dimension_filters' not in st.session_state:
    st.session_state.dimension_filters = {}

# Definizione dello scope OAuth per l'autorizzazione
OAUTH_SCOPE = 'https://www.googleapis.com/auth/webmasters.readonly'

# URI di reindirizzamento per l'autenticazione OAuth
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

# Funzione per autorizzare l'app e ottenere le credenziali
def authorize_app(client_id, client_secret, oauth_scope, redirect_uri):
    # Flusso di autorizzazione OAuth
    flow = OAuth2WebServerFlow(client_id=client_id, client_secret=client_secret, scope=oauth_scope, redirect_uri=redirect_uri)

    # Verifica se le credenziali sono già memorizzate nella cache
    if st.session_state.credentials is None:
        # Se non ci sono credenziali memorizzate, richiedi l'autorizzazione all'utente
        authorize_url = flow.step1_get_authorize_url()
        st.write(f"➡️ Go to [this link]({authorize_url}) and autorize app")

        auth_code = st.text_input('Inserisci il tuo Authorization Code qui:')

        if auth_code:
            try:
                # Scambia l'Authorization Code per le credenziali
                credentials = flow.step2_exchange(auth_code)

                # Memorizza le credenziali nella sessione
                st.session_state.credentials = credentials
            except Exception as e:
                st.write(f"Errore durante l'autorizzazione: {e}")

    return st.session_state.credentials

# Pagina iniziale
st.title('🔍Search Console API Companion')
st.text("by Cristiano Caggiula")
st.write(
    "Welcome to **Search Console API Companion**! Explore and analyze Google Search Console data with ease. Authenticate effortlessly, choose your website, and access features like URL inspection and search analytics. Customize your searches and enjoy unlimited rows of data, without the need for programming skills. Unleash the full potential of your website's visibility with this user-friendly tool, perfect for webmasters, SEO experts, and digital marketers."
)


# Inserimento delle credenziali Google Cloud Project
st.subheader('Insert Google Cloud Project Credential:')
st.write("➡️ Google Cloud Console: https://console.cloud.google.com/apis/credentials")
with st.expander("How to Get credential?"):
    st.text("")

col1, col2 = st.columns(2)
with col1:
    CLIENT_ID = st.text_input('Client ID', type='password')
with col2:
    CLIENT_SECRET = st.text_input('Client Secret', type='password')

# Utilizza la session state per mantenere i dati utente
if CLIENT_ID and CLIENT_SECRET:
    # Autorizza l'app e ottieni le credenziali
    credentials = authorize_app(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, REDIRECT_URI)

    if credentials:
        # Crea un oggetto http autorizzato
        http = credentials.authorize(httplib2.Http())

        # Crea il servizio Google Search Console
        webmasters_service = build('searchconsole', 'v1', http=http)

        # Ottieni la lista dei siti disponibili solo se non è già stata memorizzata nella sessione
        if not st.session_state.available_sites:
            site_list = webmasters_service.sites().list().execute()
            st.session_state.available_sites = [site['siteUrl'] for site in site_list.get('siteEntry', [])]

        # Seleziona un sito dalla lista
        st.session_state.selected_site = st.selectbox('Seleziona un sito web:', st.session_state.available_sites)

        # Crea due tab per la selezione delle funzionalità
        
        tab1, tab2 = st.tabs(["URL INSPECTION", "SEARCH ANALYTICS"])

        with tab1:
            # Inserisci l'URL da ispezionare
            url_to_inspect = st.text_input("Insert URL to inspect:")

            # Esegui l'ispezione dell'URL
            if st.button('Ispeziona URL'):
                if st.session_state.selected_site is not None:
                    request_body = {
                        'inspectionUrl': url_to_inspect,
                        'siteUrl': st.session_state.selected_site
                    }
                    response = webmasters_service.urlInspection().index().inspect(body=request_body).execute()
                    st.write(f'Risultato dell\'ispezione: {response}')

        with tab2:
            # Ottieni dati dalla Search Console
            col1, col2, col3 = st.columns(3)
            with col1:
                # Opzioni per il tipo di dati nell'API
                options_type = {
                    'Web': 'web',
                    'News': 'news',
                    'Discovery': 'discovery',
                    'Image': 'image',
                    'Video': 'video'
                }
              
                selected_type = st.selectbox('CHANNEL', list(options_type.keys()))
                with st.container():                   
                         start_date = st.date_input('Start date', pd.to_datetime('2023-01-01'))                   
                         end_date = st.date_input('End date', pd.to_datetime('2023-10-28'))
               
                
            with col2:
                # Aggiungi una selectbox per le dimensioni
                selected_dimensions = st.multiselect('DIMENSIONS', ['Date', 'Page', 'Query', 'Device', 'Country'], default=['Query', 'Page'] )
                with st.expander(f"Filters for Dimensions"):
                 unique_key = 0
                 for dimension in selected_dimensions:                    
                    col1, col2 =st.columns(2)
                    with col1:
                        operator = st.selectbox(f' {dimension}', ['equals', 'contains', 'notEquals', 'notContains', 'includingRegex', 'excludingRegex'])
                    with col2:
                        filter_value = st.text_input(label="", placeholder=" value", key=unique_key)
                    unique_key += 1
                    st.session_state.dimension_filters[dimension] = {'operator': operator, 'filter_value': filter_value}
                    
                    

       
            with col3:
                with st.container():
                    col1, col2 = st.columns(2)
                    with col1:
                         aggregation_type = ['No', 'Auto', 'by Page']
                         check_box_aggregation = st.radio('AGGREGATION TYPE', aggregation_type)

                    with col2:                                       
               
                        row_limit_options = ['No', 'Yes']
                        check_box_row = st.radio('SET ROW LIMIT?', row_limit_options)
                        if check_box_row == 'Yes':
                            row_limit = st.number_input('Row limit', min_value=1, max_value=25000, value=25000)
                        else:
                            row_limit = None  # Nessun limite
                
                
        
            # Aggiungi un bottone per ottenere i dati in batch
            if st.button('GET DATA'):
                if st.session_state.selected_site is not None:
                    start_row = 0  # Inizia dalla prima riga
                    data_list = []  # Inizializza una lista per i dati
                    
            
                    # Costruisci il parametro "dimensions" in base alle selezioni dell'utente
                    dimensions = []
                    if 'Date' in selected_dimensions:
                        dimensions.append('DATE')
                    if 'Query' in selected_dimensions:
                        dimensions.append('QUERY')
                    if 'Page' in selected_dimensions:
                        dimensions.append('PAGE')
                    if 'Device' in selected_dimensions:
                        dimensions.append('DEVICE')
                    if 'Country' in selected_dimensions:
                        dimensions.append('COUNTRY')

                    
                    with st.spinner("Downloading data..."):
                                 
                        while True:                     
                            
                            request_body = {
                                "startDate": start_date.strftime('%Y-%m-%d'),
                                "endDate": end_date.strftime('%Y-%m-%d'),
                                "dimensions": dimensions,  # Utilizza le dimensioni selezionate dall'utente
                                "startRow": start_row,
                                "dataState": "final",
                                "type": selected_type,
                            }
                            for dimension in selected_dimensions:
                                if dimension in st.session_state.dimension_filters:
                                    filter_operator = st.session_state.dimension_filters[dimension]['operator']
                                    filter_value = st.session_state.dimension_filters[dimension]['filter_value']
                                    if filter_value:
                                        if 'dimensionFilterGroups' not in request_body:
                                            request_body['dimensionFilterGroups'] = []
                                        request_body['dimensionFilterGroups'].append({
                                            'filters': [{
                                                'dimension': dimension,
                                                'expression': filter_value,
                                                'operator': filter_operator
                                            }]
                                        })
                
                            if row_limit is not None:
                                request_body["rowLimit"] = min(row_limit, 25000)  # Imposta il limite massimo a 25.000
                            else:
                                request_body["rowLimit"] = 25000  # Imposta un limite predefinito a 25.000
                
                            if check_box_aggregation == 'by Page':
                                request_body["aggregationType"] = "byPage"
                            elif check_box_aggregation == 'Auto':
                                request_body["aggregationType"] = "auto"
                
                            response_data = webmasters_service.searchanalytics().query(siteUrl=st.session_state.selected_site, body=request_body).execute()
                
                            for row in response_data.get('rows', []):
                                data_entry = {}  # Crea un dizionario vuoto per i dati di questa riga
                                if 'Date' in selected_dimensions:
                                    data_entry['Date'] = row['keys'][dimensions.index('DATE')]
                                if 'Query' in selected_dimensions:
                                    data_entry['Query'] = row['keys'][dimensions.index('QUERY')]
                                if 'Page' in selected_dimensions:
                                    data_entry['Page'] = row['keys'][dimensions.index('PAGE')]
                                if 'Device' in selected_dimensions:
                                    data_entry['Device'] = row['keys'][dimensions.index('DEVICE')]
                                if 'Country' in selected_dimensions:
                                    data_entry['Country'] = row['keys'][dimensions.index('COUNTRY')]
                                data_entry['Clicks'] = row['clicks']
                                data_entry['Impressions'] = row['impressions']
                                data_entry['CTR'] = row['ctr']
                                data_entry['Position'] = row['position']
                                data_list.append(data_entry)
                            
                            
                            if len(response_data.get('rows', [])) < 25000 and (row_limit is None or start_row + len(response_data.get('rows', [])) >= row_limit):
                                # Se abbiamo meno di 25.000 righe o abbiamo superato il limite specificato, abbiamo ottenuto tutti i dati
                                break
                            else:
                                # Altrimenti, incrementa il valore di startRow per la prossima richiesta
                                start_row += 25000
                                

                    # Alla fine del processo, mostra un messaggio di completamento
                    
                    st.subheader("Your data")
                    df = pd.DataFrame(data_list)
                    average_position = df['Position'].mean()
                    formatted_average_m= "{:.2f}".format(average_position)

                    total_clicks_m = df['Clicks'].sum()
                    average_ctr_m = df['CTR'].mean()
                    average_ctr_perc= average_ctr_m * 100
                    formatted_ctr_m = "{:.2f}%".format(average_ctr_perc)
                    total_impressions_m = df['Impressions'].sum()
                    col1, col2, col3, col4, col5 = st.columns(5)

                    with col1:
                        st.text("")

                    with col2:
                        st.metric(label="Total Clicks", value=total_clicks_m)
                        st.text("")
                    with col3:
                        st.metric(label="Total Impressions", value=total_impressions_m)         
                    with col4:
                        st.metric(label="Average Position", value=formatted_average_m)
                    with col5:
                        st.metric(label="Average CTR", value=formatted_ctr_m)
                        
                 
                    st.dataframe(df, width=2000)
            
                    st.subheader("QUERIES ANALYSIS")
            


                    tab1, tab2 = st.tabs(["QUERY INSIGHT", "TRAFFIC REPORT"])
                    with tab1:
        
                        
                        # Crea il DataFrame con i dati delle query
                        # ...
                        
                        # Estrai le colonne rilevanti dal DataFrame
    
                        # Calcola la media per la posizione media e il CTR
                        df = pd.DataFrame(data_list)
                         # Valore minimo
                        # Calcola i valori minimi e massimi per gli assi
                        min_ctr = df['CTR'].min()
                        max_ctr = df['CTR'].max()
                        min_position = df['Position'].min()
                        max_position = df['Position'].max()
                        
                        # Crea il grafico a bolle con Plotly
                        fig = px.scatter(df, x='CTR', y='Position', size='Clicks', hover_data=['Query'], log_y=True, log_x=True,)
                        fig.update_yaxes(autorange="reversed")
                        fig.update_xaxes(type="log", tickvals=[min_ctr, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1], ticktext=[str(min_ctr), "0.2", "0.3", "0.42", "0.5", "0.6", "0.7", "0.8", "0.9", "1"])
                        fig.update_yaxes(type="log", tickvals=[min_position, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100], ticktext=[str(min_position), "10", "20", "30", "40", "50", "60", "70", "80", "90", "100"])
                        
                        # Aggiungi linee di riferimento per la media di CTR e posizione
                        fig.add_shape(type='line', x0=df['CTR'].mean(), x1=df['CTR'].mean(), y0=min_position, y1=max_position, line=dict(color='red', dash='dash'))
                        fig.add_shape(type='line', x0=min_ctr, x1=max_ctr, y0=df['Position'].mean(), y1=df['Position'].mean(), line=dict(color='red', dash='dash'))

                                    
                        # Mostra il grafico interattivo
                        with st.container():
                            st.plotly_chart(fig, use_container_width=True)
                      
                        average_position = df['Position'].mean()
                        average_ctr = df['CTR'].mean()
                        #suddividere i dati in quattro DataFrame in base ai quadranti specificati e fornire all'utente la lista delle query in ciascun quadrante
                        upper_high_ctr = df[(df['Position'] <= average_position) & (df['CTR'] > average_ctr)]
                        lower_high_ctr = df[(df['Position'] > average_position) & (df['CTR'] > average_ctr)]
                        lower_low_ctr = df[(df['Position'] > average_position) & (df['CTR'] <= average_ctr)]
                        upper_low_ctr = df[(df['Position'] <= average_position) & (df['CTR'] <= average_ctr)]
                        try:
                            df_upper_high_ctr = upper_high_ctr[['Query', 'Page', 'Impressions', 'Clicks', 'CTR', 'Position']]
                            #Per ciascun quadrante, creare un DataFrame separato
                            df_lower_high_ctr = lower_high_ctr[['Query', 'Page', 'Impressions', 'Clicks', 'CTR', 'Position']]
                            df_lower_low_ctr = lower_low_ctr[['Query', 'Page', 'Impressions', 'Clicks', 'CTR', 'Position']]
                            df_upper_low_ctr = upper_low_ctr[['Query', 'Page', 'Impressions', 'Clicks', 'CTR', 'Position']]
                            #mostrare df
                     


                            with st.expander("Top position and high CTR Queries"):           
                                st.write("For these queries, there's not much you need to do; you're already doing a great job.")
                                st.write(df_upper_high_ctr)
                            with st.expander("Low position and high CTR Queries"):
                                st.write("""
                                Those queries appear to be highly relevant to users. They achieve a high click-through rate (CTR) even when they rank lower than the average query on your website. If the average position of these queries improves, it could significantly impact your website's performance. It's advisable to focus on enhancing the SEO for these queries. For instance, consider a prominent query in quadrant 2 for a gardening website, such as "how to build a wooden shed." Check if you already have a dedicated page for this topic and proceed in two ways:
    
                                -If you don't have a dedicated page, think about creating one to consolidate all the information on your website related to this subject.
    
                                -If you already have a page, contemplate adding more content to better address the needs of users searching for this query.
                                """)
                                st.write(df_lower_high_ctr)
                            with st.expander("Low position and low CTR Queries"):
                                st.write("""
                                When looking at queries with low CTR (both with low and top position), it's especially interesting to look at the bubble sizes to understand which queries have a low CTR but are still driving significant traffic. While the queries in this quadrant might seem unworthy of your effort, they can be divided into two main groups:
                                
                                **Related queries**: If the query in question is important to you, it's a good start to have it appearing in Search already. Prioritize these queries over queries that are not appearing in Search results at all, as they'll be easier to optimize.
                                
                                **Unrelated queries**: If your site doesn't cover content related to this query, maybe it's a good opportunity to fine tune your content or focus on queries that will bring relevant traffic.
                                """)
                                st.write(df_lower_low_ctr)
                            with st.expander("Top position and low CTR Queries"):
                                st.write("""
                                These queries might have a low click-through rate (CTR) for various reasons. Check the largest bubbles to find signs of the following:
    
                                Your competitors may be using structured data markup and appearing with rich results, attracting users to click on their results instead of yours. Consider optimizing for the most common visual elements in Google Search.
    
                                You may have optimized, or be "accidentally" ranking for a query that users are not interested in relation to your site. This might not be an issue for you, in which case you can ignore those queries. If you prefer people not to find you through those queries (for example, they contain offensive words), try to fine-tune your content to remove mentions that could be seen as synonyms or related queries to the one bringing traffic.
    
                                People may have already found the information they needed, for example, your company's opening hours, address, or phone number. Check the queries that were used and the URLs that contained the information. If one of your website goals is to drive people to your stores, this is working as intended; if you believe that people should visit your website for extra information, you could try to optimize your titles and descriptions to make that clear. See the next section for more details.
                                """)
                                st.write(df_upper_low_ctr)
                        except KeyError as e:
                            st.warning("To obtain insights on both queries and pages, consider adding 'Page' to the dimensions in your analysis.")

                    with tab2:
                        st.text("")
