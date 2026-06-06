import folium
import streamlit as st
from pathlib import Path
from streamlit_folium import st_folium

from akwaaba_store import (
    init_store,
    find_university,
    get_university_options,
    get_campus_options,
    find_campus,
    get_nearby_hostels,
    get_hostel,
    get_hostel_image_paths,
    get_directions_url,
    get_hostel_room_types,
    get_hostel_rules,
    get_gps_coordinates,
    add_university,
    add_campus,
    add_hostel,
    _haversine,
)
from marketplace import (
    get_hostel_rating,
    get_availability_status,
    format_distance,
    get_star_html,
    add_favorite,
    remove_favorite,
    is_favorite,
    add_review,
    get_hostel_reviews,
)


def build_map(campus, hostels):
    campus_lat, campus_lon = get_gps_coordinates(campus)
    campus_map = folium.Map(location=[campus_lat, campus_lon], zoom_start=15)
    for hostel in hostels:
        hostel_lat, hostel_lon = get_gps_coordinates(hostel)
        if hostel_lat is None or hostel_lon is None:
            continue
        
        # Compute display price
        price = hostel.get('price')
        if price is None:
            room_types = hostel.get('room_types', [])
            prices = [r.get('price') for r in room_types if r.get('price') is not None]
            price = min(prices) if prices else 'N/A'

        # Get marketplace data
        rating, review_count = get_hostel_rating(hostel['name'])
        avail_status, avail_color = get_availability_status(hostel.get('available_slots', 0))
        amenities = hostel.get('amenities', [])[:3]  # Top 3 amenities
        distance = None
        if campus_lat and hostel_lat:
            distance = _haversine(campus_lat, campus_lon, hostel_lat, hostel_lon)
        distance_str = format_distance(distance)
        star_html = get_star_html(rating) if rating > 0 else "No ratings"
        
        # Build verified badge
        verified_badge = '✓ Verified' if hostel.get('verified') else ''
        
        # Image
        placeholder = hostel.get('image_urls', [])[:1] or hostel.get('image_paths', [])[:1] or ['https://via.placeholder.com/150']
        directions = get_directions_url(hostel) or '#'

        # Rich Quick View Card with all marketplace features
        card_html = f"""
        <div style="width:280px;font-family:Arial,Helvetica,sans-serif;padding:12px;background:#f9f9f9;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.1);">
          <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:8px;">
            <div style="font-weight:700;font-size:14px;flex:1;">{hostel['name']}</div>
            <span style="font-size:12px;color:#28a745;font-weight:bold;">{verified_badge}</span>
          </div>
          
          <img src="{placeholder[0]}" width="256" height="140" style="object-fit:cover;border-radius:6px;margin-bottom:8px;width:100%;"/>
          
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;font-size:12px;">
            <div>{star_html} ({review_count} reviews)</div>
            <div style="background:{avail_color};color:#fff;padding:2px 6px;border-radius:3px;font-size:11px;font-weight:bold;">{avail_status}</div>
          </div>
          
          <div style="margin-bottom:6px;font-size:12px;color:#666;">
            <div>📍 {distance_str}</div>
            <div>💰 from GHS {price}</div>
          </div>
          
          <div style="margin-bottom:8px;">
            <div style="font-size:11px;color:#666;margin-bottom:3px;"><strong>Amenities:</strong> {', '.join(amenities[:3]) if amenities else 'N/A'}</div>
          </div>
          
          <div style="display:flex;gap:4px;margin-bottom:8px;flex-wrap:wrap;">
            {''.join([f'<span style="background:#e8f4f8;color:#0066cc;padding:3px 6px;border-radius:3px;font-size:10px;">{a}</span>' for a in amenities[:3]])}
          </div>
          
          <div style="margin-bottom:8px;border-top:1px solid #ddd;padding-top:8px;">
            <div style="font-size:11px;color:#666;"><strong>Manager:</strong> {hostel.get('manager_name', 'Not listed')}</div>
            <div style="font-size:11px;color:#666;">
              {'<strong>📱 ' + hostel.get("contact_phone", "") + '</strong>' if hostel.get("contact_phone") else ''}
              {'<strong>💬 WhatsApp Available</strong>' if hostel.get("whatsapp") else ''}
            </div>
          </div>
          
          <div style="display:flex;gap:6px;flex-wrap:wrap;">
            <a href="{directions}" target="_blank" style="flex:1;background:#007bff;color:#fff;padding:6px 8px;border-radius:4px;text-decoration:none;text-align:center;font-size:12px;">📍 Directions</a>
            <a href="{directions}" target="_blank" style="flex:1;background:#28a745;color:#fff;padding:6px 8px;border-radius:4px;text-decoration:none;text-align:center;font-size:12px;">👁️ View</a>
            <a href="https://wa.me/{hostel.get('whatsapp', '')}" target="_blank" style="flex:1;background:#25d366;color:#fff;padding:6px 8px;border-radius:4px;text-decoration:none;text-align:center;font-size:12px;" {'display:none;' if not hostel.get('whatsapp') else ''}>💬 Chat</a>
          </div>
          
          <div style="margin-top:8px;font-size:11px;color:#999;text-align:center;">
            ❤️ Save to Favorites
          </div>
        </div>
        """

        iframe = folium.IFrame(card_html, width=300, height=380)
        popup = folium.Popup(iframe, max_width=320)

        folium.Marker(
            [hostel_lat, hostel_lon],
            popup=popup,
            tooltip=hostel['name'],
        ).add_to(campus_map)
    return campus_map


