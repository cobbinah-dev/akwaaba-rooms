import folium
import streamlit as st
from pathlib import Path
from streamlit_folium import st_folium

from hostel_management.akwaaba_store import (
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
)


def build_map(campus, hostels):
    campus_lat, campus_lon = get_gps_coordinates(campus)
    campus_map = folium.Map(location=[campus_lat, campus_lon], zoom_start=15)
    for hostel in hostels:
        hostel_lat, hostel_lon = get_gps_coordinates(hostel)
        if hostel_lat is None or hostel_lon is None:
            continue
        popup_html = f"<strong>{hostel['name']}</strong><br>Available: {hostel['available_slots']}<br>" \
                     f"<a href='{get_directions_url(hostel)}' target='_blank'>Directions</a>"
        folium.Marker(
            [hostel_lat, hostel_lon],
            popup=popup_html,
            tooltip=hostel['name'],
        ).add_to(campus_map)
    return campus_map


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
    image_paths = get_hostel_image_paths(hostel)
    if image_paths:
        st.image(image_paths, caption=[Path(path).name for path in image_paths], use_column_width=True)
    else:
        st.info('No images available for this hostel yet.')

    st.subheader('Description')
    st.write(hostel.get('description', 'No description available.'))

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

    directions_url = get_directions_url(hostel)
    if directions_url:
        st.markdown(f"[Get Directions]({directions_url})")
    else:
        st.warning('GPS coordinates not available.')


def main():
    st.set_page_config(page_title='Akwaaba Rooms', layout='wide')
    st.title('Akwaaba Rooms')
    st.markdown(
        'A nationwide hostel search platform for Ghana. Browse universities, select a campus, and view nearby available hostels.'
    )

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

            hostel_name = st.text_input('Hostel Name').strip()
            description = st.text_area('Hostel Description').strip()
            rules_text = st.text_area('Hostel Rules (one per line)').strip()
            room_types_text = st.text_area('Room Types (format: Type:Price:Available per line)').strip()
            available_slots = st.number_input('Total Available Slots', min_value=0, step=1)
            hostel_lat = st.number_input('Hostel Latitude', value=0.0, format='%.6f')
            hostel_lon = st.number_input('Hostel Longitude', value=0.0, format='%.6f')

            if st.button('Add Hostel'):
                if not selected_uni:
                    st.error('Please select a university.')
                elif not selected_campus:
                    st.error('Please select a campus.')
                elif not hostel_name:
                    st.error('Hostel name is required.')
                else:
                    rules = [rule.strip() for rule in rules_text.splitlines() if rule.strip()]
                    room_types = []
                    for line in room_types_text.splitlines():
                        parts = [p.strip() for p in line.split(':') if p.strip()]
                        if len(parts) != 3:
                            continue
                        room_types.append({
                            'type': parts[0],
                            'price': float(parts[1]),
                            'available': int(parts[2]),
                        })
                    hostel_data = {
                        'name': hostel_name,
                        'description': description,
                        'rules': rules,
                        'room_types': room_types,
                        'available_slots': int(available_slots),
                        'gps_coordinates': {'latitude': hostel_lat, 'longitude': hostel_lon},
                        'image_paths': [],
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
