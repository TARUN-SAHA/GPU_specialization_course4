# -*- coding: utf-8 -*-
"""nlp-getting-started.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1djm0wx6ECxDyCeGf5HF67qVL6Fl-MQcz

**This notebook is to classify tweets if it's an emergency situation or a random tweets.**

Competition details are given here: https://www.kaggle.com/competitions/nlp-getting-started

I'll be using bidirectional LSTM model and use GloVE word embedding for creating this classification model.

Will be running this model on both CPU and GPU to compare the performance of the model for 10 iterations.
"""

# Install kaggle to interact with kaggle competition and download dataset.
# Download the kaggle.json by creating a new API token from kaggle account.
!pip install kaggle

!mkdir ~/.kaggle
!touch ~/.kaggle/kaggle.json
!cp kaggle.json ~/.kaggle/kaggle.json

# Download and unzip the dataset
!kaggle competitions download -c nlp-getting-started
!unzip ./nlp-getting-started.zip

# Download GloVE word embeddings for later use
!wget http://nlp.stanford.edu/data/glove.6B.zip
!unzip -q glove.6B.zip

# Import required libraries
import csv
import numpy as np
import tensorflow as tf
import tensorflow.keras.layers as layers

# Specify and train and test filepath
train_file = './train.csv'
test_file = './test.csv'

"""**Load Train and Test data from CSV**"""

# Load Training data
texts = []
labels = []

with open(train_file) as f:
  reader = csv.reader(f, delimiter=',')
  next(reader)
  for line in reader:
    texts.append(line[3])
    labels.append(line[4])

# Randomly split the train data into train and val dataset with 90:10 ratio
texts = np.array(texts)
labels = np.asarray(labels, dtype=np.int32)
totalLen = len(texts)
val_split = int(0.1 * totalLen)
val_pos = np.random.randint(totalLen, size=val_split)
train_pos = np.setdiff1d(np.arange(totalLen), val_pos)
train_sentences, train_labels = texts[train_pos], labels[train_pos]
val_sentences, val_labels = texts[val_pos], labels[val_pos]

# Load Test data
test_sentences = []
test_ids = []

with open(test_file) as f:
  reader = csv.reader(f, delimiter=',')
  next(reader)
  for line in reader:
    test_sentences.append(line[3])
    test_ids.append(line[0])

"""**Creating sequences with padding**

Convert all sentences to a fixed length, i.e. SEQ_LEN.
If sentence length is less than the SEQ_LEN, pad at the end.
Or if sentence length is greater than SEQ_LEN, truncate from the end.
"""

lens = [len(sentence.split()) for sentence in train_sentences]
SEQ_LEN = int(np.percentile(lens, 100))

vectorizer = layers.TextVectorization(max_tokens=None,
                                      output_sequence_length=SEQ_LEN)
vectorizer.adapt(train_sentences)

"""**Create a dictionary of word and its corresponding indexes from vocabulary**"""

voc = vectorizer.get_vocabulary()
word_index = dict(zip(voc, range(len(voc))))

"""**GloVE vector of dimension 100 will be used as word embeddings**"""

path_to_glove_file = './glove.6B.100d.txt'
embedding_index = {}
with open(path_to_glove_file) as f:
  for line in f:
    word, coefs = line.split(maxsplit=1)
    coefs = np.fromstring(coefs, 'f', sep=' ')
    embedding_index[word] = coefs

"""**Create Embedding Matrix from pre-trained vectors**

Creating a map for each word in the current vocabulary, if the word is not available in GloVE then keep embedding of that matrix as sequence of zeros.
"""

num_tokens = len(voc) + 2
embedding_dim = 100
hits = 0
misses = 0
missed_words = []

embedding_matrix = np.zeros((num_tokens, embedding_dim))
for word, i in word_index.items():
  embedding_vector = embedding_index.get(word)
  if embedding_vector is not None:
    embedding_matrix[i] = embedding_vector
    hits += 1
  else:
    misses += 1
    missed_words.append(word)
print(f'Converted {hits} words and missed {misses}')

embedding_layer = layers.Embedding(num_tokens,
                                   embedding_dim,
                                   embeddings_initializer=tf.keras.initializers.Constant(embedding_matrix),
                                   trainable=False)

"""**Creating LSTM Model**

"""

def create_model(lstm_units, output_units=1, output_activation='sigmoid'):
  model = tf.keras.Sequential([
    layers.Input(shape=(1,), dtype=tf.string),
    vectorizer,
    embedding_layer,
    layers.Bidirectional(layers.LSTM(lstm_units, return_sequences=True)),
    layers.BatchNormalization(),
    layers.Dropout(0.5),
    layers.Bidirectional(layers.LSTM(lstm_units)),
    layers.BatchNormalization(),
    layers.Dropout(0.5),
    layers.Dense(128),
    layers.Dropout(0.5),
    layers.Dense(units=output_units, activation=output_activation)
  ])

  return model

"""**Prepare dataset for optimization**

Convert an array of sentence and label to TF dataset.
Shuffle the training dataset.
"""

train_dataset = tf.data.Dataset.from_tensor_slices((train_sentences, train_labels)).shuffle(1024).batch(32).prefetch(-1)
val_dataset = tf.data.Dataset.from_tensor_slices((val_sentences, val_labels)).batch(32).prefetch(-1)

def train_model(model, device, epochs=10, model_callbacks=None):
  with tf.device(device_name=device):
    history = model.fit(train_dataset,
              epochs=epochs,
              validation_data=val_dataset,
              callbacks=model_callbacks)
    model.load_weights(checkpoint_filepath)
  return history

"""**Select a CPU and a GPU device to train the model**"""

CPU_DEVICE = '/cpu:0'
GPU_DEVICE = '/gpu:0' if tf.config.list_physical_devices('GPU') else None

"""**Training the Model**

First train on a CPU and then train the same model on a GPU to compare the difference in performance.

Training only for 10 iterations with same hyper-parameters.
"""

# Train on CPU
checkpoint_filepath = './checkpoint_cpu'
model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
    filepath=checkpoint_filepath,
    save_weights_only=True,
    monitor='val_loss',
    mode='min',
    save_best_only=True)

model_c = create_model(64, 1, 'sigmoid')
model_c.compile(loss='binary_crossentropy',
                optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
                metrics=['accuracy'])
train_model(model_c, CPU_DEVICE, 10, [model_checkpoint_callback])

# Train on GPU
checkpoint_filepath = './checkpoint_gpu'
model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
    filepath=checkpoint_filepath,
    save_weights_only=True,
    monitor='val_loss',
    mode='min',
    save_best_only=True)

model_g = None
if GPU_DEVICE is not None:
  model_g = create_model(64, 1, 'sigmoid')
  model_g.compile(loss='binary_crossentropy',
                  optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
                  metrics=['accuracy'])
  history = train_model(model_g, GPU_DEVICE, 10, [model_checkpoint_callback])

"""**Evaluate the model on validation dataset**"""

model_g.evaluate(val_dataset)

model_c.evaluate(val_dataset)

"""**Optional steps to submit the predicted results to the kaggle competition**"""

preds = model_g.predict(test_sentences)

test_pred_labels = tf.cast(tf.squeeze(tf.round(preds)), dtype=tf.int32)

import pandas as pd

test_df = pd.DataFrame({
    'id': test_ids,
    'target': test_pred_labels
})
test_df.to_csv('./submission_gpu.csv', index=False)

!kaggle competitions submit -c nlp-getting-started -f ./submission_gpu.csv -m "gpu"