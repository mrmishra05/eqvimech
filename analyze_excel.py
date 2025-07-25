#!/usr/bin/env python3
import pandas as pd
import sys

def analyze_excel_file(file_path):
    try:
        print(f"\n=== Analyzing {file_path} ===")
        
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        print(f"Sheets: {excel_file.sheet_names}")
        
        for sheet_name in excel_file.sheet_names:
            print(f"\n--- Sheet: {sheet_name} ---")
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            
            # Show first few rows
            print("\nFirst 5 rows:")
            print(df.head().to_string())
            
            # Show data types
            print(f"\nData types:")
            print(df.dtypes.to_string())
            
            # Show unique values for categorical columns
            for col in df.columns:
                if df[col].dtype == 'object' and df[col].nunique() < 20:
                    print(f"\nUnique values in '{col}': {sorted(df[col].dropna().unique())}")
                    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

if __name__ == "__main__":
    analyze_excel_file("/home/ubuntu/upload/ItemlistwithTags.xlsx")
    analyze_excel_file("/home/ubuntu/upload/ItemStagesDropDown.xlsx")

