import streamlit as st
import validators
from datetime import datetime
import pandas as pd
import numpy as np

st.title('Shopify products to Google Merchant Center')

df = pd.DataFrame()

def _removeNonAscii(s):
    s = str(s)
    return "".join(i for i in s if  ord(i)<128)

def process_data(domain_input,quantity_filter,status_filter,include_description_filter):
    try:
      #Process Data
      #validate URL
      if not (validators.url(domain_input)):
        data_load_state = st.text('Error: Domain not valid.')
        return

      #remove trailing slash
      if domain_input.endswith('/'):
          domain_input = domain_input[:-1]

      data_load_state = st.text('Processing data...')

      df_filtered = df[(df['Title'].notnull()) & (df['Image Src'].notnull())]

      df_filtered['Body'] = df_filtered['Body (HTML)'].replace(r'(<.*?>)+',"",regex=True)
      df_filtered['Body'] = df_filtered['Body'].apply(_removeNonAscii)

      if 'Variant Inventory Qty' in df:
        df_total_inventory = df.groupby(['Handle'], as_index=False)['Variant Inventory Qty'].sum()

        merged_left = pd.merge(left=df_filtered, right=df_total_inventory, how='left', left_on='Handle', right_on='Handle')

        # Select the ones you want
        df_filtered = merged_left[['Handle','Title','Body','Vendor','Published','Variant Price','Image Src','Variant Image','Status','Variant Inventory Qty_y']]
        df_filtered = df_filtered[(df_filtered['Variant Inventory Qty_y'] >= quantity_filter)]

        if(status_filter):
          df_filtered = df_filtered[(df_filtered['Status'] == "active")]

      #Create Categories Dataframe
      df_export_data = pd.DataFrame(columns=["id","title","description","link","condition","price","availability","image_link","gtin","mpn","brand","google product category"])
      for index, row in df_filtered.iterrows():
              df2 = {
                    'id': row['Handle'],
                    'title': row['Title'],
                    'link' : domain_input+"/products/"+row['Handle'],
                    'image_link' : row['Image Src'],
                    'brand' : row['Vendor'],
                    'availability' : 'in_stock',
                    'price' : '{0:.2f}'.format(row['Variant Price'])+' NZD'
                    }
              if(include_description_filter):
                df2['description'] = str(row['Body'])
              df_export_data = df_export_data.append(df2, ignore_index = True)

      data_load_state = st.text('Completed.')
      st.write(df_export_data)
      # if st.checkbox('Show processed data'):
      #   #st.subheader('Processed data')
      #   st.dataframe(df_export_data)

      # Export Data
      csv = df_export_data.to_csv(index=False)

      st.download_button(
      "Download",
      csv,
      domain_input+"-"+datetime.today().strftime('%Y-%m-%d')+".csv",
      "text/csv",
      key='download-csv'
      )
    except Exception as e:
      data_load_state.text("Error processing file "+str(e))
      print("Error: "+ e)

try:
  #Upload Data
  uploaded_file = st.file_uploader("Choose a CSV file",help="The file must be a product list exported from Shopify")
  if uploaded_file is not None:
    data_load_state = st.text('Loading data.')
    df = pd.read_csv(uploaded_file)

    data_load_state.text("Successfully imported.")
    st.write(df)

    domain_input = st.text_input("Enter the brands domain name(starting with https://)", "https://exampledomain.com",help="This is required to create each of the product links in the export.")

    quantity_filter = st.slider('Choose the minimum product stock level to include', min_value=0, max_value=100, value=10, step=1, help="Any products with a total stock quantity less than this amount will not be included in the export.")
    if not 'Variant Inventory Qty' in df:
      st.text('NOTE: Variant Inventory Qty column does not exist - above stock level filter will not apply')
    status_filter = st.checkbox("Only include active products in export",True, help="If checked, only products with a status of active will be included in the export.")
    include_description_filter = st.checkbox("Include product description in export",True, help="If checked, product description will be included in the export.")
    
    if st.button("Process", key=None, help=None, args=None, kwargs=None):
      process_data(domain_input,quantity_filter,status_filter,include_description_filter)

except Exception as e:
  error_string = str(e)
  data_load_state.text("Error processing file")
  print("Error: "+ error_string)

