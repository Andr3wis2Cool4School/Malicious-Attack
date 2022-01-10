import pandas as pd
import util as ut
from sklearn.model_selection import train_test_split
import collections
import torch
from torch.utils import data


def return_data(data_path):
    dataset = pd.read_csv(data_path)
    X = dataset['Text']
    y = dataset['Label']

    X = X.apply(lambda x: ut.clean_text(x))
    X = X.apply(lambda x: x.split())
    y = y.apply(lambda x: ut.change_label(x))

    # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, random_state=100) 
    # return X_train, X_test, y_train, y_test
    return X, y


def count_corpus(X):
    tokens = [token for data_sample in X for token in data_sample]
    cnt = collections.Counter(tokens)
    return cnt


class Vocab:
    def __init__(self, X, min_freq, reserved_tokens=None):
        if reserved_tokens is None:
            reserved_tokens = []
        cnt = count_corpus(X)      
        
        # lambda x: x[1] means the second elements
        # sorting by the number 
        self._token_freqs = sorted(cnt.items(), key=lambda x: x[1], reverse=True)

        # idx_to_token --- a List
        self.idx_to_token = ['<unk>'] + reserved_tokens
        # token_to_idx --- a Dict
        self.token_to_idx = {token: idx
                             for idx, token in enumerate(self.idx_to_token)}
        

        # adding token to the index 
        for token, freq in self._token_freqs:
            if freq < min_freq:
                break
            if token not in self.token_to_idx:
                self.idx_to_token.append(token)
                self.token_to_idx[token] = len(self.idx_to_token) - 1 
        
    def __len__(self):
        return len(self.idx_to_token)

    '''
    "In real life", we will call our vacob by calling `vocab[X[i]]`.
    Note that, here, vocab[X[i]] is one data sample;
    we will also use recurcive to get the index for one token.
    If there is no such token inside the `token_to_idx`, 0 is returned
                        \*
                        dict.get(key, default=None)
                        take two parameters
                        If key not exists, in this case, 0 is returned --> self.UNK
                        */

    Input: one row text/ one data_sample
    Output: the indices of the data sample
    '''
    def __getitem__(self, data_sample):
        if not isinstance(data_sample, (list, tuple)):
            return self.token_to_idx.get(data_sample, self.unk)
        return [self.__getitem__(token) for token in data_sample]
        
    '''
    Input: the list of indices
    Output: the tokens
    Maybe we will only take input one index.
    '''
    def to_tokens(self, indices):
        if not isinstance(indices, (list, tuple)):
            return self.idx_to_token[indices]
        return [self.idx_to_token(index) for index in indices]

    @property
    def unk(self):
        return 0

def truncate_pad(indices, pad_length, padding_token):
    if len(indices) > pad_length:
        return indices[:pad_length]
    return indices + [padding_token]*(pad_length - len(indices)) 

def load_array(data_arrays, batch_size, is_train=True):
    dataset = data.TensorDataset(*data_arrays)
    return data.DataLoader(dataset, batch_size, shuffle=is_train)


def dataloader(config):
    # X_train, X_test, y_train, y_test = return_data(config.data_path)
    X, y  = return_data(config.data_path)
    vocab = Vocab(X, min_freq=config.min_freq, reserved_tokens=['<pad>'])
    train_features = torch.tensor([truncate_pad(vocab[data_sample], config.pad_length, vocab['<pad>']) for data_sample in X]) 
    # train_features = torch.tensor([truncate_pad(vocab[data_sample], config.pad_length, vocab['<pad>']) for data_sample in X_train])
    # test_features = torch.tensor([truncate_pad(vocab[data_sample], config.pad_length, vocab['<pad>']) for data_sample in X_test])

    # print(train_features)

    # y_train = torch.tensor(y_train.to_list())
    # y_test = torch.tensor(y_test.to_list())
    # print(y_train)


    train_iter = load_array((train_features, torch.tensor(y)), config.batch_size)
    # test_iter = load_array((test_features, y_train), config.batch_size, is_train=False)
    
    # return train_iter, test_iter
    return train_iter
        
