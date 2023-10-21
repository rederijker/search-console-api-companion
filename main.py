# Import delle librerie
import streamlit as st
import httplib2
import pandas as pd
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow

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

# Variabile per la gestione dell'autorizzazione
authorized = False

# Variabili per gestire le credenziali
credentials = None
webmasters_service = None

# Seleziona un sito dalla lista
if CLIENT_ID and CLIENT_SECRET:
    # Flusso di autorizzazione OAuth
    flow = OAuth2WebServerFlow(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, scope=OAUTH_SCOPE, redirect_uri=REDIRECT_URI)

    
    # Verifica se l'app è già autorizzata
    if not authorized:
        authorize_url, _ = flow.authorization_url()
        st.write(f"Per autorizzare l'app, segui [questo link]({authorize_url})")
        auth_code = st.text_input('Inserisci il tuo Authorization Code qui:')
        
    
        # Se l'Authorization Code è stato inserito
        if auth_code:
            try:
                # Scambia l'Authorization Code per le credenziali
                credentials = flow.step2_exchange(auth_code)
                http = httplib2.Http()
                creds = credentials.authorize(http)
                webmasters_service = build('searchconsole', 'v1', http=creds)
                authorized = True
            except Exception as e:
                st.write(f"Errore durante l'autorizzazione: {e}")

    if authorized:
        # Ottieni la lista dei siti nell'account Google Search Console
        site_list = webmasters_service.sites().list().execute()

        # Seleziona un sito dalla lista
        selected_site = st.selectbox('Seleziona un sito web:', [site['siteUrl'] for site in site_list['siteEntry']])

        # Se un sito è stato selezionato
        if selected_site:
            st.write(f'Hai selezionato il sito web: {selected_site}')

            # Inserisci l'URL da ispezionare
            url_to_inspect = st.text_input('Inserisci l\'URL da ispezionare:')

            # Esegui l'ispezione
            if st.button('Ispeziona URL'):
                request_body = {
                    'inspectionUrl': url_to_inspect,
                    'siteUrl': selected_site
                }
                response = webmasters_service.urlInspection().index().inspect(body=request_body).execute()
                st.write(f'Risultato dell\'ispezione: {response}')

                # Ottieni dati dalla Search Console
                start_date = st.date_input('Data di inizio', pd.to_datetime('2023-01-01'))
                end_date = st.date_input('Data di fine', pd.to_datetime('2023-10-28'))
                row_limit = st.number_input('Limite di righe', min_value=1, max_value=25000, value=25000)

                if st.button('Ottieni dati'):
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
