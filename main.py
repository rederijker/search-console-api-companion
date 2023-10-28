import streamlit as st
import httplib2
import pandas as pd
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
import numpy as np

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
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            with col1:
                start_date = st.date_input('Start date', pd.to_datetime('2023-01-01'))
            with col2:
                end_date = st.date_input('End date', pd.to_datetime('2023-10-28'))
            with col3:
                # Opzioni per il tipo di dati nell'API
                options_type = {
                    'Web': 'web',
                    'News': 'news',
                    'Discovery': 'discovery',
                    'Image': 'image',
                    'Video': 'video'
                }
                selected_type = st.selectbox('Choose channel:', list(options_type.keys()))
            with col4:
                # Aggiungi una selectbox per le dimensioni
                selected_dimensions = st.multiselect('Select Dimensions', ['Date', 'Page', 'Query', 'Device', 'Country'])

            
        
            with col5:
                row_limit_options = ['No', 'Yes']
                check_box_row = st.radio('Row limit', row_limit_options)
                if check_box_row == 'Yes':
                    row_limit = st.number_input('Row limit', min_value=1, max_value=25000, value=25000)
                else:
                    row_limit = None  # Nessun limite
            with col6:
                aggregation_type = ['No', 'Auto', 'by Page']
                check_box_aggregation = st.radio('Aggregation Type', aggregation_type)
                
                
        
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
        
                    while True:
                        request_body = {
                            "startDate": start_date.strftime('%Y-%m-%d'),
                            "endDate": end_date.strftime('%Y-%m-%d'),
                            "dimensions": dimensions,  # Utilizza le dimensioni selezionate dall'utente
                            "startRow": start_row,
                            "dataState": "final",
                            "type": selected_type,
                        }
        
                        if row_limit is not None:
                            request_body["rowLimit"] = min(row_limit, 25000)  # Imposta il limite massimo a 25.000
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
        
                    df = pd.DataFrame(data_list)
                    st.dataframe(df)
        
                    #chart_data = pd.DataFrame(df, columns=["Impressions", "Clicks", "Date"])
                    #st.line_chart(chart_data, x="Date", y=["Impressions", "Clicks"], color=["#FF0000", "#00FF00"])
