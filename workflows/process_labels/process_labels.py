"""
Read and process the labels in the sized snapshot output of the `create_iq_snapshot` process  
"""
import argparse
import sys
if './' not in sys.path:
    sys.path.append('./')

import pandas as pd
import process_labels_util as plu

def main():
    # load argparser
    parser = argparse.ArgumentParser(
    prog='process_labels.py',
    description='Read and process the labels in the sized snapshot output of the `create_iq_snapshot` process',
    epilog='Usage: python process_labels.py --input <infile> --output <ofile>')

    parser.add_argument('--input', type=str, help='full path to input file', required=True)
    parser.add_argument('--output', type=str, help='full path to output file', required=True)
    parser.add_argument('--matrix', type=str, help='full path to matrix output file, if desired')

    args = parser.parse_args()
    # get input file
    infile = args.input
    # get output file
    outfile = args.output
    # get optional matrix file
    matrix = args.matrix

    # read the input file 
    df = plu.read_sized_snapshot(infile)

    # process the labels in the file
    new_df = plu.process_sized_snapshot(df, labels='Labels', key='CardURL')

    # write to matrix file if provided
    if (matrix):
        new_df.to_csv(matrix, sep='\t', index=False)

    # create a summary of processed labels
    output_df = pd.DataFrame(new_df.sum()).transpose()
    output_df.drop('CardURL', axis=1, inplace=True)
    output_df.drop('Repo', axis=1, inplace=True)
    output_df.to_csv(outfile, sep='\t',index=False)

if __name__ == "__main__":
    main()