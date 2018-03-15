import logging
from flask import Flask, render_template
import time

# set up logging
logger = logging.getLogger('Any2VecVis')
logging.basicConfig(format = '[%(name)s] - %(levelname)-7s - %(message)s', level = logging.DEBUG)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('cloud.html')

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
    model = None
    try:
        if args.input_type == 'FastText':
            from gensim.models import FastText
            model = FastText.load(args.infile)
        else:
            raise RuntimeError("unknown input type '%s'" % args.input_type)
    except Exception as e:
        logger.critical("failed to load '%s' (%s) with %r",
                        args.infile, args.input_type, e)
    else:
        logger.info('loaded model: %r', model)
    
    # run dimensionality reduction
    logger.info('using algorithm %s for dimensionality reduction', args.projection)
    try:
        if args.projection == 'tsne':
            from sklearn.manifold import TSNE
            tsne = TSNE(verbose = 2)
            start = time.perf_counter()
            print(dir(model.wv))
            X = tsne.fit_transform(model.wv.vectors)
            end = time.perf_counter()
        elif args.projection == 'tsne':
            pass
        else:
            raise RuntimeError("unknown projection '%s'" % args.projection)
    except Exception as e:
        logger.critical("failed to perform dimensionality reduction with %r", e)
    else:
        logger.info('computed 2D embedding in %.2ds', end - start)

    app.run()