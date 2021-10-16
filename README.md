# Word-Sense-Disambiguation-using-Neural Networks

File description:

  * data.py:   preprocessing Senseval2 and Senseval3 dataset, get the input for all models, including the sense embedding of the target sense, and forward data and backward arount the central word for Bidirectional LSTM
   
  * bilstm.py:   build bidrection LSTM for word sense disambiguation, using data.py as input, it will output the model. 
  
  * atten_in_lstm.py: build lstm model with attention layer for forward and backward data seperately for word sense disambiguation, using data.py as input, it will output the      model. 
 
  * seq2seq.py:   build a sequence 2 sequence for word sense disambiguation, using data.py as input, it will output the model. 
  
  * Biatten.py:   build bidrection LSTM with attention layer to the concatenated forward and backward lstm layers for word sense disambiguation, using data.py as input, it will output the model.  
  
  * glove.py:   load the pre-trained Glove word embedding vector for our own dataset
  
  * sense_embedding.csv:   the 100-dimension sense vector of Google - Word Sense Disambiguation corpora
  
  * senseval_sense_embedding.csv:   the 100-dimensiion sense vector of Senseval2 dataset
  
  * data:   including Senseval2 and Senseval3 dataset
  
  * Images: Model Images and Graphs of Accurance and Loss


# Code File to Use

Once you have cloned the code on your systems and opened it in your interface, set the path and then follow the following file:

  * Thesis_Code_Final.ipynb: As instruction from setting the path to loading the data. There are Explanation of the functions created and modified for the thesis. The models are created and divided my sections in the file for easier navigation. 




