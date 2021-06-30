from abc import ABC, abstractmethod
from . import snn_knn as sk
from sklearn.cluster import KMeans
from pyclustering.cluster.xmeans import xmeans

import numpy as np
import hdbscan
from . import distance_matrix as dm

def get_euclidean_infos(raw, emb, dist_parameter, length, k):
    raw_dist_matrix = dm.dist_matrix_gpu(raw)
    emb_dist_matrix = dm.dist_matrix_gpu(emb)
    
    raw_dist_max = np.max(self.raw_dist_matrix)
    emb_dist_max = np.max(self.emb_dist_matrix)

    raw_dist_matrix /= raw_dist_max
    emb_dist_matrix /= emb_dist_max

    raw_knn_info = sk.knn_info(raw_dist_matrix, k)
    emb_knn_info = sk.knn_info(emb_dist_matrix, k)

    return {
        "raw_dist_matrix" : raw_dist_matrix,
        "emb_dist_matrix" : emb_dist_matrix, 
        "raw_knn"         : raw_knn_info,
        "emb_knn"         : emb_knn_info
    }


def get_snn_infos(raw, emb, dist_parameter, length, k):

    infos = get_euclidean_infos(raw, emb, dist_parameter, k)
    
    # Compute snn matrix
    raw_snn_matrix = sk.snn_gpu(infos["raw_knn"], length, k)
    emb_snn_matrix = sk.snn_gpu(infos["emb_knn"], length, k)
    raw_snn_max    = np.max(raw_snn_matrix)
    emb_enn_max    = np.max(emb_snn_matrix)

    # normalize snn matrix
    raw_snn_matrix /= raw_snn_max
    emb_snn_matrix /= emb_snn_max

    # compute dist matrix
    raw_snn_dist_matrix = 1 / (raw_snn_matrix + dist_parameter["alpha"])
    emb_snn_dist_matrix = 1 / (emb_snn_matrix + dist_parameter["alpha"])

    # update infos
    infos["raw_dist_matrix"] = raw_snn_dist_matrix
    infos["emb_dist_matrix"] = emb_snn_dist_matrix
    infos["raw_snn_matrix"]  = raw_snn_matrix
    infos["emb_snn_matrix"]  = emb_snn_matrix

    return infos

def get_a_cluster_snn(infos, mode, seed_idx, walk_num):
    if mode == "steadiness":   ## extract from the embedded (projected) space
        knn_info   = infos["emb_knn"]
        snn_matrix = infos["emb_snn_matrix"]
    if mode == "cohesiveness": ## extract from the original space
        knn_info   = infos["raw_knn"]
        snn_matrix = infos["raw_snn_matrix"]
    
    return sk.snn_based_cluster_extraction(knn_info, snn_matrix, seed_idx, walk_num)

def get_a_cluster_naive(infos, mode, seed_idx, walk_num):
    if mode == "steadiness":
        knn_info = infos["emb_knn"]
    if mode == "cohesiveness":
        knn_info = infos["raw_knn"]
    
    return sk.naive_cluster_extraction(knn_info, seed_idx, walk_num)


'''
INSTALLING Hyperparameter functions
'''

def install_hparam(dist_strategy, dist_parameter, cluster_strategy, raw, emb):
    if (dist_strategy == "snn"):
        if (cluster_strategy == "dbscan"):
            return SNNCS(dist_parameter, raw, emb)
        if (cluster_strategy == "x-means"):
            return SNNXM(dist_parameter, raw, emb)
        else:
            cluster_strategy_splitted = cluster_strategy.split("-")
            if (cluster_strategy_splitted[1] == "means"):
                K_val = int(cluster_strategy_splitted[0])
                return SNNKM(dist_parameter, raw, emb, K_val)
                
    raise Exception("Wrong strategy choice!! check dist_strategy ('" + dist_strategy + 
                    "') and cluster_strategy ('" + cluster_strategy + "')")




