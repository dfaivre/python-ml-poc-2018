import logging

import numpy
import pandas
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.preprocessing import StandardScaler

from data_scripts import pcs_data_loader
from modeling.preprocessing import DummyEncoder
from modeling.score_util import ScoreReport

logging.basicConfig(level=logging.DEBUG)


def transform(X, dummy_enc, label_mask):
    X_scaled = scaler.transform(X.loc[:, ~label_mask].fillna(0))
    X_transformed = numpy.array(X)
    X_transformed[:,~label_mask] = X_scaled

    return dummy_enc.transform(X_transformed)


label_cols = pcs_data_loader.group_cols()
# remove plntdate#
label_cols.remove('PlntDate#')
label_cols.remove('HarvDate#')

for x in range(0, 4):
    df = pcs_data_loader.load_corn_rows_pickle_gz().sample(10000)
    df.drop(['Year', 'YearId', 'ProcessedLayerUID', 'Area'], axis=1, errors='ignore', inplace=True)
    X = df.drop(['Dry_Yield'], axis=1, errors='ignore')
    y = df['Dry_Yield']
    label_mask = numpy.isin(X.columns, label_cols)

    enc = DummyEncoder(label_mask)
    enc.fit(X)

    scaler = StandardScaler()
    scaler.fit(X.loc[:, ~label_mask].fillna(0))

    model = ExtraTreesRegressor(verbose=99, min_samples_leaf=3, n_jobs=-1)
    X_scaled = transform(X, enc, label_mask)
    model.fit(X_scaled, y)

    elb_path = 'data/elbs/265869_elb.pickle.gz'
    elb_df = pandas.read_pickle(elb_path, compression='gzip')
    elb_df.drop(['Year', 'YearId', 'ProcessedLayerUID', 'Area'], axis=1, errors='ignore', inplace=True)
    elb_df = elb_df[df.columns]
    elb_X = elb_df.drop(['Dry_Yield'], axis=1)
    elb_X_scaled = transform(elb_X, enc, label_mask)
    elb_y = elb_df['Dry_Yield']

    predictions = model.predict(elb_X_scaled)
    elb_score = ScoreReport(elb_y.values, predictions)
    logging.info(elb_score)