"""AI Assistant UI for Akwaaba Rooms (separate runner to avoid mixing with main app)."""
import streamlit as st
from ai_agent import search_hostels
from pathlib import Path

st.set_page_config(page_title='Akwaaba Rooms - AI Assistant', layout='wide')
st.title('Akwaaba Rooms — AI Assistant')

q = st.text_input('Ask (e.g. "Hostels with wifi under 1500 GHS near Legon")')
if st.button('Search') and q.strip():
    results = search_hostels(q.strip(), max_results=20)
    if not results:
        st.info('No matching hostels found.')
    else:
        for r in results:
            cols = st.columns([1,3])
            with cols[0]:
                img = (r.get('image_urls') or r.get('image_paths') or ['https://via.placeholder.com/150'])[0]
                st.image(img, width=120)
            with cols[1]:
                st.subheader(r.get('name'))
                st.write(r.get('description',''))
                st.write(f"**Price:** {r.get('price')}")
                st.write(f"**Amenities:** {', '.join(r.get('amenities') or [])}")
                st.write(f"Score: {r.get('_score'):.2f}")
                st.markdown('---')
