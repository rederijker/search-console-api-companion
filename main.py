# Import delle librerie
import streamlit as st
import httplib2
import pandas as pd
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Pagina iniziale
st.title('Google Search Console Link Suggestions')

# Inserimento delle credenziali
st.subheader('Inserisci le tue credenziali Google Cloud Project:')
CLIENT_ID = st.text_input('Client ID')
CLIENT_SECRET = st.text_input('Client Secret')

# Definizione dello scope OAuth
OAUTH_SCOPE = ['https://www.googleapis.com/auth/webmasters.readonly']

# Variabile per la gestione dell'autorizzazione
authorized = False

# Seleziona un sito dalla lista
if CLIENT_ID and CLIENT_SECRET:
    # Flusso di autorizzazione OAuth
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secrets.json", scopes=OAUTH_SCOPE
    )
    
    # Verifica se l'app è già autorizzata
    if st.button('Autorizza l\'app'):
        creds = flow.run_local_server(port=0)
        authorized = True

    if authorized:
        # Ottieni la lista dei siti nell'account Google Search Console
        webmasters_service = build('webmasters', 'v3', credentials=creds)
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
                response = webmasters_service.urlTestingTools().mobileFriendlyTest().run(body=request_body).execute()
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