class HparamFunctions():
    '''
    Saving raw, emb info and setting parameter
    '''
    def __init__(self, raw, emb, dist_parameter, get_infos, get_a_cluster):
        self.raw = raw
        self.emb = emb
        self.length = len(self.raw)
        self.dist_parameter = dist_parameter
        self.k = dist_parameter["k"]
        
        ## Inject functions
        self.get_infos = get_infos
        self.get_a_cluster = get_a_cluster

    def preprocessing(self):
        self.infos = self.get_infos(self.raw, self.emb, self.dist_parameter, self.length, self.k)
        dissim_matrix = self.infos["raw_dist_matrix"] - self.infos["emb_dist_matrix"]

        dissim_max = np.max(dissim_matrix)
        dissim_min = np.min(dissim_matrix)

        max_compress = dissim_max if dissim_max > 0 else 0
        min_compress = dissim_min if dissim_min > 0 else 0
        max_stretch  = - dissim_min if dissim_min < 0 else 0
        min_stretch  = - dissim_max if dissim_max < 0 else 0
        return max_compress, min_compress, max_stretch, min_stretch

    '''
    Extract the clusters from the given incidices
    mode : steadiness / cohesiveness 
    '''
    def extract_cluster(self, mode, walk_num):
        seed_idx = np.random.randint(self.length)
        extracted_cluster = []
        while len(extracted_cluster) == 0:
            cluster_candidate.size = self.get_a_cluster(self.infos, seed_idx, wall_num)
            if cluster_candidate.size > 1:
                extracted_cluster = cluster_candidate
        return extracted_cluster
    

    '''
    Get the indices of the points which to be clustered as input
    and return the clustereing result
    mode : steadiness / cohesiveness 
    '''
    @abstractmethod
    def clustering(self, mode, indices):
        pass
    
    '''
    Compute the distance between two clusters in raw / emb space
    return two distance (raw_dist, emb_dist)
    mode: steadiness / cohesiveness
    '''
    @abstractmethod
    def compute_distance(self, mode, cluster_a, cluster_b):
        pass



class ClusterStrategy(ABC):

    '''
    Saving raw, emb info and setting parameter
    '''
    def __init__(self, dist_parameter, raw, emb):
        self.raw = raw
        self.emb = emb
        self.length = len(self.raw)
        self.k = dist_parameter["k"]

    @abstractmethod
    def preprocessing(self):
        pass
    
    '''
    Extract the clusters from the given incidices
    mode : steadiness / cohesiveness 
    '''
    @abstractmethod
    def extract_cluster(self, mode, walk_num):
        pass
    

    '''
    Get the indices of the points which to be clustered as input
    and return the clustereing result
    mode : steadiness / cohesiveness 
    '''
    @abstractmethod
    def clustering(self, mode, indices):
        pass
    
    '''
    Compute the distance between two clusters in raw / emb space
    return two distance (raw_dist, emb_dist)
    mode: steadiness / cohesiveness
    '''
    @abstractmethod
    def compute_distance(self, mode, cluster_a, cluster_b):
        pass









