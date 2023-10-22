# Import delle librerie
import streamlit as st
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Pagina iniziale
st.title('Google Search Console Link Suggestions')

# Inserimento delle credenziali
st.subheader('Inserisci il tuo file JSON delle credenziali del Google Cloud Project:')
keyfile = st.file_uploader('Carica il file JSON delle credenziali', type=['json'])

# Variabili per la gestione dell'autorizzazione
authorized = False

# Variabili per gestire le credenziali
credentials = None
webmasters_service = None

# Se il file JSON delle credenziali è stato caricato
if keyfile:
    try:
        # Creazione di un servizio webmasters con le credenziali
        credentials = service_account.Credentials.from_service_account_info(keyfile, ['https://www.googleapis.com/auth/webmasters.readonly'])
        webmasters_service = build('webmasters', 'v3', credentials=credentials)
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
                'url': url_to_inspect
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
                    "dimensions": ['query', 'page'],
                    "rowLimit": row_limit,
                    "searchType": "web",
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
