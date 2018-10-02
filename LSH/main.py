import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

import preprocess

def process_arguments(parser):
    parser.add_argument("--shingle_num",required=True, type=int, help="shingle value k")
    parser.add_argument("--hash_num",required=True, type=int, help="number of hash function")
    parser.add_argument("--band_num",required=True, type=int, help="number of band")
    parser.add_argument("--jaccard_sim",required=True, type=float, help="minimum jaccard similarity")

    return parser.parse_args()

def main():
    parser = ArgumentParser("preprocess", formatter_class=ArgumentDefaultsHelpFormatter, conflict_handler="resolve")
    args = process_arguments(parser)

    preprocess.main(args)

if __name__ == "__main__":
    sys.exit(main())
