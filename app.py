import streamlit as st
import extractor as ext
import pandas as pd

@st.cache_data
def get_soup(f):
    return ext.make_soup(f)

@st.cache_data
def get_csv_output(df : pd.DataFrame) -> str:
    return df.to_csv(index=False).encode('utf-8-sig')

st.set_page_config(page_title='ShiftAdmin Schedule Extractor', layout='wide')
st.title('ShiftAdmin Schedule Extractor')
st.markdown('Convert a ShiftAdmin generated schedule page into a spreadsheet.')

with st.expander('How to use this tool'):
    st.markdown('''
1. Go to your ShiftAdmin generated schedule page in your browser.
2. Save the page as an HTML file:
   - **Chrome/Edge**: File → Save Page As → select "Webpage, Complete"
   - **Firefox**: File → Save Page As → select "Web Page, Complete"
3. Upload the saved `.html` file below.
4. The extracted schedule will appear as a table. Use the **Download CSV** button to save it.
''')

f = st.file_uploader('Upload ShiftAdmin HTML file:', type=['html', 'htm'])

if f is None:
    st.stop()

with st.spinner('Parsing schedule...'):
    try:
        soup = get_soup(f)
        shiftsp = ext.extract_calendar(soup).reset_index()

        if shiftsp.empty:
            st.warning('No shift assignments were found in this file. Make sure you uploaded a ShiftAdmin generated schedule page.')
            st.stop()

        shiftsp = shiftsp.sort_values('userName')

        st.success(f'Successfully extracted schedule for {len(shiftsp)} providers.')
        st.dataframe(shiftsp, hide_index=True, use_container_width=True)

        csv = get_csv_output(shiftsp)
        st.download_button(
            label='Download CSV',
            data=csv,
            file_name='shiftadmin_schedule.csv',
            mime='text/csv'
        )

    except Exception as e:
        st.error(f'Error parsing file: {e}')
        st.markdown('Please make sure you uploaded a ShiftAdmin generated schedule HTML page.')
