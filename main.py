import streamlit as st
import httplib2
import pandas as pd
from apiclient import errors
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow

st.title("Google Search Console API")

# Campi di input per client_id e client_secret
client_id = st.text_input("Inserisci il tuo Client ID:")
client_secret = st.text_input("Inserisci il tuo Client Secret:", type="password")

# Imposta il percorso di reindirizzamento
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

# Imposta lo scope OAuth2
OAUTH_SCOPE = 'https://www.googleapis.com/auth/webmasters.readonly'

# Creazione del flusso OAuth2
flow = OAuth2WebServerFlow(client_id, client_secret, OAUTH_SCOPE, REDIRECT_URI)

# Genera l'URL per l'autorizzazione
authorize_url = flow.step1_get_authorize_url(REDIRECT_URI)

# Pagina di autorizzazione
st.write("Vai al seguente link nel tuo browser:")
st.write(authorize_url)

# Ottieni l'autorizzazione dall'utente
auth_code = st.text_input("Inserisci il codice di autorizzazione qui:")

# Scambio del codice di autorizzazione con le credenziali
if st.button("Genera Credenziali"):
    credentials = flow.step2_exchange(auth_code)
    st.write("Credenziali generate con successo!")

    # Crea un oggetto httplib2.Http e autorizza con le credenziali
    http = httplib2.Http()
    creds = credentials.authorize(http)

    # Creazione del servizio GSC
    webmasters_service = build('searchconsole', 'v1', http=creds)

    # Ottieni la lista dei siti nel tuo account GSC
    site_list = webmasters_service.sites().list().execute()

    # Visualizza la lista dei siti
    st.write("Lista dei siti nel tuo account GSC:")
    st.write(site_list)

    # Seleziona un sito
    selected_site = st.selectbox("Seleziona un sito GSC", [site['siteUrl'] for site in site_list['siteEntry']])

    # Mostra il sito selezionato
    st.write(f"Sito selezionato: {selected_site}")

    # Funzionalità di ispezione di URL
    st.header("Ispezione di URL")
    url_to_inspect = st.text_input("Inserisci l'URL da ispezionare:")
    if st.button("Esegui Ispezione"):
        request_body = {
            'inspectionUrl': url_to_inspect,
            'siteUrl': selected_site
        }
        response = webmasters_service.urlInspection().index().inspect(body=request_body).execute()
        st.write("Risultato dell'ispezione:")
        st.write(response)

    # Funzionalità di accesso ai dati di analytics
    st.header("Accesso ai dati di analytics")
    start_date = st.date_input("Data di inizio")
    end_date = st.date_input("Data di fine")

    if st.button("Estrai dati di analytics"):
        request_body = {
            "startDate": start_date.strftime('%Y-%m-%d'),
            "endDate": end_date.strftime('%Y-%m-%d'),
            "dimensions": ['QUERY', 'PAGE'],
            "rowLimit": 25000,
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
        st.write("Dati di analytics:")
        st.write(df)