def _inject_flag_banner():
        # Ghana flag colors: red (#C8102E), gold (#FFD100), green (#009E49)
        flag_html = """
        <div style="width:100%;display:flex;justify-content:center;margin-bottom:8px;">
            <div style="width:90%;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.15);">
                <div style="background:#C8102E;height:36px;"></div>
                <div style="background:#FFD100;height:36px;display:flex;align-items:center;justify-content:center;">
                    <div style="width:20px;height:20px;background:#000;clip-path:polygon(50% 0,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%);">
                    </div>
                </div>
                <div style="background:#009E49;height:36px;"></div>
            </div>
        </div>
        <div style="text-align:center;margin-top:-18px;">
            <h2 style="margin:0;padding:0;font-weight:700">🇬🇭 Akwaaba Rooms</h2>
            <div style="color:#444;margin-top:4px">A nationwide hostel search platform for Ghana</div>
        </div>
        """
        st.markdown(flag_html, unsafe_allow_html=True)


def show_hostel_overview(hostel):
    st.write(f"**{hostel['name']}**")
    st.write(hostel.get('description', 'No description available.'))
    st.write(f"**Available slots:** {hostel.get('available_slots', 0)}")
    room_types = get_hostel_room_types(hostel)
    if room_types:
        st.write("**Room types and prices:**")
        st.table([{"Type": r["type"], "Price (GHS)": r["price"], "Available": r["available"]} for r in room_types])


def show_hostel_detail(hostel):
    st.header(hostel['name'])
    
    # Marketplace header: rating, verified status, manager
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        rating, review_count = get_hostel_rating(hostel['name'])
        if rating > 0:
            st.write(f"⭐ {rating} stars ({review_count} reviews)")
        else:
            st.write("No ratings yet")
    with col2:
        if hostel.get('verified'):
            st.write("✅ Verified")
    with col3:
        student_id = "student_123"  # In production, use actual student login
        if is_favorite(student_id, hostel['name']):
            if st.button("💔 Remove from Favorites", key=f"unfav_{hostel['name']}"):
                remove_favorite(student_id, hostel['name'])
                st.success("Removed from favorites")
        else:
            if st.button("❤️ Add to Favorites", key=f"fav_{hostel['name']}"):
                add_favorite(student_id, hostel['name'])
                st.success("Added to favorites")
    
    # Contact info
    if hostel.get('manager_name') or hostel.get('contact_phone') or hostel.get('whatsapp'):
        st.write("---")
        st.subheader("📞 Contact")
        contact_cols = st.columns(3)
        with contact_cols[0]:
            if hostel.get('manager_name'):
                st.write(f"**Manager:** {hostel['manager_name']}")
        with contact_cols[1]:
            if hostel.get('contact_phone'):
                st.write(f"**Phone:** {hostel['contact_phone']}")
        with contact_cols[2]:
            if hostel.get('whatsapp'):
                st.link_button("💬 WhatsApp Chat", f"https://wa.me/{hostel['whatsapp']}")
    
    # Images
    image_paths = get_hostel_image_paths(hostel)
    if image_paths:
        st.image(image_paths, caption=[Path(path).name for path in image_paths], use_column_width=True)
    else:
        st.info('No images available for this hostel yet.')

    st.subheader('Description')
    st.write(hostel.get('description', 'No description available.'))

    st.subheader('Amenities')
    amenities = hostel.get('amenities', [])
    if amenities:
        for amenity in amenities:
            st.write(f"✓ {amenity}")
    else:
        st.write('No amenities listed.')

    st.subheader('Rules')
    rules = get_hostel_rules(hostel)
    if rules:
        for rule in rules:
            st.write(f"- {rule}")
    else:
        st.write('No rules listed.')

    st.subheader('Room Types')
    room_types = get_hostel_room_types(hostel)
    if room_types:
        st.table([{"Type": room['type'], "Price (GHS)": room['price'], "Available": room['available']} for room in room_types])
    else:
        st.write('No room type details available.')

    # Reviews section
    st.subheader(f"🎓 Student Reviews ({review_count})")
    reviews = get_hostel_reviews(hostel['name'])
    if reviews:
        for review in reviews[-5:]:  # Show last 5 reviews
            with st.container():
                r_col1, r_col2 = st.columns([3, 1])
                with r_col1:
                    st.write(f"**{review['student_name']}** - {get_star_html(review['rating'])}")
                    st.write(review['comment'])
                with r_col2:
                    st.caption(review['timestamp'][:10])
    else:
        st.write("No reviews yet. Be the first to review!")
    
    # Add review form
    st.write("---")
    st.subheader("📝 Leave a Review")
    with st.form(f"review_form_{hostel['name']}"):
        student_name = st.text_input("Your name")
        star_rating = st.slider("Rating", 1, 5, 4)
        comment = st.text_area("Your review")
        submit = st.form_submit_button("Submit Review")
        if submit and student_name and comment:
            add_review(hostel['name'], student_name, star_rating, comment)
            st.success("Review submitted! Thank you!")

    directions_url = get_directions_url(hostel)
    if directions_url:
        st.write("---")
        st.markdown(f"[📍 Get Directions]({directions_url})")
    else:
        st.warning('GPS coordinates not available.')


