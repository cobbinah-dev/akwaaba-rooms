"""Modern AI Assistant UI for Akwaaba Rooms - ChatGPT-like experience."""
import streamlit as st
from ai_agent import search_hostels
from marketplace import get_hostel_rating, get_availability_status, get_star_html
from pathlib import Path
import json
from datetime import datetime

# ============================================================================
# PAGE CONFIG & STYLING
# ============================================================================
st.set_page_config(
    page_title='Akwaaba Rooms - AI Assistant',
    layout='wide',
    initial_sidebar_state='expanded',
    page_icon='🤖'
)

# Modern CSS styling
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Chat-like styling */
    .chat-message {
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .user-message {
        background-color: #007bff;
        color: white;
        margin-left: 5%;
        border-bottom-right-radius: 0;
    }
    
    .assistant-message {
        background-color: white;
        color: #333;
        margin-right: 5%;
        border-bottom-left-radius: 0;
        border-left: 4px solid #007bff;
    }
    
    /* Result card styling */
    .result-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .result-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    }
    
    .result-title {
        font-size: 18px;
        font-weight: 700;
        color: #1a73e8;
        margin-bottom: 0.5rem;
    }
    
    .result-meta {
        font-size: 13px;
        color: #666;
        margin-bottom: 1rem;
    }
    
    .tag {
        display: inline-block;
        background-color: #e8f4f8;
        color: #0066cc;
        padding: 4px 10px;
        border-radius: 16px;
        font-size: 12px;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    
    /* Suggestion pills */
    .suggestion-pill {
        display: inline-block;
        background-color: #f0f0f0;
        border: 1px solid #ddd;
        padding: 8px 16px;
        border-radius: 20px;
        cursor: pointer;
        font-size: 13px;
        margin-right: 8px;
        margin-bottom: 8px;
        transition: all 0.2s;
    }
    
    .suggestion-pill:hover {
        background-color: #e0e0e0;
        border-color: #007bff;
    }
    
    /* Modern header */
    .header-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .stat-box {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .availability-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================
st.sidebar.title("🎯 Search Filters")

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

# Sidebar filters
st.sidebar.write("**Refine Your Search:**")
price_range = st.sidebar.slider(
    "💰 Price Range (GHS)",
    min_value=500,
    max_value=5000,
    value=(1000, 3000),
    step=100
)

min_rating = st.sidebar.slider(
    "⭐ Minimum Rating",
    min_value=0.0,
    max_value=5.0,
    value=3.0,
    step=0.5
)

amenities_filter = st.sidebar.multiselect(
    "🏷️ Must Have Amenities",
    ["WiFi", "AC/Aircon", "Hot Water", "Kitchen", "Laundry", "Parking", "Breakfast"]
)

availability_only = st.sidebar.checkbox("✅ Only Available Hostels", value=True)

st.sidebar.markdown("---")

# Quick actions
st.sidebar.write("**Quick Actions:**")
if st.sidebar.button("❤️ View Favorites", use_container_width=True):
    st.session_state.show_favorites = True

if st.sidebar.button("🔄 Clear History", use_container_width=True):
    st.session_state.conversation_history = []
    st.rerun()

# ============================================================================
# HEADER & TITLE
# ============================================================================
st.markdown("""
<div class="header-section">
    <h1 style="margin: 0; font-size: 2.5em;">🤖 AI Hostel Assistant</h1>
    <p style="margin: 0.5rem 0 0 0; font-size: 1.1em; opacity: 0.9;">
        Your intelligent companion for finding the perfect hostel
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SUGGESTION PILLS
# ============================================================================
st.write("**💡 Popular Queries:**")
suggestion_cols = st.columns([1, 1, 1, 1])
suggestions = [
    "Cheap hostels under 1000 GHS",
    "Hostels with WiFi near Legon",
    "Best rated hostels in Accra",
    "Hostels with AC and kitchen"
]
for col, suggestion in zip(suggestion_cols, suggestions):
    with col:
        if st.button(suggestion, use_container_width=True, key=f"sug_{suggestion}"):
            st.session_state.search_query = suggestion

st.markdown("---")

# ============================================================================
# MAIN SEARCH INTERFACE
# ============================================================================
st.write("**🔍 What are you looking for?**")
search_cols = st.columns([5, 1])
with search_cols[0]:
    query = st.text_input(
        "Ask anything about hostels...",
        placeholder="e.g., 'Hostels with WiFi and AC under 2000 GHS'",
        label_visibility="collapsed",
        key="search_input"
    )

with search_cols[1]:
    search_btn = st.button("🔍 Search", use_container_width=True)

# ============================================================================
# SEARCH RESULTS & PROCESSING
# ============================================================================
if search_btn and query.strip():
    # Add to conversation history
    st.session_state.conversation_history.append({
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "type": "user"
    })
    
    # Add to search history
    if query not in st.session_state.search_history:
        st.session_state.search_history.append(query)
    
    # Perform search
    with st.spinner("🔍 Searching across all hostels..."):
        results = search_hostels(query.strip(), max_results=30)
    
    if not results:
        st.markdown("""
        <div class="assistant-message">
        <strong>😔 Hmm, I couldn't find matching hostels.</strong><br>
        Try adjusting your filters or use more general search terms like "cheap hostels" or "near Accra".
        </div>
        """, unsafe_allow_html=True)
    else:
        # Filter results based on sidebar settings
        filtered_results = []
        for r in results:
            price = r.get('price', 0)
            if not (price_range[0] <= price <= price_range[1]):
                continue
            
            if availability_only and r.get('available_slots', 0) <= 0:
                continue
            
            # Basic rating check
            filtered_results.append(r)
        
        if not filtered_results:
            st.info("No hostels match your filter criteria. Try adjusting the filters.")
        else:
            # AI Summary
            st.markdown(f"""
            <div class="assistant-message">
            <strong>✨ Found {len(filtered_results)} perfect matches for you!</strong><br>
            Here are the best options sorted by relevance and value. Click any hostel to save to favorites.
            </div>
            """, unsafe_allow_html=True)
            
            # Display results
            st.write("---")
            st.write(f"**Results ({len(filtered_results)}):**")
            
            for idx, hostel in enumerate(filtered_results[:20], 1):
                # Get additional data
                rating, review_count = get_hostel_rating(hostel.get('name', 'Unknown'))
                avail_status, avail_color = get_availability_status(hostel.get('available_slots', 0))
                
                # Result card
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    img = (hostel.get('image_urls') or hostel.get('image_paths') or ['https://via.placeholder.com/150'])[0]
                    st.image(img, use_column_width=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="result-card">
                        <div class="result-title">#{idx} {hostel.get('name', 'Unknown Hostel')}</div>
                        <div class="result-meta">
                            {get_star_html(rating) if rating > 0 else '⭐ No ratings yet'} 
                            ({review_count} reviews)
                        </div>
                        
                        <div style="margin-bottom: 0.8rem;">
                            <span class="availability-badge" style="background-color: {avail_color}; color: white;">
                                {avail_status}
                            </span>
                        </div>
                        
                        <p style="font-size: 14px; color: #333; margin-bottom: 0.8rem;">
                            {hostel.get('description', 'No description available')[:150]}...
                        </p>
                        
                        <div style="margin-bottom: 0.8rem;">
                            <strong style="font-size: 16px; color: #28a745;">GHS {hostel.get('price', 'N/A')}</strong>
                            <span style="color: #666; font-size: 12px;"> per month</span>
                        </div>
                        
                        <div style="margin-bottom: 0.8rem;">
                    """, unsafe_allow_html=True)
                    
                    # Amenities
                    amenities = hostel.get('amenities', [])[:4]
                    for amenity in amenities:
                        st.write(f"<span class='tag'>{amenity}</span>", unsafe_allow_html=True)
                    
                    st.markdown(f"""
                        </div>
                        
                        <div>
                            <strong>📊 Match Score:</strong> {hostel.get('_score', 0):.1%}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Action buttons
                    res_col1, res_col2, res_col3 = st.columns(3)
                    with res_col1:
                        if st.button("❤️ Save", key=f"fav_{idx}_{hostel.get('name')}", use_container_width=True):
                            if hostel.get('name') not in st.session_state.favorites:
                                st.session_state.favorites.append(hostel.get('name'))
                            st.success("Added to favorites!")
                    with res_col2:
                        if st.button("📍 Map", key=f"map_{idx}_{hostel.get('name')}", use_container_width=True):
                            st.info(f"📍 Opening map for {hostel.get('name')}...")
                    with res_col3:
                        if st.button("📞 Contact", key=f"contact_{idx}_{hostel.get('name')}", use_container_width=True):
                            st.info("📞 Contact info opening...")
                
                st.write("")

# ============================================================================
# CONVERSATION HISTORY SECTION
# ============================================================================
if st.session_state.conversation_history:
    st.markdown("---")
    with st.expander("📜 Search History"):
        for item in st.session_state.conversation_history[-10:]:
            st.write(f"• {item['query']}")

# ============================================================================
# FAVORITES SECTION
# ============================================================================
if st.session_state.favorites:
    st.markdown("---")
    with st.expander(f"❤️ Your Favorites ({len(st.session_state.favorites)})"):
        for fav in st.session_state.favorites:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{fav}**")
            with col2:
                if st.button("Remove", key=f"rem_fav_{fav}"):
                    st.session_state.favorites.remove(fav)
                    st.rerun()

# ============================================================================
# AI TIPS
# ============================================================================
st.markdown("---")
with st.expander("💡 AI Assistant Tips"):
    st.write("""
    **Try these search patterns:**
    - "Hostels under 1500 GHS" - Price-based search
    - "WiFi and AC" - Amenities search
    - "Best rated hostels" - Rating-based search
    - "Close to campus" - Location-based search
    - "Cheapest hostels with kitchen" - Combined search
    
    **The AI can help with:**
    ✓ Finding hostels by price, amenities, or rating
    ✓ Comparing options and recommendations
    ✓ Checking availability
    ✓ Saving favorites
    ✓ Getting contact information
    """)
