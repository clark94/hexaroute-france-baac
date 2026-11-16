"""HexaRoute · Tableau de bord national des accidents corporels (BAAC officiel)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.pipeline import build_dataset
from src.sources import DATASET_PAGE, fetch_years
from src.style import apply_style, section
from src.interactive_map import build_map_payload, build_map_html, build_hero_html, MAX_MAP_POINTS
from src.ui_embed import render_html_frame
from src.analytics import year_month_trend, day_hour_matrix, snapshot

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'data' / 'raw'
PROCESSED = ROOT / 'data' / 'processed'
COLOR = {'Mortel': '#FC7487', 'Avec blessé hospitalisé': '#F6C66E',
         'Avec blessé léger': '#61C9DE', 'Indéterminée': '#8693AB'}
WEEKDAYS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
MONTHS = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']

st.set_page_config(page_title='HexaRoute | Observatoire BAAC', page_icon='🛣️', layout='wide',
                   initial_sidebar_state='expanded')
apply_style()


def fmt_int(x):
    return f'{int(x):,}'.replace(',', ' ')


def plot_chart(fig, key=None):
    fig.update_layout(
        template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#BECBE1', family='DM Sans'),
        margin=dict(l=18, r=18, t=30, b=15),
        legend=dict(orientation='h', y=-0.18),
        hoverlabel=dict(bgcolor='#1C2940'),
    )
    fig.update_xaxes(showgrid=False, linecolor='#37435B')
    fig.update_yaxes(gridcolor='#26364C', zeroline=False)
    st.plotly_chart(fig, use_container_width=True, key=key)


@st.cache_data(show_spinner=False)
def local_tables():
    a = pd.read_parquet(PROCESSED / 'accidents.parquet')
    u = pd.read_parquet(PROCESSED / 'usagers.parquet')
    return a, u


@st.cache_data(ttl=1800, show_spinner=False)
def snowflake_tables():
    from src.snowflake_io import fetch_tables
    return fetch_tables()


def import_data(years):
    year_list = list(years)
    try:
        with st.status('Chargement des données officielles en cours…', expanded=True) as s:
            def log(text):
                st.write('• ' + text)
            fetch_years(year_list, RAW, progress=log)
            stats = build_dataset(year_list, RAW, PROCESSED, progress=log)
            st.write(f"{fmt_int(stats['accidents'])} accidents préparés et vérifiés.")
            s.update(label='Données officielles préparées avec succès.', state='complete')
        local_tables.clear()
        st.rerun()
    except Exception as err:
        st.error(f'Importation interrompue : {err}')
        st.info('Vérifie ta connexion Internet, puis réessaie. Les CSV déjà téléchargés sont conservés.')


def loading_screen():
    st.markdown('## Première utilisation · récupérer les données réelles')
    st.markdown('''<div class="callout">Les graphiques ne sont <b>jamais fabriqués</b> :
    les fichiers originaux sont téléchargés depuis data.gouv.fr, contrôlés, puis convertis en Parquet.
    Le téléchargement exige une connexion Internet uniquement à cette première étape.</div>''', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader('⚡ Démarrage rapide')
        st.write('4 CSV officiels · année 2025 · environ 30 à 35 Mo de données sources.')
        if st.button('Télécharger et analyser 2025', type='primary', use_container_width=True):
            import_data([2025])
    with c2:
        st.subheader('📈 Étude pluriannuelle')
        st.write('12 CSV officiels · 2023, 2024 et 2025 · comparaison temporelle.')
        if st.button('Charger 2023–2025', use_container_width=True):
            import_data([2023, 2024, 2025])
    st.caption('Données : ministère de l’Intérieur / ONISR · Licence Ouverte 2.0 · accidents corporels enregistrés, pas tous les incidents routiers.')
    st.link_button('Consulter les données officielles', DATASET_PAGE)


def filter_accidents(a):
    with st.sidebar:
        st.markdown('### PÉRIMÈTRE')
        years = sorted(int(y) for y in a.annee.dropna().unique())
        sel_years = st.multiselect('Années', years, default=years)
        if not sel_years:
            st.warning('Sélectionne au moins une année.')
            st.stop()
        deps = sorted(a.departement.dropna().astype(str).unique())
        sel_deps = st.multiselect('Départements', deps, placeholder='Tous les départements')
        milieux = sorted(a.milieu.dropna().unique())
        sel_mil = st.multiselect('Milieu', milieux, placeholder='Tous les milieux')
        gravites = list(COLOR)
        sel_grav = st.multiselect('Gravité de l’accident', gravites, placeholder='Toutes les gravités')
        months = st.slider('Mois', 1, 12, (1, 12))
        st.divider()
        st.caption('Un accident = une ligne ; les usagers et véhicules sont agrégés avant jointure.')
        st.caption('Les indicateurs ne sont pas des taux de risque rapportés au trafic ou à la population.')

    f = a[a.annee.isin(sel_years)]
    if sel_deps:
        f = f[f.departement.astype(str).isin(sel_deps)]
    if sel_mil:
        f = f[f.milieu.isin(sel_mil)]
    if sel_grav:
        f = f[f.gravite_accident.isin(sel_grav)]
    f = f[f.mois_num.between(months[0], months[1])]
    return f


def executive_view(f):
    """Vue de direction : comparer les périodes et repérer les volumes observés."""
    insights = snapshot(f)
    section('Lecture exécutive', 'Trois observations sur le périmètre filtré. Les volumes ne sont pas des taux de risque.')
    a,b,c = st.columns(3, gap='medium')
    dep = f"{insights['departement']}" if insights['departement'] else '—'
    hour = f"{insights['heure']:02d} h" if insights['heure'] is not None else '—'
    with a:
        st.markdown(f'<div class="insight"><div class="insight-label">DÉPARTEMENT LE PLUS REPRÉSENTÉ</div>'
                    f'<div class="insight-value">{dep}</div><p>{fmt_int(insights["departement_nombre"])} accidents enregistrés</p></div>', unsafe_allow_html=True)
    with b:
        st.markdown(f'<div class="insight"><div class="insight-label">HEURE LA PLUS FRÉQUENTE</div>'
                    f'<div class="insight-value">{hour}</div><p>{fmt_int(insights["heure_nombre"])} accidents enregistrés</p></div>', unsafe_allow_html=True)
    with c:
        st.markdown(f'<div class="insight"><div class="insight-label">PART DES ACCIDENTS MORTELS</div>'
                    f'<div class="insight-value">{insights["part_mortels"]:.1f} %</div>'
                    f'<p>{fmt_int(insights["mortels"])} accidents mortels dans la sélection</p></div>', unsafe_allow_html=True)

    section('Tendance et sévérité', 'Comparaison mensuelle par année ; les mois absents d’une source ne sont pas des prévisions.')
    c1,c2 = st.columns([1.7, 1.0], gap='large')
    with c1:
        monthly = year_month_trend(f)
        if not monthly.empty:
            monthly['Année'] = monthly.annee.astype(str)
            monthly['Mois'] = monthly.mois_num.map(dict(enumerate(MONTHS, 1)))
            fig = px.line(monthly, x='Mois', y='accidents', color='Année', markers=True,
                          category_orders={'Mois': MONTHS},
                          labels={'accidents': 'Accidents corporels'},
                          color_discrete_sequence=['#62DCE8','#93A6FF','#F4CA7C','#F78D98'])
            fig.update_traces(line=dict(width=3), marker=dict(size=7))
            plot_chart(fig, 'exec_trend')
    with c2:
        severity = f.gravite_accident.value_counts().rename_axis('Gravité').reset_index(name='Accidents')
        fig = px.pie(severity, names='Gravité', values='Accidents', hole=.65,
                     color='Gravité', color_discrete_map=COLOR)
        fig.update_traces(textinfo='percent', textposition='inside')
        plot_chart(fig, 'exec_gravite')

    section('Quand les accidents sont-ils recensés ?', 'Carte thermique : nombre brut d’accidents par jour et heure de la semaine.')
    mat = day_hour_matrix(f)
    fig = go.Figure(go.Heatmap(z=mat.to_numpy(), x=[f'{hr:02d}h' for hr in mat.columns], y=mat.index.tolist(),
                              colorscale=[[0,'#15243B'],[.35,'#25566F'],[.68,'#42A6B9'],[1,'#86F0EB']],
                              colorbar=dict(title='Accidents', thickness=11),
                              hovertemplate='%{y} · %{x}<br>%{z:,} accidents<extra></extra>'))
    fig.update_layout(height=350, yaxis=dict(autorange='reversed'), xaxis_title='Heure de la journée')
    plot_chart(fig, 'exec_heatmap')
    st.caption('Lecture descriptive uniquement : les volumes de circulation varient selon les heures et les jours.')

    section('Départements · les 8 volumes les plus élevés', 'Classement brut, sans rapporter le nombre d’accidents au trafic.')
    depts = f.departement.dropna().value_counts().head(8).sort_values()
    if not depts.empty:
        fig = px.bar(x=depts.values, y=depts.index.astype(str), orientation='h',
                     labels={'x':'Nombre d’accidents', 'y':'Code département'},
                     color_discrete_sequence=['#68D9E4'])
        fig.update_layout(height=310)
        plot_chart(fig, 'exec_deps')
    st.info('Pour une interprétation du **risque routier**, il faudrait compléter les données BAAC par une mesure d’exposition au trafic.')


def national(f):
    section('Évolution des accidents', 'Comptage des accidents corporels observés dans les données sélectionnées.')
    monthly = f.dropna(subset=['date']).copy()
    if monthly.empty:
        st.info('Aucune date valide dans la sélection.'); return
    monthly['periode'] = monthly.date.dt.to_period('M').dt.to_timestamp()
    monthly = monthly.groupby('periode', as_index=False).agg(accidents=('num_acc', 'size'),
        deces=('nb_tues', 'sum'), blesses=('nb_blesses_graves', 'sum'))
    c1, c2 = st.columns([1.85, 1.0], gap='large')
    with c1:
        fig = px.area(monthly, x='periode', y='accidents', markers=True,
                      labels={'periode': 'Période', 'accidents': 'Accidents corporels'})
        fig.update_traces(line_color='#63DDE9', fillcolor='rgba(73,195,213,.18)')
        plot_chart(fig, 'tendance')
    with c2:
        sever = f.gravite_accident.value_counts().rename_axis('gravite').reset_index(name='nombre')
        fig = px.pie(sever, names='gravite', values='nombre', hole=.66,
                     color='gravite', color_discrete_map=COLOR)
        fig.update_traces(textposition='inside', textinfo='percent')
        plot_chart(fig, 'gravite')
    section('Rythmes et contextes')
    c1, c2, c3 = st.columns(3, gap='large')
    with c1:
        hours = f.dropna(subset=['heure']).groupby('heure').size().reindex(range(24), fill_value=0)
        fig = px.bar(x=hours.index, y=hours.values,
                     labels={'x': 'Heure de la journée', 'y': 'Accidents'}, color_discrete_sequence=['#6ED5DC'])
        plot_chart(fig, 'heures')
    with c2:
        weekday = f.dropna(subset=['jour_semaine']).groupby('jour_semaine').size().reindex(range(7), fill_value=0)
        fig = px.bar(x=WEEKDAYS, y=weekday.values, labels={'x': 'Jour', 'y': 'Accidents'},
                     color_discrete_sequence=['#F1C878'])
        plot_chart(fig, 'jours')
    with c3:
        m = f.meteo.value_counts().head(8).sort_values()
        fig = px.bar(x=m.values, y=m.index, orientation='h',
                     labels={'x':'Accidents', 'y':'Météo relevée'}, color_discrete_sequence=['#79A6F8'])
        plot_chart(fig, 'meteo')
    st.caption('Ces distributions présentent des comptages, sans correction pour les volumes de circulation et sans inférence causale.')


def geography(f):
    section('Géographie des accidents', 'Carte interactive Leaflet en JavaScript : regroupements, densité et détails au clic. Échantillonnage stable pour la fluidité.')
    geo = f.dropna(subset=['latitude', 'longitude']).copy()
    metro = geo[geo.latitude.between(41, 52) & geo.longitude.between(-6, 10)]
    if metro.empty:
        st.warning('Aucune position géographique exploitable en France métropolitaine pour cette sélection.')
    else:
        st.caption('Cliquez sur les points pour explorer les accidents. Les filtres latéraux Streamlit s’appliquent avant la carte ; le sélecteur JS filtre seulement les points affichés.')
        mode_c, info_c = st.columns([2, 3])
        with mode_c:
            map_engine = st.radio('Moteur cartographique',
                                  ['Carte JavaScript · Leaflet', 'Carte de secours · Plotly'],
                                  horizontal=False, label_visibility='collapsed')
        with info_c:
            st.caption('La carte JavaScript nécessite Internet pour Leaflet et les fonds CARTO. La vue Plotly fournit un affichage alternatif.')
        if map_engine.startswith('Carte JavaScript'):
            payload = build_map_payload(metro, MAX_MAP_POINTS)
            render_html_frame(build_map_html(payload), height=718)
            count = payload['sample_size']
        else:
            sampled = metro.sample(min(len(metro), 8000), random_state=42)
            fig = px.scatter_map(
                sampled, lat='latitude', lon='longitude', color='gravite_accident',
                color_discrete_map=COLOR, hover_name='departement',
                hover_data={'annee': True, 'date': True, 'latitude': False, 'longitude': False},
                zoom=4.45, center={'lat': 46.6, 'lon': 2.2},
                map_style='carto-darkmatter', opacity=0.5,
                title='Accidents localisés · France métropolitaine',
            )
            fig.update_layout(height=560, margin=dict(l=0,r=0,t=45,b=0),
                              paper_bgcolor='rgba(0,0,0,0)',font=dict(color='#CBD9EF'))
            st.plotly_chart(fig, use_container_width=True)
            count = len(sampled)
        st.caption(f'{fmt_int(len(metro))} accidents métropolitains géolocalisés, dont {fmt_int(count)} affichés. Les DROM/COM restent dans les statistiques mais ne figurent pas sur ce cadrage. Les points échantillonnés ne sont pas exhaustifs.')
    section('Départements · classement en nombre absolu')
    depart = f.groupby('departement', as_index=False).agg(
        accidents=('num_acc','size'), tues=('nb_tues','sum'), blesses=('nb_blesses_graves','sum'))
    depart = depart.sort_values('accidents', ascending=False)
    c1, c2 = st.columns([1.5, 1.0])
    with c1:
        top = depart.head(15).sort_values('accidents')
        fig = px.bar(top, x='accidents', y='departement', orientation='h',
                     labels={'accidents':'Accidents', 'departement':'Département'},
                     color_discrete_sequence=['#6DD5DC'])
        plot_chart(fig,'depart')
    with c2:
        st.dataframe(depart, use_container_width=True, hide_index=True, height=470,
                     column_config={'departement':'Département', 'accidents':'Accidents',
                                    'tues':'Personnes tuées', 'blesses':'Blessés hospitalisés (code BAAC)'})
    st.info('Un nombre élevé d’accidents ne signifie pas nécessairement un risque routier plus fort : il faut tenir compte du trafic, de la population et des kilomètres parcourus.')


def people_tab(f, u):
    section('Portrait des usagers', 'Comptage des personnes dans les accidents retenus par les filtres.')
    if f.empty:
        return
    # Filtrer les personnes par (année, id accident) pour éviter toute collision entre années.
    pairs = f[['annee', 'num_acc']].drop_duplicates()
    us = u.merge(pairs, on=['annee', 'num_acc'], how='inner', validate='many_to_one')
    if us.empty:
        st.info('Aucun usager associé à la sélection.'); return
    c1, c2, c3 = st.columns(3)
    c1.metric('Usagers impliqués', fmt_int(len(us)))
    c2.metric('Usagers déclarés tués', fmt_int(us.gravite_code.eq(2).sum()))
    c3.metric('Usagers déclarés blessés', fmt_int(us.gravite_code.isin([3,4]).sum()))
    c1, c2 = st.columns(2)
    with c1:
        counts = us.profil.value_counts().rename_axis('profil').reset_index(name='nombre')
        fig = px.bar(counts, x='profil', y='nombre', labels={'profil':'Rôle', 'nombre':'Usagers'},
                     color_discrete_sequence=['#65D5DB'])
        plot_chart(fig,'profiles')
    with c2:
        sev = us.gravite_code.map({1:'Indemne',2:'Tué',3:'Blessé hospitalisé',4:'Blessé léger'}).fillna('Non renseigné')
        s = sev.value_counts().rename_axis('issue').reset_index(name='personnes')
        fig = px.bar(s, x='issue', y='personnes', color='issue',
                     color_discrete_sequence=['#8DAFFC','#F16B85','#F1C777','#61D4DE','#A9B2C6'])
        plot_chart(fig,'usagers_issues')
    section('Âges des usagers renseignés')
    aged = us.dropna(subset=['age']).copy()
    if not aged.empty:
        fig = px.histogram(aged, x='age', nbins=22,
                           labels={'age':'Âge', 'count':'Usagers'},
                           color_discrete_sequence=['#8EAEFD'])
        fig.update_layout(bargap=.06)
        plot_chart(fig,'ages')
    st.caption('Les données ne couvrent que les accidents corporels recensés. L’âge et les catégories peuvent être manquants. Les codes de gravité sont issus du BAAC et leur interprétation est régie par la documentation ONISR.')


def quality_tab(a, q):
    section('Qualité & traçabilité', 'Journal d’ingestion et vérifications reproductibles. Aucune ligne statistique artificielle.')
    audits = pd.DataFrame(q.get('details_qualite', []))
    if not audits.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric('Accidents traités', fmt_int(q.get('accidents', 0)))
        c2.metric('Usagers traités', fmt_int(q.get('usagers', 0)))
        c3.metric('Clés accidents dupliquées', fmt_int(a.duplicated(['annee','num_acc']).sum()))
        c4.metric('Géolocalisation disponible', f'{100*a.latitude.notna().mul(a.longitude.notna()).mean():.1f} %')
        st.dataframe(audits, hide_index=True, use_container_width=True)
        data = audits.melt(id_vars=['annee'], value_vars=['coordonnees_manquantes', 'dates_invalides', 'accidents_sans_usagers'],
                           var_name='anomalie', value_name='nombre')
        fig = px.bar(data, x='annee', y='nombre', color='anomalie', barmode='group',
                     labels={'annee':'Année', 'nombre':'Lignes concernées'})
        plot_chart(fig,'quality')
        st.download_button('Exporter le journal qualité JSON', json.dumps(q, ensure_ascii=False, indent=2),
                           file_name='hexaroute_qualite.json', mime='application/json')
    st.info('Les coordonnées manquantes, les dates invalides et les joints sans correspondance sont tracés, pas silencieusement convertis en données fictives.')


def method_tab(f, q):
    section('Méthodologie & sources')
    st.markdown('''**Producteur :** ministère de l’Intérieur / ONISR. **Licence :** Licence Ouverte / Open Licence.

**Périmètre :** accidents corporels de la circulation enregistrés par les forces de l’ordre.
Cela ne représente ni tous les accidents matériels, ni un taux de risque par habitant ou par véhicule.

**Modèle :** `Caract` est la table centrale (un accident) ; `Lieux` lui apporte le contexte routier,
`Vehicules` et `Usagers` sont d’abord agrégés par identifiant d’accident afin d’éviter les
multiplications de lignes lors des jointures. Clé : `(annee, num_acc)`.

**Précautions :** les données de gravité reposent sur les codifications BAAC ; l’ONISR avertit
que les blessés hospitalisés ne sont pas directement comparables aux anciennes années
(rupture de collecte depuis 2018). Les cartes peuvent afficher un échantillon de points.
''')
    st.link_button('Consulter la source originale sur data.gouv.fr', DATASET_PAGE)
    st.link_button('Consulter les précautions ONISR', 'https://www.onisr.securite-routiere.gouv.fr/outils-statistiques/open-data')
    st.markdown('### Export des accidents filtrés')
    st.caption('Export limité aux colonnes analytiques ; aucun identifiant personnel. Les résultats ne sont pas anonymisés par un traitement supplémentaire.')
    export = f[['annee','num_acc','date','departement','milieu','gravite_accident',
                'nb_vehicules','nb_usagers','nb_tues','nb_blesses_graves','nb_blesses_legers']]
    st.download_button('Télécharger la sélection CSV', export.to_csv(index=False).encode('utf-8-sig'),
                       file_name='hexaroute_selection.csv', mime='text/csv')
    st.markdown('### Provenance technique')
    st.json({k: q.get(k) for k in ('genere_le_utc','annees','accidents','usagers','vehicules','source')})


render_html_frame(build_hero_html(), height=281)
with st.sidebar:
    st.markdown('### 🛣️ HEXAROUTE')
    st.caption('Observatoire BAAC · édition 2026')
    st.divider()
    source = st.selectbox('Source des analyses', ['Parquet local (recommandé)', 'Snowflake (optionnel)'])

if source.startswith('Parquet') and not (PROCESSED / 'accidents.parquet').exists():
    loading_screen()
    st.stop()

try:
    if source.startswith('Snowflake'):
        with st.spinner('Lecture des tables Snowflake…'):
            a, u = snowflake_tables()
        q = {'annees': sorted(a.annee.dropna().unique().tolist()), 'details_qualite': [],
             'accidents': len(a), 'usagers': len(u), 'source': DATASET_PAGE}
    else:
        a, u = local_tables()
        qpath = PROCESSED / 'qualite.json'
        q = json.loads(qpath.read_text(encoding='utf-8')) if qpath.exists() else {'details_qualite': []}
except Exception as exc:
    st.error(f'Impossible de charger les données : {exc}')
    st.info('Pour Snowflake : vérifier le fichier .env et installer requirements-snowflake.txt. Le mode local est disponible sans compte cloud.')
    st.stop()

if not len(a):
    st.warning('Aucun accident enregistré dans la source sélectionnée.'); st.stop()
a['date'] = pd.to_datetime(a['date'], errors='coerce')
if 'mois_num' not in a.columns:
    a['mois_num'] = a.date.dt.month
if 'jour_semaine' not in a.columns:
    a['jour_semaine'] = a.date.dt.dayofweek

f = filter_accidents(a)
if f.empty:
    st.warning('Aucune ligne pour ces filtres. Élargis les critères dans le panneau gauche.')
    st.stop()

c1,c2,c3,c4,c5 = st.columns(5, gap='small')
c1.metric('Accidents corporels', fmt_int(len(f)))
c2.metric('Accidents mortels', fmt_int(f.accident_mortel.sum()))
c3.metric('Personnes tuées', fmt_int(f.nb_tues.sum()))
c4.metric('Blessés hospitalisés*', fmt_int(f.nb_blesses_graves.sum()))
c5.metric('Véhicules impliqués', fmt_int(f.nb_vehicules.sum()))
st.markdown('<p class="smallsource">* Catégorie BAAC, à interpréter avec les avertissements méthodologiques de l’ONISR. Filtre actif : {} accidents.</p>'.format(fmt_int(len(f))), unsafe_allow_html=True)

one, two, three, four, five, six = st.tabs([
    '◈ Synthèse', '📊 Tendances', '🗺️ Carte & territoires',
    '👥 Usagers', '🧪 Qualité', '📚 Sources & exports',
])
with one:
    executive_view(f)
with two:
    national(f)
with three:
    geography(f)
with four:
    people_tab(f, u)
with five:
    quality_tab(a, q)
with six:
    method_tab(f, q)
