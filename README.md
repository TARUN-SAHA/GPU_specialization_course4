# This Getting started project is to classify Disaster tweets.

Detailed description is available on the kaggle: https://www.kaggle.com/competitions/nlp-getting-started/overview

Primary task is to identify if a given tweet is actually announcing a disasterous event or it's a normal tweet with no emergency.

Model is trained on both CPU and GPU(Nvidia) to compare the performance.


# System requirements:
1. Install Python3 
   * # sudo apt install python3.8
2. Install tensorflow
   * # conda install -c conda-forge cudatoolkit=11.2 cudnn=8.1.0
   * # export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib/
   * # python3 -m pip install tensorflow
3. Install Numpy
   * # sudo apt install python3-numpy
4. (Optional)Install Jupyter
5. Requires a kaggle account download the dataset

# Source Code (src):
* python - source code in .py file. To run the code: "python3 nlp_getting_started.py.py"
* jupyter - same code in a jupyter notebook. Load the code on Jupyter browser and run all the cells.

# Model:
It uses a LSTM model with GLoVE embedding vectors.