class SNNCS(ClusterStrategy):

    def __init__(self, dist_parameter, raw, emb):
        super().__init__(dist_parameter, raw, emb)

        ## distance matrix
        self.raw_dist_matrix = dm.dist_matrix_gpu(self.raw)
        self.emb_dist_matrix = dm.dist_matrix_gpu(self.emb)

        ## normalizing
        self.raw_dist_max = np.max(self.raw_dist_matrix)
        self.emb_dist_max = np.max(self.emb_dist_matrix)
        
        self.raw_dist_matrix /= self.raw_dist_max
        self.emb_dist_matrix /= self.emb_dist_max 

        self.a = parameter["alpha"]    # parameter for similairty => distance = 1 / 1 + similarity

    def preprocessing(self):
        # Compute knn infos
        self.raw_knn_info = sk.knn_info(self.raw_dist_matrix, self.k)
        self.emb_knn_info = sk.knn_info(self.emb_dist_matrix, self.k)
        
        # Compute snn matrix
        self.raw_snn_matrix = sk.snn_gpu(self.raw_knn_info, self.length, self.k)
        self.emb_snn_matrix = sk.snn_gpu(self.emb_knn_info, self.length, self.k)
        raw_snn_max    = np.max(self.raw_snn_matrix)
        emb_snn_max    = np.max(self.emb_snn_matrix)

        # Normalize snn matrix
        self.raw_snn_matrix /= raw_snn_max
        self.emb_snn_matrix /= emb_snn_max

        # Compute dist matrix 
        self.raw_snn_dist_matrix = 1 / (self.raw_snn_matrix + self.a)
        self.emb_snn_dist_matrix = 1 / (self.emb_snn_matrix + self.a)

        dissimilarity_matrix = self.raw_snn_dist_matrix - self.emb_snn_dist_matrix
        dissimilarity_max = np.max(dissimilarity_matrix)
        dissimilarity_min = np.min(dissimilarity_matrix)

        max_compress = dissimilarity_max if dissimilarity_max > 0 else 0
        min_compress = dissimilarity_min if dissimilarity_min > 0 else 0
        max_stretch  = - dissimilarity_min if dissimilarity_min < 0 else 0
        min_stretch  = - dissimilarity_max if dissimilarity_max < 0 else 0
        return max_compress, min_compress, max_stretch, min_stretch
        

    def extract_cluster(self, mode, walk_num):
        # Seed selection
        if mode == "steadiness":   ## extract from the embedded (projected) space
            knn_info   = self.emb_knn_info
            snn_matrix = self.emb_snn_matrix
        if mode == "cohesiveness": ## extract from the original space
            knn_info   = self.raw_knn_info
            snn_matrix = self.raw_snn_matrix
        seed_idx = np.random.randint(self.length)
        extracted_cluster = []
        while len(extracted_cluster) == 0:
            cluster_candidate = sk.snn_based_cluster_extraction(knn_info, snn_matrix, seed_idx, walk_num)
            if cluster_candidate.size > 1:
                extracted_cluster = cluster_candidate
        return extracted_cluster



    ## HDBSCAN with precomputed distance based on snn
    def clustering(self, mode, indices):
        if mode == "steadiness":
            snn_dist_matrix = self.raw_snn_dist_matrix
        if mode == "cohesiveness":
            snn_dist_matrix = self.emb_snn_dist_matrix

        cluster_snn_dist_matrix = (snn_dist_matrix[indices].T)[indices] 

        np.fill_diagonal(cluster_snn_dist_matrix, 0)

        clusterer = hdbscan.HDBSCAN(metric="precomputed", allow_single_cluster=True)
        clusterer.fit(cluster_snn_dist_matrix)
        
        return clusterer.labels_


    def compute_distance(self, mode, cluster_a, cluster_b):

        pair_num = cluster_a.size * cluster_b.size
        if(cluster_a.size == 1):
            cluster_a = cluster_a[0]
        if(cluster_b.size == 1):
            cluster_b = cluster_b[0]
        raw_similarity = np.sum((self.raw_snn_matrix[cluster_a].T)[cluster_b]) / pair_num
        emb_similarity = np.sum((self.emb_snn_matrix[cluster_a].T)[cluster_b]) / pair_num

        raw_dist = 1 / (raw_similarity + self.a) 
        emb_dist = 1 / (emb_similarity + self.a) 

        return raw_dist, emb_dist
    
  

'''
SNN Similarity + KMEANS
overrides SNNCS 
'''
class SNNKM(SNNCS):

    def __init__(self, parameter, raw, emb, k):
        super().__init__(parameter, raw, emb)
        self.cluster_num = k

    ## KMEANS with precomputed distance based on snn
    def clustering(self, mode, indices):
        if mode == "steadiness":
            data = self.raw
        if mode == "cohesiveness":
           data = self.emb

        clusterer = KMeans(n_clusters=self.cluster_num)
        clusterer.fit(data[indices])

        
        return clusterer.labels_

'''
SNN Similarity + XMEANS
overrides SNNCS
'''
class SNNXM(SNNCS):
    ## KMEANS with precomputed distance based on snn
    def clustering(self, mode, indices):
        if mode == "steadiness":
            data = self.raw
        if mode == "cohesiveness":
            data = self.emb

        clusterer = xmeans(data[indices])
        clusterer.process()

        clusters = np.zeros(len(indices), dtype=np.int32)
        labels = clusterer.get_clusters()

        for cnum, cluster in enumerate(labels):
            for idx in cluster:
                clusters[idx] = cnum

        return clusters.tolist()