def main():
    st.set_page_config(page_title='Akwaaba Rooms', layout='wide', page_icon='assets/ghana_flag.svg')
    _inject_flag_banner()

    # Auto-initialize database (ensures hostels table exists)
    try:
        from database import engine
        from models import Base, Hostel
        Base.metadata.create_all(bind=engine, tables=[Hostel.__table__])
    except Exception as e:
        st.warning(f"Database init warning (non-blocking): {e}")

    data = init_store()
    mode = st.sidebar.radio('App Mode', ['Explore', 'Admin'])

    university = None
    campus = None
    selected_hostel = None

    if mode == 'Admin':
        st.subheader('Admin Panel')
        admin_action = st.selectbox('Choose admin action', ['Add University', 'Add Campus', 'Add Hostel'])

        if admin_action == 'Add University':
            with st.form('add_university_form'):
                uni_code = st.text_input('University Code').strip().upper()
                uni_name = st.text_input('University Name').strip()
                if st.form_submit_button('Add University'):
                    success, message = add_university(data, uni_code, uni_name)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

        elif admin_action == 'Add Campus':
            universities = get_university_options(data)
            uni_select = st.selectbox('Select University', ['Choose a university...'] + universities)
            campus_name = st.text_input('Campus Name').strip()
            campus_lat = st.number_input('Campus Latitude', value=0.0, format='%.6f')
            campus_lon = st.number_input('Campus Longitude', value=0.0, format='%.6f')
            if st.button('Add Campus'):
                if uni_select == 'Choose a university...':
                    st.error('Please select a university.')
                else:
                    selected_uni = find_university(data, uni_select)
                    success, message = add_campus(data, selected_uni['code'], campus_name, campus_lat, campus_lon)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

        else:
            universities = get_university_options(data)
            uni_select = st.selectbox('Select University', ['Choose a university...'] + universities)
            selected_uni = find_university(data, uni_select) if uni_select != 'Choose a university...' else None
            campus_name = None
            selected_campus = None
            if selected_uni:
                campus_options = get_campus_options(selected_uni)
                campus_name = st.selectbox('Select Campus', ['Choose a campus...'] + campus_options)
                if campus_name != 'Choose a campus...':
                    selected_campus = find_campus(selected_uni, campus_name)

            with st.form('add_hostel_form'):
                hostel_name = st.text_input('Hostel Name')
                description = st.text_area('Hostel Description')
                price = st.number_input('Price (GHS)', min_value=0.0, value=0.0, format='%.2f')
                amenities_text = st.text_area('Amenities (comma separated)')
                rules_text = st.text_area('Hostel Rules (one per line)')
                room_types_text = st.text_area('Room Types (format: Type:Price:Available per line)')
                available_slots = st.number_input('Total Available Slots', min_value=0, step=1)
                hostel_lat = st.number_input('Hostel Latitude', value=0.0, format='%.6f')
                hostel_lon = st.number_input('Hostel Longitude', value=0.0, format='%.6f')
                
                # Marketplace fields
                st.write("**Marketplace Information**")
                manager_name = st.text_input('Manager Name')
                contact_phone = st.text_input('Contact Phone')
                whatsapp = st.text_input('WhatsApp Number')
                email = st.text_input('Email Address')
                verified = st.checkbox('✅ Verified Hostel', value=False)
                
                images = st.file_uploader('Hostel Images', accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'svg'])
                submitted = st.form_submit_button('Add Hostel')

                if submitted:
                    if not selected_uni:
                        st.error('Please select a university.')
                    elif not selected_campus:
                        st.error('Please select a campus.')
                    elif not hostel_name or not hostel_name.strip():
                        st.error('Hostel name is required.')
                    else:
                        # process inputs
                        rules = [r.strip() for r in rules_text.splitlines() if r.strip()]
                        room_types = []
                        for line in room_types_text.splitlines():
                            parts = [p.strip() for p in line.split(':') if p.strip()]
                            if len(parts) != 3:
                                continue
                            try:
                                room_types.append({'type': parts[0], 'price': float(parts[1]), 'available': int(parts[2])})
                            except Exception:
                                continue

                        amenities = [a.strip() for a in amenities_text.split(',') if a.strip()]

                        # save uploaded images to assets/uploads
                        upload_dir = Path('assets') / 'uploads'
                        upload_dir.mkdir(parents=True, exist_ok=True)
                        image_paths = []
                        for f in images or []:
                            fname = f.name
                            target = upload_dir / fname
                            with target.open('wb') as out:
                                out.write(f.getbuffer())
                            image_paths.append(str(target))

                        hostel_data = {
                            'name': hostel_name.strip(),
                            'description': description,
                            'rules': rules,
                            'room_types': room_types,
                            'available_slots': int(available_slots),
                            'gps_coordinates': {'latitude': float(hostel_lat), 'longitude': float(hostel_lon)},
                            'image_paths': image_paths,
                            'image_urls': image_paths,
                            'price': float(price),
                            'amenities': amenities,
                            # Marketplace fields
                            'manager_name': manager_name.strip(),
                            'contact_phone': contact_phone.strip(),
                            'whatsapp': whatsapp.strip(),
                            'email': email.strip(),
                            'verified': verified,
                        }
                        success, message = add_hostel(data, selected_uni['code'], selected_campus['name'], hostel_data)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)

        st.markdown('---')
        st.write('Use the admin panel to add new universities, campuses, and hostels.')
        return

    universities = get_university_options(data)
    university_choice = st.sidebar.selectbox('Select University', ['Choose a university...'] + universities)

    if university_choice != 'Choose a university...':
        university = find_university(data, university_choice)

    if university:
        campus_options = get_campus_options(university)
        campus_choice = st.sidebar.selectbox('Select Campus', ['Choose a campus...'] + campus_options)
        if campus_choice != 'Choose a campus...':
            campus = find_campus(university, campus_choice)

    if campus:
        st.subheader(f"{university['name']} — {campus['name']}")
        hostels = get_nearby_hostels(campus, max_distance_km=3)

        if not hostels:
            st.warning('No hostels were found near this campus. Try another campus or check back later.')
            return

        if 'detail_hostel' not in st.session_state:
            st.session_state['detail_hostel'] = None

        if st.session_state['detail_hostel'] is None:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown('### Campus Map')
                campus_map = build_map(campus, hostels)
                st_folium(campus_map, width=700, height=500)

            with col2:
                st.markdown('### Nearby Hostels')
                for hostel in hostels:
                    button_key = f"hostel_{hostel['name']}"
                    st.write(f"**{hostel['name']}**")
                    st.write(hostel.get('description', 'No description available.'))
                    st.write(f"Available slots: {hostel.get('available_slots', 0)}")
                    if st.button('View Details', key=button_key):
                        st.session_state['detail_hostel'] = hostel['name']
                        st.experimental_rerun()
                    st.markdown('---')

        else:
            hostel_name = st.session_state['detail_hostel']
            selected_hostel = get_hostel(campus, hostel_name)
            if selected_hostel:
                def clear_hostel_selection():
                    st.session_state['detail_hostel'] = None

                st.button('Back to hostel list', on_click=clear_hostel_selection)
                show_hostel_detail(selected_hostel)
            else:
                st.warning('Selected hostel could not be found. Returning to list.')
                st.session_state['detail_hostel'] = None
                st.experimental_rerun()
    else:
        st.info('Select a university and campus from the sidebar to begin exploring hostels.')


if __name__ == '__main__':
    main()
