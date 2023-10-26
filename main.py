import streamlit as st
import httplib2
import pandas as pd
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
import numpy as np

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
        st.write(f"Per autorizzare l'app, segui [questo link]({authorize_url})")

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
st.title('Google Search Console API Companion')
st.write("Google Cloud Console: https://console.cloud.google.com/apis/credentials")

# Inserimento delle credenziali Google Cloud Project
st.subheader('Inserisci le tue credenziali Google Cloud Project:')
col1, col2 = st.columns(2)
with col1:
    CLIENT_ID = st.text_input('Client ID')
with col2:
    CLIENT_SECRET = st.text_input('Client Secret')

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
        tab1, tab2 = st.tabs(["URL Inspection", "Search Analytics"])

        with tab1:
            # Inserisci l'URL da ispezionare
            url_to_inspect = st.text_input("Inserisci l'URL da ispezionare:")

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
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                start_date = st.date_input('Start date', pd.to_datetime('2023-01-01'))
            with col2:
                end_date = st.date_input('End date', pd.to_datetime('2023-10-28'))
            with col3:
                row_limit_options = ['Yes', 'No']
                check_box_row = st.radio(row_limit_options)
                if check_box_row = 'Yes':
                    row_limit = st.number_input('Row limit', min_value=1, max_value=25000, value=25000)
                else
            with col4:
                # Opzioni per il tipo di dati nell'API
                options_type = {
                    'Web': 'web',
                    'News': 'news',
                    'Discovery': 'discovery',
                    'Image': 'image',
                    'Video': 'video'
                }
                selected_type = st.selectbox('Choose channel:', list(options_type.keys()))

            # Aggiungi un bottone per ottenere i dati in batch
            if st.button('Ottieni dati'):
                if st.session_state.selected_site is not None:
                    start_row = 0  # Inizia dalla prima riga
                    batch_size = 25000  # Dimensione del batch

                    data_list = []  # Inizializza una lista per i dati

                    while True:
                        request_body = {
                            "startDate": start_date.strftime('%Y-%m-%d'),
                            "endDate": end_date.strftime('%Y-%m-%d'),
                            "dimensions": ['DATE', 'QUERY', 'PAGE'],
                            "rowLimit": batch_size,
                            "startRow": start_row,
                            "dataState": "final",
                            "type": selected_type,
                            "aggregationType": "byPage"
                        }

                        response_data = webmasters_service.searchanalytics().query(siteUrl=st.session_state.selected_site, body=request_body).execute()

                        for row in response_data.get('rows', []):
                            data_list.append({
                                'date': row['keys'][0],
                                'query': row['keys'][1],
                                'page': row['keys'][2],
                                'clicks': row['clicks'],
                                'impressions': row['impressions'],
                                'ctr': row['ctr'],
                                'position': row['position']
                            })

                        if len(response_data.get('rows', [])) < batch_size:
                            # Se abbiamo meno righe di quanto richiesto, abbiamo ottenuto tutti i dati
                            break
                        else:
                            # Altrimenti, incrementa il valore di startRow per la prossima richiesta
                            start_row += batch_size

                    df = pd.DataFrame(data_list)
                    st.dataframe(df)

                    chart_data = pd.DataFrame(df, columns=["impressions", "date"])
                    st.line_chart(chart_data, x="date", y=["impressions"], color=["#FF0000"])
