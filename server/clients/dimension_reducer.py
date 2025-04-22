"""
Module to handle dimension reduction.
"""

import logging

from pacmap import PaCMAP
from clients.database_connector import DatabaseConnector

class DimensionReducer:
    """
    Class to handle dimension reduction.
    """

    def __init__(
        self, 
        n_neighbours=5,
        MN_ratio=0.5,
        FP_ratio=0.5,
        init="pca",
        normalise_range=(200, 200),
        ):
        logging.info("DimensionReducer initialising.")
        self.n_neighbours = n_neighbours
        self.MN_ratio = MN_ratio
        self.FP_ratio = FP_ratio
        self.init = init
        self.normalise_range = normalise_range
        self.map_vectors = None
        logging.info("DimensionReducer initialised.")
    
    def _normalize_vectors(self, vectors):
        """
        Private method to normalize the vectors within the specified range.
        """
        keys = list(vectors.keys())
        points = list(vectors.values())
        x_values = [point[0] for point in points]
        y_values = [point[1] for point in points]
        x_min, x_max = min(x_values), max(x_values)
        y_min, y_max = min(y_values), max(y_values)
        normalized_vectors = {}
        x_range, y_range = self.normalise_range
        for key, point in zip(keys, points):
            x_norm = (point[0] - x_min) / (x_max - x_min) * 2 - 1 if x_max > x_min else 0
            y_norm = (point[1] - y_min) / (y_max - y_min) * 2 - 1 if y_max > y_min else 0
            x_scaled = x_norm * (x_range / 2)
            y_scaled = y_norm * (y_range / 2)
            normalized_vectors[key] = [x_scaled, y_scaled]
        return normalized_vectors

    def reduce_dimensions(self, database_filename):
        """
        Method to reduce the dimensions of the embeddings.
        """
        logging.info("DimensionReducer reducing dimensions.")
        self.map_vectors = None
        database_connector = DatabaseConnector(database_filename)
        embeddings_dict = database_connector.get_embeddings()
        embeddings = list(embeddings_dict.values())
        config = dict(
            n_neighbors=self.n_neighbours,
            MN_ratio=self.MN_ratio,
            FP_ratio=self.FP_ratio,
        )
        projection_model = PaCMAP(
            n_components=2,
            **config,
        )
        map_vectors = projection_model.fit_transform(embeddings, init=self.init).tolist()
        map_vectors = dict(zip(embeddings_dict.keys(), map_vectors))
        
        self.map_vectors = self._normalize_vectors(map_vectors)
        
        return self.map_vectors