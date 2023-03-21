import os
import snowflake.connector
import json
from fpdf import FPDF
import streamlit as st
import pandas as pd
import base64
from st_aggrid import GridOptionsBuilder, AgGrid


st.set_option('deprecation.showPyplotGlobalUse', False)
st.set_page_config(layout="wide")
# st.cache()
# st.cache_resources()

#st_autorefresh(interval=2000, limit=1, key="fizzbuzzcounter")


# with open('templates/style.css', 'r') as f:
#     style = f.read()
# fixed_width_style = """
# <style>
# .ag-theme-material .ag-root-wrapper {
#     width: 1000px !important;
# }
# </style>
# """

# st.write(f"""
# <style>
# {fixed_width_style}
# </style>
# """, unsafe_allow_html=True)


# Connect to the database
conn = snowflake.connector.connect(
    user='snowpark_user',
    password='snowpark0653',
    account='OVCHZBX-QUANTIPHI_PARTNER',
    warehouse='POC_WH',
    database='POC_DB',
    schema='usecase_5'
)

cursor = conn.cursor()



LOGO_IMAGE = "qu.gif"
st.markdown(
    f"""
    <div class="container">
    <center> <h1><img width="auto" height= "50rem" class="logo-img" src="data:image/gif;base64,{base64.b64encode(open(LOGO_IMAGE, "rb").read()).decode()}"></h1><h2> NLP For Unstructured Data Extraction  : Email</h2></center>
    </div>
    """,
    unsafe_allow_html=True
)

#----------------------------------***********************





cursor.execute("SELECT * FROM POC_DB.usecase_5.email_metadata")

df = cursor.fetchall()
data = pd.DataFrame(df, columns=[desc[0] for desc in cursor.description])


data1 = data.copy()

data1['Subject'] = [x[15:] for x in data['Subject']]

gb = GridOptionsBuilder.from_dataframe(data1)
# gb.configure_pagination(paginationAutoPageSize=True) #Add pagination
gb.configure_side_bar() #Add a sidebar
# gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
gb.configure_selection('single')
gb.configure_column("Time", width=200,type=["string"],tooltip={"showTooltip":True})
gb.configure_column("Sender", width=360,type=["string"],tooltip={"showTooltip":True})
gb.configure_column("Subject", width=600,type=["string"],tooltip={"showTooltip":True})

gridOptions = gb.build()

grid_response = AgGrid(
    data1,
    gridOptions=gridOptions,
    data_return_mode='AS_INPUT',
    update_mode='MODEL_CHANGED',
    fit_columns_on_grid_load=False,
    theme='material', #Add theme color to the table
    enable_enterprise_modules=True,
    height=400,
    # fit_columns_jscode = True,
    width='100%',
    reload_data=True
)

data1 = grid_response['data']
selected = grid_response['selected_rows']
dff = pd.DataFrame(selected) #Pass the selected rows to a new dataframe df
file_name = None

if not dff.empty:
    for transaction_id in dff['Subject'].tolist():
        file_name=f"{data['Subject'][0][:15]}{transaction_id}.json"
        st.write({file_name})
        
        query = f'GET @email/{file_name} file://C:\snowflake'
        cursor.execute(query)
        st.markdown(
            f"""
            <div style="background-color:#F0F8FF;">
            <h6 style="text-align:center;"> Selected email '{transaction_id}' loaded successfully </h6><br>
            </div>
            """,
            unsafe_allow_html=True
           )
        result =  cursor.fetchone()
        st.markdown("_________________________________________________________________")
        data_col , edit_col = st.columns([1,1])
        with edit_col:
            cursor.execute(f"SELECT * FROM POC_DB.USECASE_5.{data['Subject'][0][:15]}{transaction_id}_PREDICTION ")
            dff =  cursor.fetchall()
            data = pd.DataFrame(dff, columns=[desc[0] for desc in cursor.description])



            df_styled= data.style.set_table_styles([
                {'selector':'th','props':[('font-weight','bold')]}
            ])

            hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """

            # Inject CSS with Markdown
            st.markdown(hide_table_row_index, unsafe_allow_html=True)
            st.table(df_styled)


            #if you want to hightlight header of coloum thn un coomment below code
            # df_styled= data.style.set_table_styles([
            #     {'selector':'th','props':[('font-weight','bold'),('background-color','#D3D3D3'),('color','#FFFFF')]},
            #     {'selector':'[class="Entity"]','props':[('font-weight','bold'),('color','red'),('background-color','lightgray')]}
            # ])

            # hide_table_row_index = """
            # <style>
            # thead tr th:first-child {display:none}
            # tbody th {display:none}
            # </style>
            # """

            # # Inject CSS with Markdown
            # st.markdown(hide_table_row_index, unsafe_allow_html=True)
            # st.table(df_styled)

           



        with data_col:


            with open(f"C:\snowflake\{file_name}","r") as f:
                data = json.load(f)

            data['body'] = data['body'].encode('latin-1', 'replace').decode('latin-1')
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', '', 12)
            pdf.multi_cell(0, 9, 'Sender : ' + data['sender'], border=0)
            pdf.multi_cell(0, 9, 'Subject : ' + data['subject'], border=0)
            pdf.multi_cell(0, 9, '', border=0)
            pdf.multi_cell(0, 9, data['body'], border=0)

            pdf.output('output.pdf', 'F')
            

            

            def show_pdf(file_path):
                with open(file_path,"rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="650" height="430"  type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)

            show_pdf('output.pdf')
      

    # else:
    #     st.write("No rows selected.")

