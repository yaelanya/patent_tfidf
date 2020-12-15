import argparse
import logging
import pickle

import gensim
import pandas as pd
import regex
import yaml
from tqdm import tqdm

import utils


def main(args):
    # load a config file
    with open(args.param_path) as f:
        param = yaml.safe_load(f)['calc']

    print("Loading data...")
    dataset = load_tokenized_file(param['input'], param['pos'])

    print("Building dictionary...")
    dct = gensim.corpora.Dictionary(dataset)

    corpus = [dct.doc2bow(line) for line in dataset]
    print("Calculating idf...")
    model = gensim.models.TfidfModel(corpus)

    print("Saving files...")
    with open(param['output_dict'], 'bw') as f:
        pickle.dump(dct, f)

    with open(param['output_model'], 'bw') as f:
        pickle.dump(model, f)


def load_tokenized_file(filepath, pos=['名詞']):
    filtered_tokens = []
    with open(filepath, 'r') as f:
        line = f.readline()
        while tqdm(line):
            tokens = line.strip().split('\t')
            filtered_tokens += [filter_pos(tokens, pos)]
            line = f.readline()
            
    return filtered_tokens


def filter_pos(tokens, pos):
    pos_patt =  r'^(' + '|'.join(pos) + r')?,'

    filtered_tokens = []
    for token in tokens:
        try:
            token_text, token_pos = token.split('###')
        except:
            continue

        if regex.search(pos_patt, token_pos):
            filtered_tokens.append(token_text)
    
    return filtered_tokens


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('param_path', type=str)
    args = parser.parse_args()

    main(args)
