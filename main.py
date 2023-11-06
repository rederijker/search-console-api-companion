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
from streamlit_raw_echarts import st_echarts, JsCode
from datetime import datetime, timedelta
import altair as alt

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
                today = datetime.now()
                # Calcola la data di 3 mesi fa
                three_months_ago = today - timedelta(days=90)

                selected_type = st.selectbox('CHANNEL', list(options_type.keys()))
                with st.container():                   
                    start_date = st.date_input('Start date', pd.to_datetime(three_months_ago))                   
                    end_date = st.date_input('End date', pd.to_datetime(today))
                
                    
               
                
            with col2:
                # Aggiungi una selectbox per le dimensioni
                selected_dimensions = st.multiselect('DIMENSIONS', ['Date', 'Page', 'Query', 'Device', 'Country'], default=['Query', 'Page', 'Date'] )
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
                         #check_box_aggregation = st.radio('AGGREGATION TYPE', aggregation_type)

                    with col2:                                       
               
                        row_limit_options = ['No', 'Yes']
                        check_box_row = st.radio('SET ROW LIMIT?', row_limit_options)
                        if check_box_row == 'Yes':
                            row_limit = st.number_input('Row limit', min_value=1, max_value=25000, value=25000)
                        else:
                            row_limit = None  # Nessun limite
                
                
        
            # Aggiungi un bottone per ottenere i dati in batch
            if st.button('⬇️ GET DATA'):
                
                if st.session_state.selected_site is not None:
                    start_row = 0  # Inizia dalla prima riga
                    data_list = []  # Inizializza una lista per i dat                   
            
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
                                request_body["rowLimit"] = 25000  # Imposta un limite predefinito a 25.00'
                
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
                        st.subheader("Your Data")
                    with col2:
                        st.metric(label="Total Clicks", value=total_clicks_m)
                        st.text("")
                    with col3:
                        st.metric(label="Total Impressions", value=total_impressions_m)         
                    with col4:
                        st.metric(label="Average Position", value=formatted_average_m)
                    with col5:
                        st.metric(label="Average CTR", value=formatted_ctr_m)
                        
                    col1, col2 = st.columns(2)
                    with col1:
                        st.dataframe(df, width=2000)

                    with col2:
                        #TRAFFIC REPORT GRAF SETUP
                        df_graf = df.groupby('Date').agg({
                            'Clicks': 'sum',
                            'Impressions': 'sum',
                            'CTR': 'mean',
                            'Position': 'mean'
                        }).reset_index()                        
                          
                                
    
                        def traffic_report(df_graf):
                            # Formattazione della colonna 'CTR' del DataFrame
                            df_graf['CTR'] = df_graf['CTR'].apply(lambda ctr: f"{ctr * 100:.2f}")
                            #df['CTR'] = df_graf['CTR'].apply(lambda ctr: f"{ctr * 100:.2f}".replace('.', ','))
                            #df_graf['CTR'] = (df_graf['CTR'] * 100).apply('{:.2f}'.format).str.replace('.', ',')
    
    
                            df['Position'] = df_graf['Position'].apply(lambda pos: round(pos, 2))
                        
                            # Opzioni tradotte di ECharts
                            options = {
                                "xAxis": {
                                    "type": "category",
                                    "data": df_graf['Date'].tolist(),
                                    "axisLabel": {
                                        "formatter": "{value}"
                                    }
                                },
                                "yAxis": {"type": "value", "name": ""},
                                "grid": {
                                    "right": 20,
                                    "left": 65,
                                    "top": 45,
                                    "bottom": 50,
                                },
                                "legend": {
                                    "show": True,
                                    "top": "top",
                                    "align": "auto",
                                    "selected": {  
                                        "Clicks": True,         # La serie "Clicks" è selezionata
                                        "Impressions": True,    # La serie "Impressions" è selezionata
                                        "CTR": False,           # La serie "CTR" non è selezionata
                                        "Position": False       # La serie "Position" non è selezionata
                                    }
                                },
                                "tooltip": {"trigger": "axis", },
                                "series": [
                                    {
                                        "type": "line",
                                        "name": "Clicks",
                                        "data": df_graf['Clicks'].tolist(),
                                        "smooth": True,
                                        "lineStyle": {"width": 1, "color": "#D5A021"},
                                        "showSymbol": True,  # Rimuovi i marcatori dei dati per questa serie
                                    },
                                    {
                                        "type": "line",
                                        "name": "Impressions",
                                        "data": df_graf['Impressions'].tolist(),
                                        "smooth": True,
                                        "lineStyle": {"width": 1, "color": "#F06449"},
                                        "showSymbol": False,  # Rimuovi i marcatori dei dati per questa serie
                                    },
                                    {
                                        "type": "line",
                                        "name": "CTR",
                                        "data": df_graf['CTR'].tolist(),
                                        "smooth": True,
                                        "lineStyle": {"width": 1, "color": "#91C499"},
                                        "showSymbol": False,  # Rimuovi i marcatori dei dati per questa serie
                                    },
                                    {
                                        "type": "line",
                                        "name": "Position",
                                        "data": df_graf['Position'].tolist(),
                                        "smooth": True,
                                        "lineStyle": {"width": 1, "color": "#5BC3EB"},
                                        "showSymbol": False,  # Rimuovi i marcatori dei dati per questa serie
                                        "yAxisIndex": 1,  # Indica che questa serie utilizzerà il secondo asse Y
                                        "axisLabel": {
                                            "show": False  # Nascondi le etichette dell'asse Y per questa serie
                                        }
                                    },
                                ],
                        
                                "yAxis": [
                                    {"type": "value", "name": ""},
                                    {"type": "value", "inverse": True, "show": False},  # Secondo asse Y con opzione "inverse"
                                ],
                                "backgroundColor": "#0E1117",
                                "color": ["#D5A021", "#F06449", "#91C499", "#5BC3EB"],
                            }
                        
                            st_echarts(option=options, theme='chalk', height=500, width='100%')                    
                        traffic_report(df_graf)
            
                    st.subheader("ANALYSIS")
            
                

                    
                    tab1, tab2, tab3 = st.tabs(["QUERY PERFORMANCE", "PAGE PERFORMANCE", "CONTENT OPTIMIZER"])
                    with tab1:
                        if all(dim in selected_dimensions for dim in ['Query', 'Page']):
                            df = pd.DataFrame(data_list)                        
                        
	                        # Calcola i valori minimi e massimi per il grafico
                            min_ctr = df['CTR'].min()
                            max_ctr = df['CTR'].max()
                            min_position = df['Position'].min()
                            max_position = df['Position'].max()
	                        
	                        # Calcola i valori medi di CTR e Posizione solo per le query selezionate
                            average_ctr = df['CTR'].mean()
                            average_position = df['Position'].mean()
	                        
	                        # Crea il grafico a bolle con Plotly utilizzando il DataFrame filtrato
                            fig = px.scatter(df, x='CTR', y='Position', size='Clicks', hover_data=['Query'])
	                        
                            fig.update_yaxes(autorange="reversed")
                            fig.update_yaxes(range=[min_position, max_position])
                            fig.update_xaxes(range=[min_ctr * 100, max_ctr * 100])
                            fig.update_xaxes(autorange=True)  # Autoscaling per l'asse X
	                        
	                        # Aggiungi linee di riferimento per la media di CTR e posizione
                            fig.add_shape(type='line', x0=average_ctr, x1=average_ctr, y0=min_position, y1=max_position, line=dict(color='green', dash='dash'))
                            fig.add_shape(type='line', x0=min_ctr, x1=max_ctr, y0=average_position, y1=average_position, line=dict(color='green', dash='dash'))
	                        
	                        # Mostra il grafico interattivo
                            st.subheader("Bubble Charts")
                            st.plotly_chart(fig, use_container_width=True)        

                            st.scatter_chart(df, x='CTR', y='Position', size='Clicks', hover_data=['Query'])

			
                                
	
				    
                            
                                
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
                        else:
                            st.write("Nessun dato da mostrare")

                    with tab2:                          
                       
                        #suddividere i dati in quattro DataFrame in base ai quadranti specificati e fornire all'utente la lista delle query in ciascun quadrante
                      
                        try:
                            #questa funzione serve a raggruppare il df per pagina, scegliendo come calcolare ogni singola colonna
                            agg_funcs = {
                                'Impressions': 'sum',
                                'Clicks': 'sum',
                                'CTR': 'mean',
                                'Position': 'mean'
                            }
                            #Raggruppiamo df
                            df_aggregated_popular_page = df.groupby('Page').agg(agg_funcs).reset_index()

                            #Calcoliamo il CTR dividendo click per impression
                            df_aggregated_popular_page['CTR'] = (df_aggregated_popular_page['Clicks'] / df_aggregated_popular_page['Impressions'])
                            # calcoliamo ctr medio e presentiamo il CTR come %

                            df_aggregated_popular_page['CTR'] = df_aggregated_popular_page['CTR'].map('{:.2%}'.format)
                            #Cambiano nome alle colonne
                            df_aggregated_popular_page = df_aggregated_popular_page.rename(columns={'CTR': 'Average CTR'})
                            #Formatta la posizione media

                            df_aggregated_popular_page['Position'] = df_aggregated_popular_page['Position'].round(2)
                            average_position_popular = df_aggregated_popular_page['Position'].mean()
                            #cambia nome alla colonna
                            df_aggregated_popular_page = df_aggregated_popular_page.rename(columns={'Position': 'Average Position'})                         
                            # Calcola la media dei clic solo tra le pagine distinte
                            average_clic_df_popular = df_aggregated_popular_page['Clicks'].mean()
                            
                            average_impression_df_pupular = df_aggregated_popular_page['Impressions'].mean()
                            # Calcola impression solo tra le pagine distinte                            
                            # Filtra le pagine con clic maggiori o uguali alla media
                            popular_pages = df_aggregated_popular_page[
                                (df_aggregated_popular_page['Average CTR'] > formatted_ctr_m) &
                                (df_aggregated_popular_page['Clicks'] > average_clic_df_popular) &
                                (df_aggregated_popular_page['Impressions'] > average_impression_df_pupular) &
                                (df_aggregated_popular_page['Average Position'] < 10)
                            ]                            #ordiniamo per clicks
                            popular_pages = popular_pages.sort_values(by='Clicks', ascending=False)
                            less_pages = df_aggregated_popular_page[
                                (df_aggregated_popular_page['Average CTR'] < formatted_ctr_m) &
                                (df_aggregated_popular_page['Clicks'] > average_clic_df_popular) &
                                (df_aggregated_popular_page['Impressions'] > average_impression_df_pupular) &
                                (df_aggregated_popular_page['Average Position'] < 10)
                            ]
                            opp_pages= df_aggregated_popular_page[
                                (df_aggregated_popular_page['Clicks'] > average_clic_df_popular) &
                                (df_aggregated_popular_page['Impressions'] > average_impression_df_pupular) &
                                (df_aggregated_popular_page['Average Position'] > 10 )  &
                                (df_aggregated_popular_page['Average Position'] <= 20 )
                                
                            ]
                            worst_pages=df_aggregated_popular_page[
                                (df_aggregated_popular_page['Clicks'] < average_clic_df_popular) &
                                (df_aggregated_popular_page['Impressions'] < average_impression_df_pupular) &
                                (df_aggregated_popular_page['Average CTR'] < formatted_ctr_m)  &
                                (df_aggregated_popular_page['Average Position'] > average_position_popular)
                             ]

                            col1, col2, col3, col4, col5 = st.columns(5)
                            
                            format_average_clicks_popular = "{:.2f}".format(average_clic_df_popular)
                            format_average_impression_popular = "{:.2f}".format(average_impression_df_pupular)
                            format_average_position_popular = "{:.2f}".format(average_position_popular)

                            with col1:
                                st.subheader("📄 Pages Performance")
                            with col2:
                                st.metric("Pages Average Clicks", value=format_average_clicks_popular)
                            with col3:
                                st.metric("Pages Average Impressions", value=format_average_impression_popular)
                            with col4:
                                st.metric("Pages Average CTR", value=formatted_ctr_m)
                            with col5:
                                st.metric("Pages Average Position", value=format_average_position_popular)
                                st.text("")



                            with st.expander("🟢 Best Pages"):
                                st.write("Pages with an elevated Click-Through Rate (CTR), a significant volume of Clicks, and a substantial number of Impressions (exceeding the average), with Average position within the top 10 search engine result positions.")
                                st.write(popular_pages)
                            with st.expander("🟡 Less Effective Pages"):
                                st.write("Page with High Clicks, High Impressions and Average position within the top 10 search engine result positions, but low CTR")
                                st.write(less_pages)
                            with st.expander("🔵 Pages with ranking opportunities"):
                                st.write("Page with High Clicks, High Impressions but average position beetwen 10-20 in SERP")
                                st.write(opp_pages)
                            with st.expander("🔴 Pages that require attention"):
                                st.write("Page low CLicks, Low Impression, Low CTR and Low Position in comparison to the average")
                                st.write(worst_pages)

                            
                            
                            # Calcola il numero di righe nei quattro insiemi di dati
                            worst_pages_count = worst_pages.shape[0]
                            opp_pages_count = opp_pages.shape[0]
                            less_pages_count = less_pages.shape[0]
                            popular_pages_count = popular_pages.shape[0]
                            
                            # Crea un dizionario per i dati da visualizzare nel grafico a barre
                            chart_data = {
                                "Set": ["Best Pages", "Less Effective Pages", "Ranking opportunities", "Require attention"],
                                "N°Pages": [popular_pages_count, less_pages_count, opp_pages_count, worst_pages_count]
                            }                           

                            # Crea il grafico a barre utilizzando st.bar_chart
                            st.bar_chart(chart_data, x="Set", y="N°Pages")

                                
                            
                        except KeyError as e:
                            st.warning(e)
                        
                    with tab3:
                        if all(dim in selected_dimensions for dim in ['Date']):
                            st.text("")   
                        else:
                            st.text("")

                    #CREAZIONE GRAFICO REPORT

                    
                       # Raggruppa il DataFrame df per la colonna 'Date' e calcola le somme di 'Clicks' e 'Impressions' e la media di 'CTR' e 'Position'


                        
