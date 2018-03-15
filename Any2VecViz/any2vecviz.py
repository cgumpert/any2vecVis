import logging
from flask import Flask, render_template
import time

# set up logging
logger = logging.getLogger('Any2VecVis')
logging.basicConfig(format = '[%(name)s] - %(levelname)-7s - %(message)s', level = logging.DEBUG)

app = Flask(__name__)

cache = {}

@app.route('/')
def index():
    return render_template('cloud.html')

def load_vector_model(infile_name, input_type):
    start = time.perf_counter()
    if input_type == 'FastText':
        from gensim.models import FastText
        model = FastText.load(infile_name)
    else:
        raise RuntimeError("unknown input type '%s'" % args.input_type)
    end = time.perf_counter()
    
    return model, end - start

def calculate_embedding(vectors, **kwargs):
    start = time.perf_counter()
    if args.projection == 'tsne':
        from sklearn.manifold import TSNE
        tsne = TSNE(**kwargs)
        X = tsne.fit_transform(vectors)
    elif args.projection == 'pca':
        pass
    else:
        raise RuntimeError("unknown projection '%s'" % args.projection)
    end = time.perf_counter()
    
    return X, end - start

def prepare_data(embedding, vocab):
    start = time.perf_counter()
    data = [{'id': v.index,
             'count': v.count,
             'label': token,
             'x': embedding[v.index, 0],
             'y': embedding[v.index, 1],
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
    args = parser.parse_args()
    
    # load the data
    try:
        model, _time = load_vector_model(args.infile, args.input_type)
    except Exception as e:
        logger.critical("failed to load '%s' (%s) with %r",
                        args.infile, args.input_type, e)
    else:
        logger.info('loaded model: %r in %.2fs', model, _time)
    
    # run dimensionality reduction
    logger.info('using algorithm %s for dimensionality reduction', args.projection)
    try:
        X, _time = calculate_embedding(model.wv.vectors, verbose = 2, n_iter = 250)
    except Exception as e:
        logger.critical("failed to perform dimensionality reduction with %r", e)
    else:
        logger.info('computed 2D embedding in %.2fs', _time)

    # preparing data for visualization
    try:
        data, _time = prepare_data(X, model.wv.vocab)
    except Exception as e:
        logger.critical("failed to prepare data with %r", e)
    else:
        logger.info('prepared %d data points for visualization in %.2fs', len(data), _time)
    
    # store things in cache
    cache['model'] = model
    cache['data'] = data
    
    app.run()