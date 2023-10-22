import streamlit as st
import httplib2
import pandas as pd
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage

# Funzione per autorizzare l'app e ottenere le credenziali
def authorize_app(client_id, client_secret, oauth_scope, redirect_uri):
    # Flusso di autorizzazione OAuth
    flow = OAuth2WebServerFlow(client_id, client_secret, oauth_scope, redirect_uri)
    
    # Verifica se le credenziali sono già memorizzate nella cache
    storage = Storage("cached_credentials.json")
    credentials = storage.get()
    
    if credentials is None:
        # Se non ci sono credenziali memorizzate, richiedi l'autorizzazione
        authorize_url = flow.step1_get_authorize_url(redirect_uri)
        st.write(f"Per autorizzare l'app, segui [questo link]({authorize_url})")
        auth_code = st.text_input('Inserisci il tuo Authorization Code qui:')
        
        if auth_code:
            try:
                # Scambia l'Authorization Code per le credenziali
                credentials = flow.step2_exchange(auth_code)
                
                # Salva le credenziali nella cache
                storage.put(credentials)
            except Exception as e:
                st.write(f"Errore durante l'autorizzazione: {e}")
    
    return credentials

# Pagina iniziale
st.title('Google Search Console Link Suggestions')

# Inserimento delle credenziali
st.subheader('Inserisci le tue credenziali Google Cloud Project:')
CLIENT_ID = st.text_input('Client ID')
CLIENT_SECRET = st.text_input('Client Secret')

# Definizione dello scope OAuth
OAUTH_SCOPE = 'https://www.googleapis.com/auth/webmasters.readonly'

# URI di reindirizzamento
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

# Seleziona un sito dalla lista
if CLIENT_ID and CLIENT_SECRET:
    # Autorizza l'app e ottieni le credenziali
    credentials = authorize_app(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, REDIRECT_URI)
    
    if credentials:
        # Crea un oggetto http autorizzato
        http = credentials.authorize(httplib2.Http())
        
        # Crea il servizio Google Search Console
        webmasters_service = build('searchconsole', 'v1', http=http)
        
        # Ottieni la lista dei siti disponibili
        site_list = webmasters_service.sites().list().execute()
        available_sites = [site['siteUrl'] for site in site_list.get('siteEntry', [])]
        
        # Seleziona un sito dalla lista        
        st.write(available_sites)
        website = st.text_input('Inserisci sito')
        
        # Inserisci l'URL da ispezionare
        url_to_inspect = st.text_input('Inserisci l\'URL da ispezionare:')
        
        # Esegui l'ispezione
        if st.button('Ispeziona URL'):
            if website is not None:
                request_body = {
                    'inspectionUrl': url_to_inspect,
                    'siteUrl': website
                }
                response = webmasters_service.urlInspection().index().inspect(body=request_body).execute()
                st.write(f'Risultato dell\'ispezione: {response}')

        # Ottieni dati dalla Search Console
        start_date = st.date_input('Data di inizio', pd.to_datetime('2023-01-01'))
        end_date = st.date_input('Data di fine', pd.to_datetime('2023-10-28'))
        row_limit = st.number_input('Limite di righe', min_value=1, max_value=25000, value=25000)

        if st.button('Ottieni dati'):
            if selected_site is not None:
                request_body = {
                    "startDate": start_date.strftime('%Y-%m-%d'),
                    "endDate": end_date.strftime('%Y-%m-%d'),
                    "dimensions": ['QUERY', 'PAGE'],
                    "rowLimit": row_limit,
                    "dataState": "final"
                }

                response_data = webmasters_service.searchanalytics().query(siteUrl=selected_site, body=request_body).execute()

                data_list = []
                for row in response_data['rows']:
                    data_list.append({
                        'query': row['keys'][0],
                        'page': row['keys'][1],
                        'clicks': row['clicks'],
                        'impressions': row['impressions'],
                        'ctr': row['ctr'],
                        'position': row['position']
                    })

                df = pd.DataFrame(data_list)

                # Filtra e suggerisci pagine interne
                filtered_data = df[(df['position'] >= 11) & (df['position'] <= 20) & (df['impressions'] >= 100)]
                st.subheader('Suggerimenti di pagine interne:')
                st.dataframe(filtered_data)
