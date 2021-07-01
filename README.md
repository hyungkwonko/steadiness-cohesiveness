<p align="center">
<img src="https://user-images.githubusercontent.com/38465539/123574467-d9c87e00-d80a-11eb-8d19-36a9f8498a95.png" alt="" data-canonical-src="https://user-images.githubusercontent.com/38465539/123574467-d9c87e00-d80a-11eb-8d19-36a9f8498a95.png" width="80%"/>
</p>

<p align="center">
  <i><b>Quality Metrics for evaluating the inter-cluster reliability of Mutldimensional Projections</b></i> 
  <br />
    <a href="">Docs</a>
    ·
<!--     <a href=""> -->
      Paper
<!--   </a> -->
    ·
    <a href="mailto:hj@hcil.snu.ac.kr">Contact</a>
  
</p>


## Why Steadiness and Cohesiveness??

For sure, we cannot trust the result seen in multidimensional projections (MDP), such as [*t*-SNE](https://lvdmaaten.github.io/tsne/), [UMAP](https://github.com/lmcinnes/umap), or [PCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html), which are also known as the embeddings generated by Dimensionality Reduction. As distortions inherently occur when reducing dimensionality, meaningful patterns in projections can be less trustworthy and thus disturb users’ accurate comprehension of the original data, leading to interpretation bias. Therefore, it is vital to measure the overall distortions using quantitative metrics or visualize where and how the distortions occurred in the projection.

So- which aspects of MDP should be evaluated? There exist numerous criteria to check whether MDP well preserved the characteristics of the original high-dimensional data. Here, we focus on **inter-cluster reliability**, representing how well the projection depicts the **inter-cluster structure** (e.g., number of clusters, outliers, the distance between clusters...). It is important for MDP to have high inter-cluster reliability, as cluster analysis is one of the most critical tasks in MDP. 

However, previous local metrics to evaluate MDP (e.g., Trustworthiness & Continuity, Mean Relative Rank Error) focused on measuring the preservation of nearest neighbors or naively checked the maintenance of predefined clustering result or classes. These approaches cannot properly measure the reliability of the complex inter-cluster structure.

Steadiness & Cohesiveness were designed and implemented to bridge such a gap. By repeatedly extracting a random cluster from one space and measuring how well the cluster stays still in the opposite space, the metrics measure inter-cluster reliability. Note that Steadiness measures the extent to which clusters in the projected space form clusters in the original space, and Cohesiveness measures the opposite.

For more details, please refer to our paper (TBA).

## Basic Usage 

If you have trouble using Steadiness & Cohesiveness in your project or research, feel free to contact us ([hj@hcil.snu.ac.kr](mailto:hj@hcil.snu.ac.kr)).
We appreciate all requests about utilizing our metrics!!

### Installation
Steadiness and Cohesiveness are served with conda virtual environment.

```sh
git clone https://github.com/hj-n/steadiness-cohesiveness snc
conda env create -f snc/env/snc_virtual_env.yaml
conda activate sncvirtual
```



### How to use Stediness & Cohesiveness

```python
from snc import SNC

...

# k value for computing Shared Nearest Neighbor-based dissimilarity 
parameter = { "k": 10, "alpha": 0.1 }

metrics = SNC(
  raw=raw_data, 
  emb=emb_data, 
  iteration=300, 
  dist_parameter = parameter
)
metrics.fit()
print(metrics.steadiness(), metrics.cohesiveness())

```

if you installed Steadiness & Cohesiveness outside your project directory:

```python
import sys

sys.path.append("/absolute/path/to/steadiness-cohesiveness")
from snc import SNC

...
```

There exists number of parameters for Steadiness & Cohesiveness, but can use default setting (which is described in our paper) by only injecting original data `raw` and projection data `emb` as arguments. Detailed explanation for these parameters is like this:
- **`raw`**: the original (raw) high-dimensional data which used to generate multidimensional projections. Should be a 2D array (or a 2D np array) with shape `(n_samples, n_dim)` where `n_samples` denotes the number of data points in dataset and `n_dim` is the original size of dimensionality (number of features).
- **`emb`**: the projected (embedded) data of **`raw`** (i.e., MDP result). Should be a 2D array (or a 2D np array) with shape `(n_samples, n_reduced_dim)` where `n_reduced_dim` denotes the dimensionality of projection. 

Refer [API description](#api) for more details about hyperparameter setting.  

## API


### Initialization

```python
class SNC(
    raw, 
    emb, 
    iteration=200, 
    walk_num_ratio=0.4, 
    dist_strategy="snn", 
    dist_paramter={}, 
    dist_function=None,
    cluster_strategy="dbscan"
)
```

> ***`raw`*** : *`Array, shape=(n_samples, n_dim), dtype=float or int`*
> - The original (raw) high-dimensional data which used to generate MDP
> - `n_samples`: the number of data points in dataset / `n_dim`: is the original size of dimensionality
>
>
> ***`emb`*** : *`Array, shape=(n_samples, n_reduced_dim), dtype=float or int`*
> - The projected (embedded) data of **`raw`**
> - `n_reduced_dim`: dimensionality of the projection
> 
> ***`iteration`*** : *`int, (optional, default: 200)`*
> - denotes the number of partial distortion computation (extracting => evaluating maintainence in the opposite side)
> - Higher `iteration` generates the more deterministic / reliable result, but computation time increases linearly to `iteration`.
> - we recommend at least 200 iterations to be set.
> 
> ***`walk_num_ratio`*** : *`float, (optional, default: 0.4)`*
> - determines the amount of traverse held to extract a cluster
> - for the data with `n_samples` samples, the total traverse number to extract a cluster is `n_samples * walk_num_ratio` 
> - the size of extracted cluster grows as `walk_num_ratio` increases, but does not effect the result significantly
> 
> ***`dist_strategy`*** : *`string, (optional, default: "snn")`*
> - the selection of the way to compute distance 
> - currently supports: 
>   - `"snn"` : utilizes Shared Nearest Neighbor based dissimilarity 
>   - `"euclidean"`
>   - `"predefined"` : allows user-defined distance function
> - We highly recommend to use default distance strategy "snn", as it well considers clusters in high-dimensional space.
> - if you set `dist_strategy` as "predefined", you should also explicitly pass the way to compute distance as `dist_function` parameter. THe distance for cluster automatically computed as average linkage.
> 
> ***`dist_parameter`*** : *`dict, (optional, default: { "alpha": 0.1, "k": 20 })`*
> - inject parameters for distance computations 
> - if `dist_strategy == "snn`, `dist_parameter` dictionary should hold:
>   - `"alpha"` : *`float, (optional, default: 0.1)`*
>     - the hyperparameter which panalizes low similarity between data points / clusters.
>     - low `"alpha"` converts smaller similarities to higher dissimilarities (distances).
>   - `"k"` : *`int, (optional, default: 20)`* 
>     - used for constructing `k`-Nearest Neighbror graph which becomes a basis to compute SNN similarity. 
> - if `dist_parameter == "euclidean"`, `dist_parameter` does nothing.
> - if `dist_parameter == "predefined"`, you can freely utilize `dist_parameter` in `dist_function`, which is decribed below.
>   - Note that unlike `"snn"` and `"euclidean"`, the computation of "predefined" is not parallelized, thus requries much time to be computed
>   
> ***`dist_function`*** : *`function, (optional, default: None)`*
> - if you set `dist_strategy` as `"predefined"`, you should pass the function to calculate distance as parameter (otherwise the class raises error)
> - the function must get three parameters as arguments : two points `a`,`b`, their length `n_dim`, and `dist_parameter` which is given by user.
>   - `a` and `b` will be 1D numpy array with size `n_dim`
>   - `n_dim` will be an integer number
> - return value should be a single float value which denotes the distance between `a` and `b`.
>
> ***`cluster_strategy`*** : *`string, (optional, default: "dbscan")`*
> - Remind: Steadiness and Cohesiveness measures inter-cluster reliability by checking the maintenance of clusters from one space in the opposite space (Refer to [Why Steadiness and Cohesiveness](#why-steadiness-and-cohesiveness)). 
> - This is done by again "clustering" the cluster in the opposite side and measuring how much the cluster is splitted. `cluster_strategy` is a hyperparameter to determine the way to conduct such "clustering
> - currently supports:
>   - `"dbscan"` : based on density-based clustering algorithm, mainly utilizing [HDBSCAN](https://hdbscan.readthedocs.io/en/latest/how_hdbscan_works.html) ligrary.
>   - `"x-means"` : based on X-Means clustering algorithm
>   - `"'K'-means"` : based on K-Means clustering algorithm, where users can freely change `'K'` value by substituting it with integer number.
>     - e.g., `15-means`, `20-means`, etc. 


### Methods

```python3
SNC.fit(record_vis_info=False)
```

> Initializating Steadiness & Cohesiveness : Preprocessing (e.g., distance matrix computation) and preparation for computing Steadiness and Cohesiveness. 
> 
> ***`record_vis_info`*** : *`bool, (optional, default: False)`*
> - If `True`, SNC object records the information needed to make [distortion visualization of Steadiness & Cohesiveness](#visualizing-steadiness-and-cohesiveness)
> - method `vis_info()` becomes able to called when the parameter is set as `True`
> - Recording the informations incurs extra overhead!!


```python3
SNC.steadiness()
SNC.cohesiveness()
```

> Performs the main computation of Steadiness and Cohesiveness and return the result.
> Note that this step generates large proportion of the computation.

```python3
SNC.vis_info(file_path=None, label=None, k=10)
```

> Able to be performed when `record_vis_info` parameter is set as `True` (Otherwise raises Error)
>
> ***`file_path`*** : *`string, (optional, default: None)`*
> - if `file_path` is not given as arugment, returns visualization infos
> - if `file_path` is given, visualization info is saved in the file with designated name (and path)
> - if you only designate the directory (`file_path` ends with `/`), info is saved as `info.json` inside the directory
> ***`label`*** : *`Array, (optional, default: None), shape=(n_samples), dtype=int`*
> - 1D array which holds the label (class) information of dataset
> - if `None`, all points are considered to have a identical label "0"
> ***`k`*** : *`int, (optional, default: 10)`*
> - the `k` value for constructing kNN graph used in visualization


## Examples


## Visualizing Steadiness and Cohesiveness


![vis](https://user-images.githubusercontent.com/38465539/123515745-b0590680-d6d3-11eb-816d-e725fd5841ee.png)

By visualizing the result of Steadiness and Cohesiveness through the reliability map, it is able to get more insight about how inter-cluster structure is distorted in MDP. You only need to inject visualization info file generated by `vis_info` method.
Please check [relability map repository](https://github.com/hj-n/snc-reliability-map) and follow the instructions to visualize Steadiness and Cohesiveness in your web browser.

*The reliability map also supports interactions to show Missing Groups — please enjoy it!!*

<p align="center">
<img src="https://user-images.githubusercontent.com/38465539/123516175-c49e0300-d6d5-11eb-9a1c-2215b924ef79.gif" alt="" data-canonical-src="https://user-images.githubusercontent.com/38465539/123516175-c49e0300-d6d5-11eb-9a1c-2215b924ef79.gif" width="55%"/>
</p>
 

## References / Citation

TBA

## Contributors

TBA

