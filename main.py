import streamlit as st
import httplib2
import pandas as pd
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
import json

def authorize_app(credentials_data, oauth_scope):
    flow = OAuth2WebServerFlow(client_id=credentials_data['client_id'],
                               client_secret=credentials_data['client_secret'],
                               scope=oauth_scope,
                               redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    authorize_url = flow.step1_get_authorize_url()
    st.write(f"Per autorizzare l'app, segui [questo link]({authorize_url})")
    auth_code = st.text_input('Inserisci il tuo Authorization Code qui:')
        
    if auth_code:
        try:
            credentials = flow.step2_exchange(auth_code)
            storage = Storage(credentials_data['client_id'] + '.dat')
            storage.put(credentials)
            return credentials
        except Exception as e:
            st.write(f"Errore durante l'autorizzazione: {e}")
        
    if auth_code:
        try:
            credentials = flow.step2_exchange(auth_code)
            storage = Storage(credentials_data['client_id'] + '.dat')
            storage.put(credentials)
            return credentials
        except Exception as e:
            st.write(f"Errore durante l'autorizzazione: {e}")
        
    if auth_code:
        try:
            credentials = flow.step2_exchange(auth_code)
            storage = Storage(credentials_data['client_id'] + '.dat')
            storage.put(credentials)
            return credentials
        except Exception as e:
            st.write(f"Errore durante l'autorizzazione: {e}")

st.title('Google Search Console Link Suggestions')

uploaded_file = st.file_uploader("Carica il tuo file JSON delle credenziali", type="json")

if uploaded_file is not None:
    credentials_data = json.loads(uploaded_file.read())
    credentials_data = credentials_data.get('installed', {})

    if 'client_id' in credentials_data and 'client_secret' in credentials_data:
        OAUTH_SCOPE = 'https://www.googleapis.com/auth/webmasters.readonly'
        credentials = authorize_app(credentials_data, OAUTH_SCOPE)

        

        if 'selected_site' not in st.session_state:
            st.session_state.selected_site = None

        if 'available_sites' not in st.session_state:
            st.session_state.available_sites = []

        credentials = authorize_app(credentials_data, OAUTH_SCOPE, REDIRECT_URI)
    
        if credentials:
            http = credentials.authorize(httplib2.Http())
        
            webmasters_service = build('searchconsole', 'v1', http=http)
        
            if not st.session_state.available_sites:
                site_list = webmasters_service.sites().list().execute()
                st.session_state.available_sites = [site['siteUrl'] for site in site_list.get('siteEntry', [])]
       
            st.session_state.selected_site = st.selectbox('Seleziona un sito web:', st.session_state.available_sites)

            url_to_inspect = st.text_input('Inserisci l\'URL da ispezionare:')
        
            if st.button('Ispeziona URL'):
                if st.session_state.selected_site is not None:
                    request_body = {
                        'inspectionUrl': url_to_inspect,
                        'siteUrl': st.session_state.selected_site
                    }
                    response = webmasters_service.urlInspection().index().inspect(body=request_body).execute()
                    st.write(f'Risultato dell\'ispezione: {response}')

            start_date = st.date_input('Data di inizio', pd.to_datetime('2023-01-01'))
            end_date = st.date_input('Data di fine', pd.to_datetime('2023-10-28'))
            row_limit = st.number_input('Limite di righe', min_value=1, max_value=25000, value=25000)

            if st.button('Ottieni dati'):
                if st.session_state.selected_site is not None:
                    request_body = {
                        "startDate": start_date.strftime('%Y-%m-%d'),
                        "endDate": end_date.strftime('%Y-%m-%d'),
                        "dimensions": ['QUERY', 'PAGE'],
                        "rowLimit": row_limit,
                        "dataState": "final"
                    }

                    response_data = webmasters_service.searchanalytics().query(siteUrl=st.session_state.selected_site, body=request_body).execute()

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

                    filtered_data = df[(df['position'] >= 11) & (df['position'] <= 20) & (df['impressions'] >= 100)]
                    st.subheader('Suggerimenti di pagine interne:')
                    st.dataframe(filtered_data)
    else:
        st.error("Il file JSON non contiene le informazioni necessarie.")
else:
    st.warning("Si prega di caricare un file JSON con le credenziali.")
