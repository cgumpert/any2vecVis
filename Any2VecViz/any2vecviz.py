import json
from http import server
import logging
import numpy as np
import os
import time

# set up logging
logger = logging.getLogger('Any2VecVis')
logging.basicConfig(format='[%(name)s] - %(levelname)-7s - %(message)s', level=logging.DEBUG)


def generate_handler(data):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_file = os.path.abspath(os.path.join(base_dir, 'cloud.html'))
    style_file = os.path.abspath(os.path.join(base_dir, 'style.css'))
    js_file = os.path.abspath(os.path.join(base_dir, 'embedding_viz.js'))
    with open(template_file) as infile:
        html_template = infile.read()
    with open(style_file) as infile:
        css_definitions = infile.read()
    with open(js_file) as infile:
        js_definitions = infile.read()

    xmin = min([point['x'] for point in data])
    xmax = max([point['x'] for point in data])
    ymin = min([point['y'] for point in data])
    ymax = max([point['y'] for point in data])

    class MyHandler(server.BaseHTTPRequestHandler):
        def do_GET(self):
            """Respond to a GET request."""
            if self.path == '/':
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(html_template.format(CSS_DEFINITIONS=css_definitions,
                                                      JS_CODE=js_definitions,
                                                      VIS_DATA=str(data),
                                                      XMIN=xmin,
                                                      XMAX=xmax,
                                                      YMIN=ymin,
                                                      YMAX=ymax
                                                      ).encode())
            else:
                self.send_error(404)

    return MyHandler


def serve(data, ip='127.0.0.1', port=5001):
    srvr = server.HTTPServer((ip, port), generate_handler(data))

    logger.info("Serving to http://%s:%d/    [Ctrl-C to exit]", ip, port)

    try:
        srvr.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("stopping Server...")

    srvr.server_close()


def prepare(embeddings,
            projection,
            projection_kwargs,
            clustering,
            clustering_kwargs
            ):
    # run dimensionality reduction
    logger.info('using algorithm %s for dimensionality reduction', projection)
    try:
        logger.debug('using projection options: %r', projection_kwargs)
        x, embedding_time = calculate_embedding(embeddings.wv.vectors, projection, **projection_kwargs)
    except Exception as exception:
        logger.critical("failed to perform dimensionality reduction with %r", exception)
    else:
        logger.info('computed 2D embedding in %.2fs', embedding_time)

    # run clustering
    logger.info('using cluster algorithm %s for finding clusters', clustering)
    try:
        if 'n_clusters' not in clustering_kwargs and 'avg_cluster_size' in clustering_kwargs:
            logger.info("set number of cluster such that the average cluster size is %d",
                        clustering_kwargs['avg_cluster_size'])
            clustering_kwargs['n_clusters'] = len(embeddings.wv.vocab) // clustering_kwargs['avg_cluster_size']
            del clustering_kwargs['avg_cluster_size']

        logger.debug('using clustering options: %r', clustering_kwargs)
        cluster_ids, cluster_time = build_clusters(embeddings.wv.vectors, clustering, **clustering_kwargs)
    except Exception as exception:
        logger.critical("failed building clusters with %r", exception)
    else:
        logger.info('found %d different clusters in %.2fs', len(np.unique(cluster_ids)), cluster_time)

    # preparing data for visualization
    data = None
    try:
        data, vis_time = build_data_dict(x, embeddings.wv.vocab, cluster_ids, embeddings)
    except Exception as exception:
        logger.critical("failed to prepare data with %r", exception)
    else:
        logger.info('prepared %d data points for visualization in %.2fs', len(data), vis_time)

    return data


def load_vector_model(infile_name, input_type):
    start = time.perf_counter()
    if input_type == 'FastText':
        from gensim.models import FastText
        embeddings = FastText.load(infile_name)
    else:
        raise RuntimeError("unknown input type '%s'" % args.input_type)
    end = time.perf_counter()

    return embeddings, end - start


def calculate_embedding(vectors, embedding_type, **kwargs):
    start = time.perf_counter()
    if embedding_type == 'tsne':
        from sklearn.manifold import TSNE
        tsne = TSNE(**kwargs)
        x = tsne.fit_transform(vectors)
    elif embedding_type == 'pca':
        pass
    else:
        raise RuntimeError("unknown projection '%s'" % embedding_type)
    end = time.perf_counter()

    return x, end - start


def build_clusters(vectors, cluster_type, **kwargs):
    start = time.perf_counter()
    if cluster_type == 'agglo':
        from sklearn.cluster import AgglomerativeClustering
        cluster_ids = AgglomerativeClustering(**kwargs).fit_predict(vectors)
    else:
        raise RuntimeError("unknown clustering '%s'" % cluster_type)
    end = time.perf_counter()

    return cluster_ids, end - start


def build_data_dict(embedding, vocab, cluster_ids, embeddings):
    start = time.perf_counter()
    sorted_vocab = sorted(vocab, key=lambda t: vocab[t].count, reverse=True)
    data = [{'id': v.index,
             'count': v.count,
             'rank': sorted_vocab.index(token) + 1,
             'label': token,
             'x': embedding[v.index, 0],
             'y': embedding[v.index, 1],
             'cluster': cluster_ids[v.index],
             'similarities': sorted(
                 [{'other_token': other_token,
                   'similarity': embeddings.wv.similarity(token, other_token)
                   } for other_token, other_v in vocab.items()
                  if (cluster_ids[other_v.index] == cluster_ids[v.index]) and (other_token != token)
                  ], key=lambda a: a['similarity'], reverse=True)
             } for token, v in vocab.items()]
    end = time.perf_counter()
    return data, end - start


if __name__ == '__main__':
    # set up command line argument parsing
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    parser = ArgumentParser(description='A general visualization for word embeddings',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('infile', type=str, help='file containing gensim model')
    parser.add_argument('--input-type',
                        dest='input_type',
                        default='FastText',
                        choices=['FastText'],
                        help='type of data to load'
                        )
    parser.add_argument('--projection',
                        type=str,
                        default='tsne',
                        choices=['tsne', 'pca'],
                        help='dimensionality reduction algorithm'
                        )
    parser.add_argument('--projection-kwargs',
                        dest='projection_kwargs',
                        default='{}',
                        help='keyword dictionary passed to projection algorithm')
    parser.add_argument('--clustering',
                        type=str,
                        default='agglo',
                        choices=['agglo'],
                        help='cluster algorithm for building finding clusters in vector space'
                        )
    parser.add_argument('--cluster-kwargs',
                        dest='cluster_kwargs',
                        default='{}',
                        help='keyword dictionary passed to cluster algorithm')
    args = parser.parse_args()

    # preprocess arguments
    projection_options = json.loads(args.projection_kwargs)
    clustering_options = json.loads(args.cluster_kwargs)

    # load the data
    try:
        model, _time = load_vector_model(args.infile, args.input_type)
    except Exception as e:
        logger.critical("failed to load '%s' (%s) with %r",
                        args.infile, args.input_type, e)
    else:
        logger.info('loaded model: %s in %.2fs', model, _time)

        vis_data = prepare(model,
                           projection=args.projection,
                           projection_kwargs=projection_options,
                           clustering=args.clustering,
                           clustering_kwargs=clustering_options)
        serve(vis_data)
