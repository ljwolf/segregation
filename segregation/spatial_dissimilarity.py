"""
Spatial Dissimilarity based Segregation Metrics
"""

__author__ = "Renan X. Cortes <renanc@ucr.edu> and Sergio J. Rey <sergio.rey@ucr.edu>"

import numpy as np
import pandas as pd
import libpysal
from segregation.dissimilarity import _dissim
from libpysal.weights import Queen

__all__ = ['Spatial_Dissim']


def _spatial_dissim(data, group_pop_var, total_pop_var, w = None, standardize = False):
    """
    Calculation of Spatial Dissimilarity index

    Parameters
    ----------

    data          : a geopandas DataFrame with a geometry column.
    
    group_pop_var : string
                    The name of variable in data that contains the population size of the group of interest
                    
    total_pop_var : string
                    The name of variable in data that contains the total population of the unit
                    
    w             : W
                    A PySAL weights object. If not provided, Queen contiguity matrix is used.
                    
    standardize   : boolean
                    A condition for row standardisation of the weights matrices. If True, the values of cij in the formulas gets row standardized.
                    For the sake of comparison, the seg R package of Hong, Seong-Yun, David O'Sullivan, and Yukio Sadahiro. "Implementing spatial segregation measures in R." PloS one 9.11 (2014): e113767.
                    works by default with row standardization.
        

    Attributes
    ----------

    statistic : float
                Spatial Dissimilarity Index
                
    core_data : a geopandas DataFrame
                A geopandas DataFrame that contains the columns used to perform the estimate.
                
    Notes
    -----
    Based on Morrill, R. L. (1991) "On the Measure of Geographic Segregation". Geography Research Forum.

    """
    if (str(type(data)) != '<class \'geopandas.geodataframe.GeoDataFrame\'>'):
        raise TypeError('data is not a GeoDataFrame and, therefore, this index cannot be calculated.')
        
    if ('geometry' not in data.columns):
        data['geometry'] = data[data._geometry_column_name]
        data = data.drop([data._geometry_column_name], axis = 1)
        data = data.set_geometry('geometry')
        
    if (type(standardize) is not bool):
        raise TypeError('std is not a boolean object')
        
    if w is None:    
        w_object = Queen.from_dataframe(data)
    else:
        w_object = w
    
    if (not issubclass(type(w_object), libpysal.weights.W)):
        raise TypeError('w is not a PySAL weights object')
    
    D = _dissim(data, group_pop_var, total_pop_var)[0]
    
    data = data.rename(columns={group_pop_var: 'group_pop_var', 
                                total_pop_var: 'total_pop_var'})
    
    x = np.array(data.group_pop_var)
    t = np.array(data.total_pop_var)
    
    # If a unit has zero population, the group of interest frequency is zero
    pi = np.where(t == 0, 0, x / t)
    
    if not standardize:
        cij = w_object.full()[0]
    else:
        cij = w_object.full()[0]
        cij = cij / cij.sum(axis = 1).reshape((cij.shape[0], 1))

    # Inspired in (second solution): https://stackoverflow.com/questions/22720864/efficiently-calculating-a-euclidean-distance-matrix-using-numpy
    # Distance Matrix
    abs_dist = abs(pi[..., np.newaxis] - pi)
        
    # manhattan_distances used to compute absolute distances
    num = np.multiply(abs_dist, cij).sum()
    den = cij.sum()
    SD = D - num / den
    SD
    
    core_data = data[['group_pop_var', 'total_pop_var', 'geometry']]
    
    return SD, core_data


class Spatial_Dissim:
    """
    Calculation of Spatial Dissimilarity index

    Parameters
    ----------

    data          : a geopandas DataFrame with a geometry column.
    
    group_pop_var : string
                    The name of variable in data that contains the population size of the group of interest
                    
    total_pop_var : string
                    The name of variable in data that contains the total population of the unit
                    
    w             : W
                    A PySAL weights object. If not provided, Queen contiguity matrix is used.
    
    standardize   : boolean
                    A condition for row standardisation of the weights matrices. If True, the values of cij in the formulas gets row standardized.
                    For the sake of comparison, the seg R package of Hong, Seong-Yun, David O'Sullivan, and Yukio Sadahiro. "Implementing spatial segregation measures in R." PloS one 9.11 (2014): e113767.
                    works by default with row standardization.

    Attributes
    ----------

    statistic : float
                Spatial Dissimilarity Index
                
    core_data : a geopandas DataFrame
                A geopandas DataFrame that contains the columns used to perform the estimate.   
                
    Examples
    --------
    In this example, we will calculate the degree of spatial dissimilarity (D) for the Riverside County using the census tract data of 2010.
    The group of interest is non-hispanic black people which is the variable nhblk10 in the dataset. The neighborhood contiguity matrix is used.
    
    Firstly, we need to read the data:
    
    >>> This example uses all census data that the user must provide your own copy of the external database.
    >>> A step-by-step procedure for downloading the data can be found here: https://github.com/spatialucr/osnap/tree/master/osnap/data.
    >>> After the user download the LTDB_Std_All_fullcount.zip and extract the files, the filepath might be something like presented below.
    >>> filepath = '~/data/std_2010_fullcount.csv'
    >>> census_2010 = pd.read_csv(filepath, encoding = "ISO-8859-1", sep = ",")
    
    Then, we filter only for the desired county (in this case, Riverside County):
    
    >>> df = census_2010.loc[census_2010.county == "Riverside County"][['trtid10', 'pop10','nhblk10']]
    
    Then, we read the Riverside map data using geopandas (the county id is 06065):
    
    >>> map_url = 'https://raw.githubusercontent.com/renanxcortes/inequality-segregation-supplementary-files/master/Tracts_grouped_by_County/06065.json'
    >>> map_gpd = gpd.read_file(map_url)
    
    It is necessary to harmonize the data type of the dataset and the geopandas in order to work the merging procedure.
    Later, we extract only the columns that will be used.
    
    >>> map_gpd['INTGEOID10'] = pd.to_numeric(map_gpd["GEOID10"])
    >>> gdf_pre = map_gpd.merge(df, left_on = 'INTGEOID10', right_on = 'trtid10')
    >>> gdf = gdf_pre[['geometry', 'pop10', 'nhblk10']]
    
    The value is estimated below.
    
    >>> spatial_dissim_index = Spatial_Dissim(gdf, 'nhblk10', 'pop10')
    >>> spatial_dissim_index.statistic
    0.2864885055405311
        
    To use different neighborhood matrices:
        
    >>> from libpysal.weights import Rook, KNN
    
    Assuming K-nearest neighbors with k = 4
    
    >>> knn = KNN.from_dataframe(gdf, k=4)
    >>> spatial_dissim_index = Spatial_Dissim(gdf, 'nhblk10', 'pop10', w = knn)
    >>> spatial_dissim_index.statistic
    0.28544347200877285
    
    Assuming Rook contiguity neighborhood
    
    >>> roo = Rook.from_dataframe(gdf)
    >>> spatial_dissim_index = Spatial_Dissim(gdf, 'nhblk10', 'pop10', w = roo)
    >>> spatial_dissim_index.statistic
    0.2866269198707091
            
    Notes
    -----
    Based on Morrill, R. L. (1991) "On the Measure of Geographic Segregation". Geography Research Forum.
    
    """

    def __init__(self, data, group_pop_var, total_pop_var, w = None, standardize = False):
        
        aux = _spatial_dissim(data, group_pop_var, total_pop_var, w, standardize)

        self.statistic = aux[0]
        self.core_data = aux[1]
        self._function = _spatial_dissim