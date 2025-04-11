import pandas as pd

def extract_tables(list_dl_doc):
    all_tables = []
    for result in list_dl_doc:
        for i, table in enumerate(result.document.tables):
            table_df = table.export_to_dataframe()
            
            # 該表格無特別索引值，且與上一個處理的表格行數相同，則合併
            if all_tables and list(table_df.columns.values) == list(range(len(table_df.columns))) and len(all_tables[-1].columns) == len(table_df.columns):
                unify_columns = list(all_tables[-1].columns)
                table_df.columns = unify_columns

                table_df = pd.concat([all_tables[-1], table_df])
                all_tables.pop()

            all_tables.append(table_df) 

    return all_tables

def df_to_text(list_df_tables):
    str_tables_list = []
    for table_ix, table in enumerate(list_df_tables):
        str_table = f"## Table {table_ix}\n {table.to_markdown()}"
        str_tables_list.append(str_table)
    
    return str_tables_list