# -*- coding: utf-8 -*-

from data import *
from glove import *
import tensorflow as tf
from tensorflow.python import keras
#import tensorflow.nn.rnn_cell as rnn_cell
from tensorflow.keras.layers import RNN
from sklearn.model_selection import train_test_split
import os
import glob
import numpy as np
import h5py
import matplotlib.pyplot as plt
from keras.layers import Layer
import keras.backend as K

from random import random
from numpy import array
from numpy import cumsum
from matplotlib import pyplot
from pandas import DataFrame

import keras
from keras_self_attention import SeqSelfAttention
from keras.layers import Dense, Input, LSTM, Embedding, Dropout, Activation, GlobalAveragePooling1D, TimeDistributed, GlobalMaxPooling1D, BatchNormalization
from keras.layers.merge import concatenate
from keras.models import Model
from tensorflow.keras.models import Sequential
import keras.layers.normalization
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras import optimizers
import keras.backend as K
from keras.utils.vis_utils import plot_model



# rm old log files
for file in glob.glob('/home/salomons/tmp/tf.log/*'):
    os.remove(file)

# config
train_path = '/data/senseval2/eng-lex-sample.training.xml'
test_path = '/data/senseval2/eng-lex-samp.evaluation.xml'

# load data
#train_data = load_senteval2_data(train_path, True)
#test_data = load_senteval2_data(test_path, False)
train_data_ = load_train_data(23)
#test_data = load_test_data(2)
#print('Dataset size (train/test): %d / %d' % (len(train_data_), len(test_data)))

EMBEDDING_DIM = 100
print('Embedding vector: %d' % EMBEDDING_DIM)

# build vocab utils
word_to_id = build_vocab(train_data_)
target_word_to_id, target_sense_to_id, n_words, n_senses_from_target_id = build_sense_ids(train_data_)
print('Vocabulary size: %d' % len(word_to_id))

#build context vocab of the target sense
train_target_sense_to_context = build_context(train_data_, word_to_id)

#build context embeddings of the target sense
embedding_matrix = fill_with_gloves(word_to_id, 100)
target_sense_to_context_embedding = build_embedding(train_target_sense_to_context, embedding_matrix, len(word_to_id), EMBEDDING_DIM)

# make numeric
train_ndata = convert_to_numeric(train_data_, word_to_id, target_word_to_id, target_sense_to_id, n_senses_from_target_id, target_sense_to_context_embedding, is_training = True)
#test_ndata = convert_to_numeric(test_data, word_to_id, target_word_to_id, target_sense_to_id, n_senses_from_target_id, target_sense_to_context_embedding, is_training = False)

n_step_f = 40
n_step_b = 40
print('n_step forward/backward: %d / %d' % (n_step_f, n_step_b))
MAX_SEQUENCE_LENGTH = 40
act = 'relu'
#STAMP = 'lstm_%d_%d_%.2f_%.2f'%(100, 2, 0.2, 0.5)

#bst_model_path = h5py.File("weights.best.hdf5", "w")

def cos_distance(y_true, y_pred):
    y_true = K.l2_normalize(y_true, axis=-1)
    y_pred = K.l2_normalize(y_pred, axis=-1)
    return K.mean(1 - K.sum((y_true * y_pred), axis=-1))

def recall_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives +K.epsilon())
    return recall

def precision_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + K.epsilon())
    return precision

def f1_m(y_true, y_pred):
    precision = precision_m(y_true, y_pred)
    recall = recall_m(y_true, y_pred)
    return 2*((precision*recall)/(precision+recall+K.epsilon()))


def own_model(train_forward_data, train_backward_data, train_sense_embedding, 
              val_forward_data=None, val_backward_data=None, val_sense_embedding=None,
              n_units=100, dense_unints=256, is_training=True, EMBEDDING_DIM=100, epochs=10, batch_size=1024, init_word_vecs=None):
    
    embedding_layer = Embedding(len(word_to_id),
                                EMBEDDING_DIM,
                                weights=[init_word_vecs],
                                input_length=MAX_SEQUENCE_LENGTH,
                                trainable=False)
    lstm_layer = LSTM(n_units, dropout=0.2, recurrent_dropout=0.2)
    forward_input = Input(shape=(MAX_SEQUENCE_LENGTH, ), dtype='int32', name='forward_input')
    embedded_forward = embedding_layer(forward_input)
    forward_lstm = lstm_layer(embedded_forward)
        
    backward_input = Input(shape=(MAX_SEQUENCE_LENGTH, ), dtype='int32', name='backward_input')
    embedded_backward = embedding_layer(backward_input)
    backward_lstm = lstm_layer(embedded_backward)
    
    merged = concatenate([forward_lstm, backward_lstm])     
    #merged = lstm_layer(merged)
    
    merged = Dropout(0.2)(merged) if is_training else merged
    #merged = BatchNormalization()(merged)


    merged = Dense(units=dense_unints, activation=act)(merged)
    merged = Dropout(0.2)(merged) if is_training else merged
    #merged = BatchNormalization()(merged)
    merged = Dropout(0.2)(merged) if is_training else merged
    merged = BatchNormalization()(merged)


    preds = Dense(units=dense_unints, activation='relu')(merged)
    #merged = Dropout(0.2)(merged) if is_training else merged
    #merged = BatchNormalization()(merged)
    
    preds_final = Dense(EMBEDDING_DIM, activation='softmax')(preds)
    
    ## train the model 
    model = Model(inputs=[forward_input, backward_input], outputs=preds_final)

    #nadam = optimizers.Nadam(clipnorm=1.) #, clipvalue=0.5
    model.compile(loss='mse', optimizer='rmsprop', metrics=['acc', cos_distance, f1_m, recall_m, precision_m])
    
    model.summary()
    early_stopping =EarlyStopping(monitor='val_loss', patience=10)
    #bst_model_path = STAMP + '.h5'
    bst_model_path = "weights.best.hdf5"
    model_checkpoint = ModelCheckpoint(bst_model_path, save_best_only=True, save_weights_only=True, verbose=1)
      
    hist = model.fit([train_forward_data, train_backward_data], train_sense_embedding, 
                     validation_data=([val_forward_data, val_backward_data], val_sense_embedding), 
                     epochs=epochs, batch_size=batch_size, shuffle=True, 
                     callbacks=[early_stopping, model_checkpoint])
    
    model.load_weights(bst_model_path)
    bst_val_score = min(hist.history['val_loss'])
    print(hist.history.keys())
    print('min val loss is: %f' % (bst_val_score))
    fig = plt.figure()
    plt.plot(hist.history["loss"], label="Training Loss")
    plt.plot(hist.history["val_loss"], label="Validation Loss")
    plt.plot(hist.history["acc"], label="Accuracy")
    plt.legend()
    plt.show()
    #fig.savefig('bilstm.png')

if __name__ == '__main__':

    grouped_by_target = group_by_target(train_ndata)
    train_data, val_data = split_grouped(grouped_by_target, 0)

    init_emb = fill_with_gloves(word_to_id, EMBEDDING_DIM)
    
    train_forward_data, train_backward_data, train_target_sense_ids, train_sense_embedding = get_data(train_data, n_step_f, n_step_b)
    val_forward_data, val_backward_data, val_target_sense_ids, val_sense_embedding = get_data(val_data, n_step_f, n_step_b)
        
    own_model(train_forward_data, train_backward_data, train_sense_embedding, 
              val_forward_data, val_backward_data, val_sense_embedding, 
              init_word_vecs=init_emb)


    