"""Functions to process analytics on activity data"""

import pandas as pd
from datetime import datetime
import time

class Analyzer():
    def __init__(self, activities=None):
        
        if activities is None:
            self.df = pd.read_csv('check.csv')
        else:
            try:
                self.df = pd.DataFrame(activities)
            except:
                raise Exception("Unable to convert activities to a dataframe")
            
        self.preprocess_df()
            
    def preprocess_df(self):
        """Preprocess df by adding and formatting columns prior to analysis"""
        # Create date object and sort by it
        self.df["date_obj"] = pd.to_datetime(self.df["date"], format = "%d/%m/%Y")
        self.df = self.df.sort_values(by = 'date_obj', ascending = False)
        
        # Create month and year column
        self.df["year"] = self.df["date_obj"].apply(lambda x: x.year)
        self.df["month"] = self.df["date_obj"].apply(lambda x: x.month)
        
        # Convert distance to metres
        self.df["distance"] = self.df["distance"]/1000
        
    def distance_aggregator(self, activity_type: str = None, period: str = "annual"):
        """Aggregate distance for activity type at given frequency.
        
        Args:
            activity_type (str): Optional string representing the activity 
            type. Defaults to include all activities.
            period (str): Frequency ("annual", "monthly")
            
        Returns:
            df: df with period and total distance in KM.
        """
        
        # Filter for only the set activity type
        if activity_type is not None:
            df = self.df[self.df['type'] == activity_type].copy()
        else:
            df = self.df.copy()
        
        # Group by year and get resulting df
        df_out = df.groupby('year').agg({'distance': 'sum'}).reset_index()
        
        # Convert DataFrame to a list of dictionaries for flask
        data = df_out.to_dict(orient='records')
                
        return data
    
    def cumulative_distances(self, activity_type: str = None, period: str = "annual"):
        """Creates rolling cumulative distances by year.
        
        Args:
            activity_type (str): Optional string representing the activity 
            type. Defaults to include all activities.
            
        Returns:
            df: df with all activities and cumulative distances
        """
            
        # Filter for only the set activity type
        if activity_type is not None:
            df = self.df[self.df['type'] == activity_type].copy()
        else:
            df = self.df.copy()
        
        # Subset for df rows
        df = df[["date_obj", "distance"]]
        df = df.sort_values(by="date_obj", ascending = True)

        # Get all date values in range
        min_date = df["date_obj"].min()
        max_date = df["date_obj"].max()
        print(min_date)
        print(max_date)
        date_range = pd.date_range(start=min_date, end=max_date)
        
        # Ensure all dates in the range are in the DataFrame with distance as 0 if not present
        df_full = pd.DataFrame(date_range, columns=["date_obj"])
        df_full = df_full.merge(df, on="date_obj", how="left").fillna(0)
        df_full['year'] = df_full['date_obj'].dt.year
        
        # Calculate cumulative distances by year and date delta since it happened
        df_full['cumulative_distance'] = df_full.groupby('year')['distance'].cumsum()
        df_full['delta'] = df_full.groupby('year')['date_obj'].cumcount()
        
        # Adjust first year values which aren't indexed to 1st Jan
        delta_y0 = (min_date - datetime.strptime(f"{min_date.year}-01-01", "%Y-%m-%d")).days
        df_full.loc[df_full['year'] == min_date.year, 'delta'] += delta_y0
        
        # Remove redundant columns and format date as string
        df_full['date'] = df_full['date_obj'].dt.strftime("%Y-%m-%d")
        df_full['date_long'] = df_full['date_obj'].dt.strftime('%d %b')
        #df_full['date_long'] = df_full['date_obj'].apply(lambda dt: datetime
        #                                                 (2000, dt.month, dt.day))
    
        df_full = df_full.drop(['date_obj','distance'], axis = 1)

        # Rename columns and convert to list of dictionaries
        df_full = df_full.rename(columns = {'cumulative_distance': 'distance'})        
        data = df_full.to_dict(orient='records')
        
        return data
        
tester = Analyzer()
df_out = tester.cumulative_distances("Run")