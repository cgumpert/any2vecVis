import logging
from flask import Flask, render_template
import numpy as np
import time

# set up logging
logger = logging.getLogger('Any2VecVis')
logging.basicConfig(format = '[%(name)s] - %(levelname)-7s - %(message)s', level = logging.DEBUG)

app = Flask(__name__)

cache = {}

@app.route('/')
def index():
    X = cache.get('embedded_X', np.identity(2))
    _min = np.min(X, axis = 0)
    _max = np.max(X, axis = 0)
    return render_template('cloud.html',
                           visData = cache.get('data',[]),
                           xmin = _min[0],
                           xmax = _max[0],
                           ymin = _min[1],
                           ymax = _max[1],
                           )

def load_vector_model(infile_name, input_type):
    start = time.perf_counter()
    if input_type == 'FastText':
        from gensim.models import FastText
        model = FastText.load(infile_name)
    else:
        raise RuntimeError("unknown input type '%s'" % args.input_type)
    end = time.perf_counter()
    
    return model, end - start

def calculate_embedding(vectors, embedding_type, **kwargs):
    start = time.perf_counter()
    if embedding_type == 'tsne':
        from sklearn.manifold import TSNE
        tsne = TSNE(**kwargs)
        X = tsne.fit_transform(vectors)
    elif embedding_type == 'pca':
        pass
    else:
        raise RuntimeError("unknown projection '%s'" % embedding_type)
    end = time.perf_counter()
    
    return X, end - start

def build_clusters(vectors, cluster_type, **kwargs):
    start = time.perf_counter()
    if cluster_type == 'agglo':
        from sklearn.cluster import AgglomerativeClustering
        cluster_ids = AgglomerativeClustering(**kwargs).fit_predict(vectors)
    else:
        raise RuntimeError("unknown clustering '%s'" % cluster_type)
    end = time.perf_counter()
    
    return cluster_ids, end - start

def prepare_data(embedding, vocab, cluster_ids, model):
    start = time.perf_counter()
    sorted_vocab = sorted(vocab, key = lambda t: vocab[t].count, reverse = True)
    data = [{'id': v.index,
             'count': v.count,
             'rank': sorted_vocab.index(token) + 1,
             'label': token,
             'x': embedding[v.index, 0],
             'y': embedding[v.index, 1],
             'cluster': cluster_ids[v.index],
             'similarities': sorted(
                 [{'other_token': other_token,
                   'similarity': model.wv.similarity(token, other_token)
                  } for other_token, other_v in vocab.items()
                    if (cluster_ids[other_v.index] == cluster_ids[v.index]) and (other_token != token)  
                 ], key = lambda a: a['similarity'], reverse = True)
             } for token, v in vocab.items()]
    end = time.perf_counter()
    return data, end - start
    
if __name__ == '__main__':
    # set up command line argument parsing
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description = 'A general visualization for word embeddings',
                            formatter_class = ArgumentDefaultsHelpFormatter)
    parser.add_argument('infile', type = str, help = 'file containing gensim model')
    parser.add_argument('--input-type',
                        dest = 'input_type',
                        default = 'FastText',
                        choices = ['FastText'],
                        help = 'type of data to load'
                        )
    parser.add_argument('--projection',
                        type = str,
                        default = 'tsne',
                        choices = ['tsne', 'pca'],
                        help = 'dimensionality reduction algorithm'
                        )
    parser.add_argument('--clustering',
                        type = str,
                        default = 'agglo',
                        choices = ['agglo'],
                        help = 'cluster algorithm for building finding clusters in vector space'
                        )
    args = parser.parse_args()
    
    # load the data
    try:
        model, _time = load_vector_model(args.infile, args.input_type)
    except Exception as e:
        logger.critical("failed to load '%s' (%s) with %r",
                        args.infile, args.input_type, e)
    else:
        logger.info('loaded model: %s in %.2fs', model, _time)
    
    # run dimensionality reduction
    logger.info('using algorithm %s for dimensionality reduction', args.projection)
    try:
        X, _time = calculate_embedding(model.wv.vectors, args.projection, n_iter = 250, verbose = 2)
    except Exception as e:
        logger.critical("failed to perform dimensionality reduction with %r", e)
    else:
        logger.info('computed 2D embedding in %.2fs', _time)
    
    # run clustering
    logger.info('using cluster algorithm %s for finding clusters', args.clustering)
    try:
        cluster_ids, _time = build_clusters(model.wv.vectors, args.clustering, n_clusters = len(model.wv.vocab) // 5)
    except Exception as e:
        logger.critical("failed building clusters with %r", e)
    else:
        logger.info('built clusters in %.2fs', _time)
        
    # preparing data for visualization
    try:
        data, _time = prepare_data(X, model.wv.vocab, cluster_ids, model)
    except Exception as e:
        logger.critical("failed to prepare data with %r", e)
    else:
        logger.info('prepared %d data points for visualization in %.2fs', len(data), _time)
    
    # store things in cache
    cache['model'] = model
    cache['data'] = data
    cache['embedded_X'] = X
    
    app.run()