'''
Euclidean + SNN
'''
class EUCCS(ClusterStrategy):

    def __init__(self, parameter, raw, emb):
        super().__init__(raw, emb)

        ## distance matrix
        self.raw_dist_matrix = dm.dist_matrix_gpu(self.raw)
        self.emb_dist_matrix = dm.dist_matrix_gpu(self.emb)

        ## normalizing
        self.raw_dist_max = np.max(self.raw_dist_matrix)
        self.emb_dist_max = np.max(self.emb_dist_matrix)
        
        self.raw_dist_matrix /= self.raw_dist_max
        self.emb_dist_matrix /= self.emb_dist_max 


        self.k = parameter["k"]
        self.a = 0.1    # parameter for similairty => distance = 1 / 1 + similarity

    def preprocessing(self):
        # Compute knn infos
        self.raw_knn_info = sk.knn_info(self.raw_dist_matrix, self.k)
        self.emb_knn_info = sk.knn_info(self.emb_dist_matrix, self.k)
        
        dissimilarity_matrix = self.raw_dist_matrix - self.emb_dist_matrix
        dissimilarity_max = np.max(dissimilarity_matrix)
        dissimilarity_min = np.min(dissimilarity_matrix)

        max_compress = dissimilarity_max if dissimilarity_max > 0 else 0
        min_compress = dissimilarity_min if dissimilarity_min > 0 else 0
        max_stretch  = - dissimilarity_min if dissimilarity_min < 0 else 0
        min_stretch  = - dissimilarity_max if dissimilarity_max < 0 else 0
        return max_compress, min_compress, max_stretch, min_stretch
        

    def extract_cluster(self, mode, walk_num):
        # Seed selection
        if mode == "steadiness":   ## extract from the embedded (projected) space
            knn_info   = self.emb_knn_info
        if mode == "cohesiveness": ## extract from the original space
            knn_info   = self.raw_knn_info
        seed_idx = np.random.randint(self.length)
        extracted_cluster = []
        while len(extracted_cluster) == 0:
            cluster_candidate = sk.naive_cluster_extraction(knn_info, seed_idx, walk_num)
            if cluster_candidate.size > 1:
                extracted_cluster = cluster_candidate
        return extracted_cluster


    ## HDBSCAN with precomputed distance based on snn
    def clustering(self, mode, indices):
        if mode == "steadiness":
            dist_matrix = self.raw_dist_matrix
        if mode == "cohesiveness":
            dist_matrix = self.emb_dist_matrix

        cluster_dist_matrix = (dist_matrix[indices].T)[indices] 

        np.fill_diagonal(cluster_dist_matrix, 0)

        clusterer = hdbscan.HDBSCAN(metric="precomputed", allow_single_cluster=True)
        clusterer.fit(cluster_dist_matrix)
        
        return clusterer.labels_


    def compute_distance(self, mode, cluster_a, cluster_b):


        a_raw_centroid, a_emb_centroid = self.__get_centroid(cluster_a)
        b_raw_centroid, b_emb_centroid = self.__get_centroid(cluster_b)

        raw_dist = np.linalg.norm(a_raw_centroid - b_raw_centroid) / self.raw_dist_max
        emb_dist = np.linalg.norm(a_emb_centroid - b_emb_centroid) / self.emb_dist_max

        # print(raw_dist, emb_dist)
        return raw_dist, emb_dist
    
    def __get_centroid(self, cluster):
        if (cluster.size == 1):
            raw_centroid = self.raw[cluster[0]]
            emb_centroid = self.emb[cluster[0]]
        else:
            raw_centroid = np.sum(self.raw[cluster], axis=0) / len(cluster)
            emb_centroid = np.sum(self.emb[cluster], axis=0) / len(cluster)
        return raw_centroid, emb_centroid

'''
EUC Similarity + KMEANS
overrides EUCCS 
'''
class EUCKM(EUCCS):

    def __init__(self, parameter, raw, emb):
        super().__init__(parameter, raw, emb)
        self.cluster_num = parameter["cluster_num"]

    ## KMEANS with precomputed distance based on snn
    def clustering(self, mode, indices):
        if mode == "steadiness":
            data = self.raw
        if mode == "cohesiveness":
           data = self.emb

        clusterer = KMeans(n_clusters=self.cluster_num)
        clusterer.fit(data[indices])

        
        return clusterer.labels_

'''
EUC Similarity + XMEANS
overrides SNNCS
'''
class EUCXM(EUCCS):

    ## KMEANS with precomputed distance based on snn
    def clustering(self, mode, indices):
        if mode == "steadiness":
            data = self.raw
        if mode == "cohesiveness":
            data = self.emb

        clusterer = xmeans(data[indices])
        clusterer.process()

        clusters = np.zeros(len(indices), dtype=np.int32)
        labels = clusterer.get_clusters()


        # print(labels)
        for cnum, cluster in enumerate(labels):
            for idx in cluster:
                clusters[idx] = cnum

        return clusters.tolist()